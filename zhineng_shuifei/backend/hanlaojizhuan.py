"""Short-window drought/flood abrupt-alternation assessment.

Based on the adjacent standardized water-balance anomaly idea used by the
provided papers (SPEI/SDFAI/SDWAI). This is an operational 3-day warning,
not a replacement for monthly climate-scale SPEI.
"""
from math import sqrt


def _num(value):
    try:
        value = float(value)
        return value if value == value else None
    except (TypeError, ValueError):
        return None


def evaluate(weather, baseline=None):
    rows = []
    for item in weather or []:
        rain = _num(item.get("jiangyu_liang"))
        et0 = _num(item.get("zhengfa_liang"))
        if rain is None or et0 is None:
            continue
        rows.append({"date": str(item.get("yubaoriqi", ""))[:10], "rain_mm": rain, "et0_mm": et0,
                     "balance_mm": rain - et0})
    if len(rows) < 2:
        return {"status": "insufficient_data", "events": [], "message": "至少需要连续2个有效日的降雨量和ET0；当前天气数据不足。",
                "method": "短期日尺度SPEI/SDFAI预警版", "source_note": "文献公式需要连续历史序列，当前仅用于运营预警。"}
    values = [r["balance_mm"] for r in rows]
    if baseline is None:
        mean = sum(values) / len(values)
        sd = sqrt(sum((x - mean) ** 2 for x in values) / max(1, len(values) - 1))
    else:
        base = [_num(x) for x in baseline if _num(x) is not None]
        mean = sum(base) / len(base) if base else sum(values) / len(values)
        sd = sqrt(sum((x - mean) ** 2 for x in (base or values)) / max(1, len((base or values)) - 1))
    sd = max(sd, 1.0)
    for row in rows:
        row["standardized_balance"] = round((row["balance_mm"] - mean) / sd, 3)
    events = []
    for before, after in zip(rows, rows[1:]):
        a, b = before["standardized_balance"], after["standardized_balance"]
        kind = None
        if a <= -0.5 and b >= 0.5:
            kind = "旱转涝"
        elif a >= 0.5 and b <= -0.5:
            kind = "涝转旱"
        if kind:
            intensity = round(abs(b - a) / sqrt(2), 2)
            level = "轻度" if intensity < 1 else "中度" if intensity < 1.5 else "重度" if intensity < 2 else "极端"
            events.append({"start_date": before["date"], "end_date": after["date"], "type": kind,
                           "intensity": intensity, "level": level,
                           "basis": "相邻日标准化水分盈亏跨越±0.5阈值"})
    risk = "高" if events and any(e["level"] in ("重度", "极端") for e in events) else "中" if events else "低"
    return {"status": "ok", "events": events, "risk_level": risk, "series": rows,
            "mean_water_balance_mm": round(mean, 3), "sd_water_balance_mm": round(sd, 3),
            "method": "短期日尺度SPEI/SDFAI预警版", "threshold": {"drought": -0.5, "wet": 0.5},
            "source_note": "依据用户提供文献的SPEI相邻时段阈值与SDFAI强度思想；需连续历史气象序列进行正式气候评价。"}
