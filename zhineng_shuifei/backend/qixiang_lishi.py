"""Local weather history used as a transparent offline baseline.

The supplied workbooks contain date, max/min/mean temperature and humidity.
They do not contain rain or ET0, so those values are never invented here.
"""
from pathlib import Path
from datetime import date, timedelta
import math

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "雅安": Path(r"C:\Users\D1782\Desktop\雅安气象数据_已填充.xlsx"),
    "西昌": Path(r"C:\Users\D1782\Desktop\西昌气象数据_已填充.xlsx"),
}
_CACHE = {}


def _load(region):
    if region in _CACHE:
        return _CACHE[region]
    path = FILES.get(region)
    if pd is None or not path or not path.exists():
        _CACHE[region] = []
        return []
    try:
        frame = pd.read_excel(path, sheet_name=0)
        if frame.shape[1] < 5:
            raise ValueError("weather workbook needs at least five columns")
        frame = frame.iloc[:, :5].copy()
        frame.columns = ["date", "max_temp", "min_temp", "mean_temp", "humidity"]
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        for col in frame.columns[1:]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.dropna(subset=["date", "max_temp", "min_temp", "humidity"])
        rows = frame.to_dict("records")
    except Exception:
        rows = []
    _CACHE[region] = rows
    return rows


def workbook_status():
    return {region: {"available": bool(_load(region)), "rows": len(_load(region)), "source": str(path)}
            for region, path in FILES.items()}


def baseline(region, start, days=3):
    """Return dated temperature/humidity rows, marked as historical baseline."""
    rows = _load(region)
    if not rows:
        return []
    start = date.fromisoformat(str(start)[:10]) if not isinstance(start, date) else start
    result = []
    for i in range(days):
        target = start + timedelta(days=i + 1)
        candidates = [r for r in rows if int(r["date"].month) == target.month and int(r["date"].day) == target.day]
        row = candidates[0] if candidates else rows[i % len(rows)]
        result.append({
            "yubaoriqi": target.isoformat(),
            "zuigao_wendu": round(float(row["max_temp"]), 2),
            "zuidi_wendu": round(float(row["min_temp"]), 2),
            "kongqi_shidu": round(float(row["humidity"]), 2),
            "jiangyu_gailv": None,
            "jiangyu_liang": None,
            "zhengfa_liang": None,
            "tianqi_leixing": "历史基线（无降雨/ET0）",
            "diqu": region,
            "shuju_laiyuan": "local_excel_historical_baseline",
        })
    return result
