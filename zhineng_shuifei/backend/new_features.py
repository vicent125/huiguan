"""Soil texture grading and pest analysis fallback services.

The module intentionally keeps model adapters optional.  When weights are not
installed it returns transparent, theory-based results rather than fabricated
model confidence.
"""
from __future__ import annotations

import io
import math
import os
import struct
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from pest_models import dual_branch_assist, label_to_zh, model_status as pest_model_status, run_yolo, run_disease_classifier
except ImportError:
    from .pest_models import dual_branch_assist, label_to_zh, model_status as pest_model_status, run_yolo, run_disease_classifier


def _number(value: Any, name: str, minimum: float = 0.0, maximum: float = 100.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name}必须是数字")
    if not math.isfinite(result) or result < minimum or result > maximum:
        raise ValueError(f"{name}必须在{minimum:g}到{maximum:g}之间")
    return result


SOIL_MODEL_WEIGHTS = Path(__file__).resolve().parent / "models" / "soil_cg_recnet" / "best.pt"


@lru_cache(maxsize=1)
def _load_soil_model():
    """Load the optional local CG-RecNet-inspired tabular checkpoint."""
    import torch
    from torch import nn

    checkpoint = torch.load(str(SOIL_MODEL_WEIGHTS), map_location="cpu", weights_only=True)
    classes = checkpoint.get("classes") if isinstance(checkpoint, dict) else None
    state_dict = checkpoint.get("state_dict") if isinstance(checkpoint, dict) else None
    if not isinstance(classes, list) or not classes or not isinstance(state_dict, dict):
        raise ValueError("土壤模型权重缺少类别或参数")

    class CGRecNetSoil(nn.Module):
        def __init__(self, num_classes: int):
            super().__init__()
            self.local = nn.Sequential(nn.Linear(3, 64), nn.LayerNorm(64), nn.GELU(), nn.Linear(64, 64))
            self.context = nn.Sequential(nn.Linear(3, 64), nn.LayerNorm(64), nn.GELU(), nn.Linear(64, 64))
            self.gate = nn.Sequential(nn.Linear(128, 64), nn.Sigmoid())
            self.head = nn.Sequential(nn.Linear(64, 32), nn.GELU(), nn.Linear(32, num_classes))

        def forward(self, values):
            local, context = self.local(values), self.context(values)
            gate = self.gate(torch.cat([local, context], dim=1))
            return self.head(gate * local + (1 - gate) * context)

    model = CGRecNetSoil(len(classes))
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    return model, [str(item) for item in classes], checkpoint


def _soil_model_prediction(sand: float, clay: float) -> Optional[Dict[str, Any]]:
    if not SOIL_MODEL_WEIGHTS.is_file():
        return None
    try:
        import torch

        model, classes, checkpoint = _load_soil_model()
        values = torch.tensor([[sand / 100.0, clay / 100.0, (100.0 - sand - clay) / 100.0]], dtype=torch.float32)
        with torch.inference_mode():
            probabilities = torch.softmax(model(values), dim=1)[0]
        index = int(torch.argmax(probabilities).item())
        confidence = round(float(probabilities[index].item()), 4)
        return {
            "label": classes[index],
            "confidence": confidence,
            "label_source": checkpoint.get("label_source", "USDA规则伪标签"),
            "supervised_ground_truth": bool(checkpoint.get("supervised_ground_truth", False)),
        }
    except Exception:
        return None


def grade_soil(payload: Dict[str, Any]) -> Dict[str, Any]:
    sand = _number(payload.get("sand_pct"), "sand_pct")
    clay = _number(payload.get("clay_pct"), "clay_pct")
    silt = payload.get("silt_pct")
    if silt is None:
        silt = 100.0 - sand - clay
    else:
        silt = _number(silt, "silt_pct")
    if silt < 0 or abs(sand + clay + silt - 100) > 1.5:
        raise ValueError("sand、clay、silt之和必须约等于100")

    # USDA texture triangle rule approximation, deliberately explainable.
    if clay >= 40 and sand <= 45 and silt <= 40:
        texture = "黏土"
    elif clay >= 27 and clay < 40 and sand > 20 and sand <= 45:
        texture = "黏壤土"
    elif clay >= 27 and sand > 45:
        texture = "砂质黏壤土"
    elif silt >= 80 and clay < 12:
        texture = "粉土"
    elif silt >= 50 and clay < 27:
        texture = "粉壤土"
    elif sand >= 85 and clay < 10:
        texture = "砂土"
    elif sand >= 70 and clay < 20:
        texture = "砂壤土"
    elif clay < 27 and sand < 52 and silt < 50:
        texture = "壤土"
    else:
        texture = "壤质黏土"

    model_prediction = _soil_model_prediction(sand, clay)
    model_path = SOIL_MODEL_WEIGHTS
    model_info = {
        "name": "CG-RecNet-inspired",
        "status": "已训练（USDA规则伪标签）" if model_path.is_file() else "待训练",
        "is_trained": model_path.is_file(),
        "label_source": "USDA土壤质地规则生成的伪标签" if model_path.is_file() else None,
        "supervised_ground_truth": False,
        "weights_available": model_path.is_file(),
        "paper_accuracy_transferred": False,
        "inference_ready": model_prediction is not None,
        "prediction": model_prediction,
    }
    return {
        "texture": texture,
        "sand_pct": round(sand, 2),
        "clay_pct": round(clay, 2),
        "silt_pct": round(silt, 2),
        "method": "USDA土壤质地三角分类的可解释规则近似",
        "model": model_info,
        "confidence": None,
        "source": payload.get("source") or "用户输入",
    }


def soil_data_status() -> Dict[str, Any]:
    root = os.environ.get("SOIL_DATA_ROOT", r"C:\Users\D1782\Desktop\A China Soil Characteristics Dataset")
    layers = []
    for name in ("sand1.tif", "sand2.tif", "clay1.tif", "clay2.tif"):
        if os.path.exists(os.path.join(root, "tiff", name)):
            layers.append(name)
    flt_available = all(os.path.exists(os.path.join(root, "flt", name)) for name in ("sand1.flt", "clay1.flt"))
    return {"available": bool(layers) and flt_available, "root": root, "layers": layers, "sampling": "单元窗口读取", "grid": {"ncols": 7389, "nrows": 4247, "cellsize": 0.00833, "xllcorner": 73.507973320232, "yllcorner": 18.16590447099}}


def sample_soil_grid(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Read one float32 cell from the large ESRI .flt files without loading them."""
    status = soil_data_status()
    root = status["root"]
    try:
        if payload.get("col") is not None and payload.get("row") is not None:
            col, row = int(payload["col"]), int(payload["row"])
        else:
            lon = float(payload.get("longitude", payload.get("lon")))
            lat = float(payload.get("latitude", payload.get("lat")))
            col = int((lon - 73.507973320232) / 0.00833)
            row = 4246 - int((lat - 18.16590447099) / 0.00833)
    except (TypeError, ValueError):
        raise ValueError("栅格采样需要row/col或longitude/latitude")
    if not (0 <= col < 7389 and 0 <= row < 4247):
        raise ValueError("栅格坐标超出范围")
    def read(name: str):
        path = os.path.join(root, "flt", name)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as handle:
            handle.seek((row * 7389 + col) * 4)
            raw = handle.read(4)
        value = struct.unpack("<f", raw)[0] if len(raw) == 4 else None
        return None if value is None or value <= -9998 else value
    sand, clay = read("sand1.flt"), read("clay1.flt")
    if sand is None or clay is None:
        raise ValueError("该栅格点没有有效sand/clay数据")
    # Dataset values are percentages in most releases; normalize fractional values.
    if sand <= 1.0: sand *= 100
    if clay <= 1.0: clay *= 100
    result = grade_soil({"sand_pct": sand, "clay_pct": clay, "source": f"中国土壤栅格 sand1/clay1 row={row}, col={col}"})
    result["grid"] = {"row": row, "col": col}
    return result


def analyze_pest_image(data: bytes, filename: str, weather: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not data:
        raise ValueError("图片内容为空")
    extension = os.path.splitext(filename or "")[1].lower()
    if extension not in {".png", ".jpg", ".jpeg"}:
        raise ValueError("仅支持PNG、JPG或JPEG图片")
    try:
        from PIL import Image
        image = Image.open(io.BytesIO(data))
        if image.format not in {"PNG", "JPEG"}:
            raise ValueError("文件内容不是PNG/JPEG图像")
        width, height = image.size
        if width <= 0 or height <= 0 or width * height > 40_000_000:
            raise ValueError("图片尺寸异常或超过4000万像素")
        image.thumbnail((256, 256))
        rgb_image = image.convert("RGB")
        pixels = list(rgb_image.get_flattened_data() if hasattr(rgb_image, "get_flattened_data") else rgb_image.getdata())
        count = max(1, len(pixels))
        green = sum(1 for r, g, b in pixels if g > r * 1.12 and g > b * 1.05 and g >= 40)
        yellow_brown = sum(1 for r, g, b in pixels if r >= g * 1.08 and g > b * 1.1 and r >= 45)
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("无法读取图片文件") from exc

    weather = weather or {}
    environment = {}
    for key, low, high in (("humidity", 0, 100), ("rainfall", 0, 1000), ("temperature", -20, 60)):
        if weather.get(key) not in (None, ""):
            environment[key] = _number(weather[key], key, low, high)
    env_score = None
    if "humidity" in environment and "rainfall" in environment:
        humidity_index = max(0.0, min(100.0, (environment["humidity"] - 60.0) / 40.0 * 100.0))
        rainfall_index = max(0.0, min(100.0, environment["rainfall"] / 30.0 * 100.0))
        env_score = round(0.6 * humidity_index + 0.4 * rainfall_index, 1)
    risk = "较高环境风险" if env_score is not None and env_score >= 65 else "中等环境风险" if env_score is not None and env_score >= 35 else "较低环境风险" if env_score is not None else ""
    yolo_result = run_yolo(data, filename)
    disease_result = run_disease_classifier(data, filename)
    dual_assist = dual_branch_assist(image)
    deployment = yolo_result.get("model_status") or pest_model_status()
    detections = yolo_result.get("detections") or []
    yolo_scope = (deployment.get("yolo_detail") or {}).get("label_scope")
    if disease_result.get("prediction"):
        diagnosis_label = f"病虫害分类：{disease_result['prediction']['label']}"
        diagnosis_note = "结果来自独立训练的YOLOv11叶片分类模型；该模型输出整张叶片的类别，不提供病斑框。"
    elif detections and yolo_scope == "olive_fruit_detection":
        diagnosis_label = "检测到橄榄果实（非病害判定）"
        diagnosis_note = "当前YOLOv11权重仅训练了橄榄果实目标框，不识别病害或虫害类别；请结合叶片病斑模型和人工复核。"
    elif detections:
        top_detection = detections[0]
        diagnosis_label = f"YOLOv11疑似：{top_detection['label']}"
        diagnosis_note = "结果来自已配置的油橄榄检测权重，请结合人工复核。"
    elif dual_assist.get("trained") and dual_assist.get("prediction"):
        diagnosis_label = f"双分支疑似：{label_to_zh(dual_assist['prediction'])}"
        diagnosis_note = "结果来自已配置的油橄榄 CNN+Transformer 分类权重，请结合人工复核。"
    elif deployment.get("yolo"):
        diagnosis_label = "YOLOv11未检出目标"
        diagnosis_note = "当前权重未检出目标，不能据此排除病虫害。"
    else:
        diagnosis_label = "未判定具体病种：油橄榄图像模型待部署"
        diagnosis_note = "当前使用颜色特征和环境规则降级，不输出未经训练验证的病种。"
    return {
        "image": {"filename": filename, "width": width, "height": height, "format": extension[1:].upper()},
        "diagnosis": {"label": diagnosis_label, "risk": risk, "score": env_score, "note": diagnosis_note},
        "visual_features": {"green_pixel_pct": round(green / count * 100, 1), "yellow_brown_pixel_pct": round(yellow_brown / count * 100, 1), "note": "缩略图颜色比例，仅为图像描述特征，不是病斑分割或病害诊断"},
        "detections": detections,
        "disease_classifier": disease_result,
        "dual_branch_assist": dual_assist,
        "theory": {
            "yolo": "YOLOv11接口采用ezer22/olive-disease-detection的训练和data.yaml约定；仅在油橄榄best.pt存在且依赖可用时输出检测框",
            "dual_branch": "已接入GL-MobFormer的CNN局部纹理、Transformer全局上下文和门控融合结构；只有本软件训练格式的油橄榄权重才会输出分类结果",
            "formula_basis": "论文评价公式：P=TP/(TP+FP)，R=TP/(TP+FN)，F1=2PR/(P+R)，mAP为各类AP均值；这些需要带标注的验证集，不能用于单张未标注图片推断",
            "environment_rule": "仅当提供湿度和近期降雨量时计算环境规则指数：0.6×湿度风险指数+0.4×降雨风险指数；不是论文病害概率公式",
            "sources": deployment.get("sources", {}),
        },
        "lstm": {"status": "未部署且无历史时序输入", "trend": [], "message": "未训练的LSTM不生成趋势预测"},
        "random_forest": {"status": "未部署；以透明环境规则替代" if env_score is not None else "未部署", "risk": risk, "score": env_score, "features": environment},
        "model_status": deployment,
        "model_message": yolo_result.get("status"),
        "model_error": yolo_result.get("error"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
