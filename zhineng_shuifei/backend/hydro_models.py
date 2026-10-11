"""Optional, local ML adapters for the water/fertilizer analysis.

The adapters are deliberately additive: legacy rule calculations remain the
fallback, while complete sensor history can activate the trained LSTM. The
random-forest artifact is a literature water-use prior and is never presented
as an autonomous local fertilizer recommendation.
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "olive_predict" / "models" / "hydro_ml"
LSTM_PATH = MODEL_DIR / "moisture_lstm.pt"
RF_PATH = MODEL_DIR / "olive_water_random_forest.joblib"


def model_status() -> dict[str, Any]:
    report = MODEL_DIR / "training_report.json"
    return {
        "lstm": {
            "deployed": LSTM_PATH.is_file(),
            "weights": str(LSTM_PATH) if LSTM_PATH.is_file() else None,
            "role": "有完整14天传感器历史时预测土壤含水趋势",
        },
        "random_forest": {
            "deployed": RF_PATH.is_file(),
            "weights": str(RF_PATH) if RF_PATH.is_file() else None,
            "role": "油橄榄文献灌溉量参考，不自动替代本地水肥决策",
        },
        "training_report": str(report) if report.is_file() else None,
        "legacy_fallback": True,
    }


class _MoistureLSTM:
    def __init__(self, input_size: int, hidden_size: int):
        import torch

        self.torch = torch
        self.model = torch.nn.Sequential()  # placeholder for type checkers
        class Net(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm = torch.nn.LSTM(input_size, hidden_size, batch_first=True)
                self.head = torch.nn.Sequential(torch.nn.Linear(hidden_size, 16), torch.nn.Tanh(), torch.nn.Linear(16, 1))

            def forward(self, values):
                sequence, _ = self.lstm(values)
                return self.head(sequence[:, -1, :]).squeeze(-1)
        self.model = Net()


@lru_cache(maxsize=1)
def _load_lstm():
    import torch

    checkpoint = torch.load(str(LSTM_PATH), map_location="cpu", weights_only=True)
    model = _MoistureLSTM(int(checkpoint["input_size"]), int(checkpoint["hidden_size"]))
    model.model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.model.eval()
    return model, checkpoint


def _daily_from_history(records: list[dict[str, Any]]) -> pd.DataFrame:
    raw = pd.DataFrame(records)
    aliases = {
        "timestamp": "timestamp", "date": "timestamp",
        "vwc_m3_m3": "vwc", "vwc": "vwc", "土壤含水量": "vwc",
        "soil_temp_c": "soil_temp", "soil_temp": "soil_temp", "土壤温度": "soil_temp",
        "bulk_ec_ds_m": "ec", "ec": "ec", "EC": "ec", "土壤EC": "ec",
    }
    mapped = {}
    for source, target in aliases.items():
        if source in raw.columns and target not in mapped:
            mapped[target] = raw[source]
    required = {"timestamp", "vwc", "soil_temp", "ec"}
    if not required.issubset(mapped):
        missing = sorted(required - set(mapped))
        raise ValueError("LSTM历史数据缺少: " + ",".join(missing))
    frame = pd.DataFrame(mapped)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    for col in ("vwc", "soil_temp", "ec"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna().sort_values("timestamp")
    frame = frame[frame.vwc.between(0, .8) & frame.soil_temp.between(-40, 65) & frame.ec.between(0, 20)]
    if frame.empty:
        raise ValueError("LSTM历史数据没有有效传感器记录")
    daily = frame.set_index("timestamp").resample("D").mean(numeric_only=True).dropna()
    return daily


def predict_lstm(records: Any, days: int = 3) -> dict[str, Any]:
    if not LSTM_PATH.is_file():
        return {"status": "model_missing", "daily": [], "message": "LSTM权重未部署"}
    if not isinstance(records, list) or not records:
        return {"status": "needs_inputs", "daily": [], "message": "需要至少14天的日期、含水量、土壤温度和EC历史"}
    try:
        frame = _daily_from_history(records)
        if len(frame) < 14:
            return {"status": "needs_inputs", "daily": [], "message": f"有效日数不足：{len(frame)}/14"}
        model, checkpoint = _load_lstm()
        mean = np.asarray(checkpoint["feature_mean"], dtype=np.float32)
        std = np.asarray(checkpoint["feature_std"], dtype=np.float32)
        std[std < 1e-8] = 1.0
        values = frame[["vwc", "soil_temp", "ec"]].tail(14).to_numpy(dtype=np.float32)
        rows = []
        for step in range(1, max(1, min(int(days or 3), 3)) + 1):
            normalized = ((values - mean) / std).astype(np.float32, copy=False)
            with model.torch.inference_mode():
                prediction = float(model.model(model.torch.from_numpy(normalized[None, ...])).item())
            prediction = float(np.clip(prediction, 0, .8))
            next_day = (frame.index[-1].date() + timedelta(days=step)).isoformat()
            # Weather is not part of this trained artifact; carry the latest
            # measured soil temperature and EC only for recursive inference.
            values = np.vstack([values[1:], np.asarray([prediction, values[-1, 1], values[-1, 2]], dtype=np.float32)]).astype(np.float32, copy=False)
            rows.append({"date": next_day, "vwc_m3_m3": round(prediction, 6), "soil_moisture_pct": round(prediction * 100, 2)})
        return {
            "status": "ready",
            "daily": rows,
            "model": "LSTM",
            "lookback_days": int(checkpoint["lookback_days"]),
            "metrics": checkpoint.get("metrics", {}),
            "warning": "雅安单年度传感器训练；结果需结合现场校准，不能外推所有地块。",
        }
    except (KeyError, TypeError, ValueError) as exc:
        return {"status": "invalid_inputs", "daily": [], "message": str(exc)}
    except Exception as exc:  # optional ML must never break legacy analysis
        return {"status": "inference_error", "daily": [], "message": str(exc)[:200]}


@lru_cache(maxsize=1)
def _load_rf():
    import joblib
    return joblib.load(RF_PATH)


def predict_rf_water(features: dict[str, Any] | None) -> dict[str, Any]:
    if not RF_PATH.is_file():
        return {"status": "model_missing", "estimate": None, "message": "随机森林权重未部署"}
    if not isinstance(features, dict):
        return {"status": "needs_inputs", "estimate": None, "message": "需要rf_features显式提供模型特征"}
    try:
        artifact = _load_rf()
        names = artifact["features"]
        values = {name: float(features[name]) for name in names}
        frame = pd.DataFrame([values], columns=names)
        estimate = float(artifact["model"].predict(frame)[0])
        return {
            "status": "ready_reference_only",
            "estimate": round(max(0.0, estimate), 3),
            "unit": "mm（来源研究原始单位）",
            "model": "RandomForestRegressor",
            "warning": "该模型由异构油橄榄文献水量样本训练，仅作参考；不自动生成施肥量或替代本地决策。",
        }
    except (KeyError, TypeError, ValueError) as exc:
        return {"status": "invalid_inputs", "estimate": None, "message": str(exc)}
    except Exception as exc:
        return {"status": "inference_error", "estimate": None, "message": str(exc)[:200]}


def run_hydro_ml(payload: dict[str, Any], days: int = 3) -> dict[str, Any]:
    history = payload.get("hydro_history") or payload.get("history_daily") or payload.get("history_15min")
    return {
        "lstm": predict_lstm(history, days) if history else {"status": "needs_inputs", "daily": [], "message": "水肥预测请求未提供14天传感器历史"},
        "random_forest": predict_rf_water(payload.get("rf_features")),
        "status": "available_with_explicit_inputs",
    }
