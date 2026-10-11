"""Decision confidence based on the supplied DTU trust paper.

The paper models trust as reliability, security, recoverability and integrity.
This operational adapter keeps the dimensions visible and uses conservative
local evidence rather than pretending the paper's generic weights are field
validated here.
"""
from math import exp


def evaluate(monitor=None, weather=None, prediction=None, ai=None, history=None):
    monitor = monitor or {}
    weather = weather or []
    prediction = prediction or {}
    ai = ai or {}
    history = history or []
    # Reliability: complete weather/monitor inputs and recent observation count.
    completeness = sum(v not in (None, "") for v in (monitor.get("turang_shidu"), monitor.get("dian_daolv"), monitor.get("turang_wendu"))) / 3
    weather_score = min(1.0, len(weather) / 3)
    reliability = round(0.6 * completeness + 0.4 * weather_score, 3)
    # Integrity: reject impossible soil readings and malformed prediction arrays.
    valid_monitor = 0.0 <= float(monitor.get("turang_shidu", 0)) <= 100 if monitor.get("turang_shidu") not in (None, "") else False
    integrity = 0.85 if valid_monitor and isinstance(prediction.get("dates", []), list) else 0.45
    # Recoverability: rule fallback and human confirmation preserve a safe path.
    recoverability = 0.9 if ai.get("fallback_used") or not ai else 0.75
    # Security: no automatic actuator execution and AI safety review status.
    security = 0.95 if prediction.get("can_auto_execute") is False else 0.65
    score = round(0.35 * reliability + 0.2 * security + 0.2 * recoverability + 0.25 * integrity, 3)
    level = "高" if score >= 0.8 else "中" if score >= 0.6 else "低"
    return {"score": score, "level": level, "dimensions": {
        "reliability": reliability, "security": security,
        "recoverability": recoverability, "integrity": integrity},
        "weights": {"reliability": 0.35, "security": 0.2, "recoverability": 0.2, "integrity": 0.25},
        "decision": "建议人工确认后执行" if score < 0.8 else "可进入人工确认流程",
        "method": "DTU四维可信度适配：R/S/Re/I；权重用于当前决策界面，需现场校准",
        "limitations": ["论文权重与阈值来自通用农业物联网场景，未完成本基地标定", "可信度不等于预测准确率"]}
