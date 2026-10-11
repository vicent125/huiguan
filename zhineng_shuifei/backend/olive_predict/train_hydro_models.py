"""Train an LSTM moisture forecaster and a cautious stage-water RF baseline.

The workbook's nine irrigation rows are calibration observations, not enough to
claim a production-grade fertilizer learner. This script records that limit.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "models" / "hydro_ml"
OUT.mkdir(parents=True, exist_ok=True)
torch.manual_seed(42)
np.random.seed(42)


def env_xlsx(name_fragment: str) -> Path:
    path = os.environ.get(name_fragment)
    if not path or not Path(path).is_file():
        raise FileNotFoundError(f"Set {name_fragment} to the source workbook path")
    return Path(path)


class MoistureLSTM(torch.nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 32):
        super().__init__()
        self.lstm = torch.nn.LSTM(input_size, hidden_size, batch_first=True)
        self.head = torch.nn.Sequential(torch.nn.Linear(hidden_size, 16), torch.nn.Tanh(), torch.nn.Linear(16, 1))

    def forward(self, values):
        sequence, _ = self.lstm(values)
        return self.head(sequence[:, -1, :]).squeeze(-1)


def build_sensor_frame(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="data", header=None, skiprows=3)
    if raw.shape[1] < 7:
        raise ValueError("雅安 EC/含水量 data sheet must have seven columns")
    frames = []
    for site, cols in (("Site1", (1, 2, 3)), ("Site2", (4, 5, 6))):
        frame = pd.DataFrame({
            "timestamp": pd.to_datetime(raw.iloc[:, 0], errors="coerce"),
            "vwc": pd.to_numeric(raw.iloc[:, cols[0]], errors="coerce"),
            "soil_temp": pd.to_numeric(raw.iloc[:, cols[1]], errors="coerce"),
            "ec": pd.to_numeric(raw.iloc[:, cols[2]], errors="coerce"),
            "site": site,
        }).dropna()
        frame = frame[frame.vwc.between(0, .8) & frame.soil_temp.between(-40, 65) & frame.ec.between(0, 20)]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True).sort_values(["site", "timestamp"])


def train_lstm(frame: pd.DataFrame) -> dict:
    daily = frame.set_index("timestamp").groupby("site").resample("D").agg(
        vwc=("vwc", "mean"), soil_temp=("soil_temp", "mean"), ec=("ec", "mean")
    ).dropna().reset_index()
    if len(daily) < 60:
        raise ValueError(f"Only {len(daily)} valid site-days; at least 60 required")

    features = []
    targets = []
    metadata = []
    lookback = 14
    for site, group in daily.groupby("site"):
        group = group.sort_values("timestamp").set_index("timestamp").asfreq("D")
        numeric = group[["vwc", "soil_temp", "ec"]].interpolate(limit=1).dropna()
        arr = numeric.to_numpy(dtype=np.float32)
        for i in range(lookback, len(arr)):
            features.append(arr[i - lookback:i])
            targets.append(arr[i, 0])
            metadata.append((site, numeric.index[i]))
    X = np.asarray(features, dtype=np.float32)
    y = np.asarray(targets, dtype=np.float32)
    n = len(y)
    split = max(1, min(n - 1, int(n * .8)))
    train_x, test_x = X[:split], X[split:]
    train_y, test_y = y[:split], y[split:]
    mean = train_x.reshape(-1, X.shape[-1]).mean(axis=0)
    std = train_x.reshape(-1, X.shape[-1]).std(axis=0)
    std[std < 1e-8] = 1.0
    train_x = (train_x - mean) / std
    test_x = (test_x - mean) / std
    model = MoistureLSTM(X.shape[-1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003, weight_decay=1e-4)
    tx, ty = torch.from_numpy(train_x), torch.from_numpy(train_y)
    model.train()
    for _ in range(120):
        optimizer.zero_grad()
        prediction = model(tx)
        loss = torch.nn.functional.smooth_l1_loss(prediction, ty)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    model.eval()
    with torch.no_grad():
        pred = np.clip(model(torch.from_numpy(test_x)).numpy(), 0, .8) if len(test_y) else np.array([])
    metrics = {
        "model": "LSTM",
        "target": "same-day mean VWC; one-day-ahead from previous 14 days",
        "lookback_days": lookback,
        "samples": int(n),
        "train_samples": int(len(train_y)),
        "chronological_test_samples": int(len(test_y)),
        "mae_vwc": float(mean_absolute_error(test_y, pred)) if len(pred) else None,
        "rmse_vwc": float(np.sqrt(mean_squared_error(test_y, pred))) if len(pred) else None,
        "baseline_last_value_mae_vwc": float(mean_absolute_error(test_y, test_x[:, -1, 0] * std[0] + mean[0])) if len(pred) else None,
        "warning": "Single-year Ya'an sensor data; random windows are not independent and results are not orchard-wide validation.",
    }
    torch.save({
        "state_dict": model.state_dict(), "input_size": X.shape[-1], "hidden_size": 32,
        "lookback_days": lookback, "feature_mean": mean.tolist(), "feature_std": std.tolist(),
        "features": ["vwc_m3_m3", "soil_temp_c", "bulk_ec_ds_m"], "sites": ["Site1", "Site2"],
        "metrics": metrics, "data_source": "雅安—EC、含水量(2022-2023).xlsx",
    }, OUT / "moisture_lstm.pt")
    return metrics


def train_water_rf(path: Path) -> dict:
    # Hold the nine local fitting rows out of training: they are a calibration set.
    fit = pd.read_excel(path, sheet_name=0, header=None, skiprows=1)
    fit = fit.iloc[:, :8].copy()
    fit.columns = ["stage", "actual_water", "actual_fertilizer", "actual_total", "recommended_water", "recommended_fertilizer", "recommended_total", "relative_error"]
    fit["actual_water"] = pd.to_numeric(fit["actual_water"], errors="coerce")
    fit["actual_fertilizer"] = pd.to_numeric(fit["actual_fertilizer"], errors="coerce")
    fit["recommended_water"] = pd.to_numeric(fit["recommended_water"], errors="coerce")
    fit["recommended_fertilizer"] = pd.to_numeric(fit["recommended_fertilizer"], errors="coerce")
    fit = fit.dropna(subset=["actual_water", "actual_fertilizer", "recommended_water", "recommended_fertilizer"])
    olive_path = env_xlsx("OLIVE_WORKBOOK")
    demand_sheet = next(s for s in pd.ExcelFile(olive_path).sheet_names if s.startswith("11-"))
    fert_sheet = next(s for s in pd.ExcelFile(olive_path).sheet_names if s.startswith("12-"))
    demand = pd.read_excel(olive_path, sheet_name=demand_sheet)
    demand = demand[pd.to_numeric(demand.iloc[:, 6], errors="coerce").notna()].copy()
    # Local nine-stage table is a calibration set; no orchard-specific nutrients
    # are joined to these rows, so the RF must not fabricate fertilizer targets.
    # The model therefore learns a small olive-literature water-response proxy,
    # and explicitly labels its weak evidence in the artifact and response.
    irrigation = pd.to_numeric(demand.iloc[:, 6], errors="coerce")
    ratio = pd.to_numeric(demand.iloc[:, 5], errors="coerce")
    kc = pd.to_numeric(demand.iloc[:, 4], errors="coerce")
    effective_rain = pd.to_numeric(demand.iloc[:, 7], errors="coerce")
    total_supply = pd.to_numeric(demand.iloc[:, 8], errors="coerce")
    years = demand.iloc[:, 3].astype(str).str.extract(r"(\d{4})", expand=False)
    year_numeric = pd.to_numeric(years, errors="coerce")
    features = pd.DataFrame({
        "irrigation_ratio_pct": ratio,
        "kc": kc,
        "effective_rain_mm": effective_rain,
        "total_supply_mm": total_supply,
        "year": year_numeric,
    })
    valid = irrigation.notna()
    features = features.loc[valid].reset_index(drop=True)
    for column in features.columns:
        median = features[column].median()
        features[column] = features[column].fillna(0.0 if pd.isna(median) else median)
    target = irrigation.loc[valid].reset_index(drop=True)
    if len(features) < 12 or target.nunique() < 4:
        return {
            "model": "RandomForestRegressor", "status": "not_trained_insufficient_olive_labels",
            "olive_label_rows": int(len(features)), "local_calibration_rows": int(len(fit)),
            "reason": "Insufficient complete olive irrigation rows for a defensible supervised model.",
        }
    model = RandomForestRegressor(n_estimators=200, min_samples_leaf=2, max_features=0.8, random_state=42)
    loo_pred = cross_val_predict(model, features, target, cv=LeaveOneOut())
    model.fit(features, target)
    model_path = OUT / "olive_water_random_forest.joblib"
    import joblib
    joblib.dump({
        "model": model,
        "features": list(features.columns),
        "target": "literature irrigation amount (mm; source units retained as supplied)",
        "status": "research_prior_not_local_recommendation",
        "sample_count": int(len(features)),
        "source": "油橄榄机器学习_数据汇总表.xlsx / 11-生育期需水",
        "warning": "Heterogeneous studies/years; use only as a comparison prior, not an autonomous local irrigation recommendation.",
    }, model_path)
    local_water_error = float(np.mean(np.abs(fit.actual_water - fit.recommended_water))) if len(fit) else None
    local_fert_error = float(np.mean(np.abs(fit.actual_fertilizer - fit.recommended_fertilizer))) if len(fit) else None
    return {
        "model": "RandomForestRegressor",
        "status": "trained_research_prior_not_local_recommendation",
        "olive_label_rows": int(len(features)),
        "leave_one_out_mae": float(mean_absolute_error(target, loo_pred)),
        "leave_one_out_rmse": float(np.sqrt(mean_squared_error(target, loo_pred))),
        "leave_one_out_r2": float(r2_score(target, loo_pred)) if len(target) > 2 else None,
        "local_calibration_rows": int(len(fit)),
        "local_water_recommendation_mae": local_water_error,
        "local_fertilizer_recommendation_mae": local_fert_error,
        "weights": str(model_path),
        "warning": "Small heterogeneous literature dataset; not suitable for automatic local dose recommendations.",
    }


def main():
    sensor = build_sensor_frame(env_xlsx("EC_WORKBOOK"))
    report = {
        "created_at": pd.Timestamp.now().isoformat(timespec="seconds"),
        "sensor_rows": int(len(sensor)),
        "sensor_sites": sorted(sensor.site.unique().tolist()),
        "lstm": train_lstm(sensor),
        "random_forest": train_water_rf(env_xlsx("FIT_WORKBOOK")),
        "fertilizer_model": {
            "status": "not_trained",
            "reason": "Available source has no orchard-specific fertilizer amount labels joined to weather/soil and growth/yield outcomes; EC is not an NPK measurement.",
        },
    }
    (OUT / "training_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
