"""Optional pest-model adapters used by the pest-analysis page.

The adapters are deliberately optional.  The application must remain usable
with the base requirements, where PyTorch and Ultralytics are not installed.
The olive repository supplies the YOLOv11 training/inference contract; the
Kaggle leaf repository supplies the CNN + Transformer fusion design only.
Its cassava labels and weights are not used for olive diagnosis.
"""
from __future__ import annotations

import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


BACKEND_ROOT = Path(__file__).resolve().parent
DEFAULT_YOLO_WEIGHTS = (
    BACKEND_ROOT / "models" / "pest_yolo" / "best.pt",
    BACKEND_ROOT / "models" / "best.pt",
)
DEFAULT_YOLO_DATA = (
    BACKEND_ROOT / "models" / "pest_yolo" / "data.yaml",
    BACKEND_ROOT / "models" / "data.yaml",
)
YOLO_METADATA = BACKEND_ROOT / "models" / "pest_yolo" / "model_metadata.json"
DISEASE_CLASSIFIER_WEIGHTS = BACKEND_ROOT / "models" / "pest_disease_cls" / "best.pt"
DISEASE_CLASSIFIER_METADATA = BACKEND_ROOT / "models" / "pest_disease_cls" / "model_metadata.json"
DEFAULT_HYBRID_WEIGHTS = (
    BACKEND_ROOT / "models" / "pest_hybrid" / "best.pt",
    BACKEND_ROOT / "models" / "pest_hybrid" / "model.pt",
)

SOURCE_INFO = {
    "yolo": {
        "name": "danielvalyano/olive-fruit-object-detection",
        "url": "https://www.kaggle.com/datasets/danielvalyano/olive-fruit-object-detection",
        "role": "油橄榄 YOLOv11 训练、data.yaml 类别和检测推理接口",
    },
    "dual_branch": {
        "name": "kozodoi/Kaggle_Leaf_Disease_Classification",
        "url": "https://github.com/kozodoi/Kaggle_Leaf_Disease_Classification",
        "role": "CNN 局部纹理 + Transformer 全局上下文的融合结构参考",
    },
}

# Keep model-native labels for traceability, while exposing Chinese labels to
# the application UI and API consumers.
LABEL_ZH = {
    "olive_fruit": "橄榄果实",
    "Healthy": "健康叶片",
    "healthy": "健康叶片",
    "aculus_olearius": "橄榄刺叶螨",
    "olive_peacock_spot": "橄榄孔雀斑病",
}


def label_to_zh(label: Any) -> str:
    value = str(label)
    return LABEL_ZH.get(value, value)


def task_to_zh(task: Any) -> str:
    return {
        "object_detection": "目标检测",
        "image_classification": "图像分类",
    }.get(str(task), str(task))


def scope_to_zh(scope: Any) -> str:
    return {
        "olive_fruit_detection": "油橄榄果实检测",
        "olive_leaf_disease_classification": "油橄榄叶片病虫害分类",
    }.get(str(scope), str(scope))


def _read_yolo_metadata() -> Dict[str, Any]:
    """Read optional training metadata without making model loading mandatory."""
    if not YOLO_METADATA.is_file():
        return {}
    try:
        import json
        payload = json.loads(YOLO_METADATA.read_text(encoding="utf-8-sig"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        import json
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}
def _env_path(name: str) -> Optional[Path]:
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser() if value else None


def _first_existing(env_name: str, candidates: Iterable[Path]) -> Optional[Path]:
    configured = _env_path(env_name)
    if configured:
        return configured if configured.is_file() else None
    return next((path for path in candidates if path.is_file()), None)


def _dependency_available(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except Exception:
        return False


def _path_string(path: Optional[Path]) -> Optional[str]:
    return str(path) if path else None


def _hybrid_checkpoint_compatible(path: Optional[Path]) -> bool:
    """Accept only checkpoints produced by the local olive training contract."""
    if not path or not _dependency_available("torch"):
        return False
    try:
        import torch

        try:
            checkpoint = torch.load(str(path), map_location="cpu", weights_only=True)
        except TypeError:
            checkpoint = torch.load(str(path), map_location="cpu")
        return bool(
            isinstance(checkpoint, dict)
            and isinstance(checkpoint.get("classes"), list)
            and checkpoint.get("classes")
            and isinstance(checkpoint.get("state_dict"), dict)
        )
    except Exception:
        return False


def model_status() -> Dict[str, Any]:
    """Return truthful deployment status without importing heavy packages."""
    yolo_weights = _first_existing("OLIVE_YOLO_WEIGHTS", DEFAULT_YOLO_WEIGHTS)
    yolo_data = _first_existing("OLIVE_YOLO_DATA", DEFAULT_YOLO_DATA)
    yolo_metadata = _read_yolo_metadata()
    disease_metadata = _read_json(DISEASE_CLASSIFIER_METADATA)
    hybrid_weights = _first_existing("OLIVE_HYBRID_WEIGHTS", DEFAULT_HYBRID_WEIGHTS)
    ultralytics_ready = _dependency_available("ultralytics")
    torch_ready = _dependency_available("torch")

    yolo_ready = bool(yolo_weights and ultralytics_ready)
    hybrid_checkpoint_valid = _hybrid_checkpoint_compatible(hybrid_weights)
    hybrid_ready = bool(hybrid_weights and torch_ready and hybrid_checkpoint_valid)
    return {
        "yolo": yolo_ready,
        "dual_branch": hybrid_ready,
        "lstm": False,
        "random_forest": False,
        "disease_classifier": bool(DISEASE_CLASSIFIER_WEIGHTS.is_file() and ultralytics_ready),
        "mode": "YOLOv11已部署" if yolo_ready else "模型待部署：规则与理论降级",
        "yolo_detail": {
            "dependency_installed": ultralytics_ready,
            "weights_found": bool(yolo_weights),
            "weights_path": _path_string(yolo_weights),
            "data_path": _path_string(yolo_data),
            "ready": yolo_ready,
            "task": yolo_metadata.get("task", "object_detection"),
            "task_zh": task_to_zh(yolo_metadata.get("task", "object_detection")),
            "label_scope": yolo_metadata.get("label_scope", "unknown"),
            "label_scope_zh": scope_to_zh(yolo_metadata.get("label_scope", "unknown")),
            "classes": yolo_metadata.get("classes", []),
            "classes_zh": [label_to_zh(item) for item in (yolo_metadata.get("classes", []) or [])],
            "dataset": yolo_metadata.get("dataset"),
            "warning": yolo_metadata.get("warning"),
            "status": "可执行油橄榄检测" if yolo_ready else "需要ultralytics和油橄榄best.pt",
            "source": SOURCE_INFO["yolo"],
        },
        "dual_branch_detail": {
            "architecture_available": torch_ready,
            "torch_installed": torch_ready,
            "weights_found": bool(hybrid_weights),
            "weights_path": _path_string(hybrid_weights),
            "checkpoint_format_valid": hybrid_checkpoint_valid,
            "ready": hybrid_ready,
            "status": "CNN+Transformer模型可推理" if hybrid_ready else "结构和训练接口已接入，等待油橄榄标注训练权重",
            "source": SOURCE_INFO["dual_branch"],
            "boundary": "仓库默认权重和类别属于木薯叶病害，不能直接用于油橄榄",
        },
        "disease_classifier_detail": {
            "ready": bool(DISEASE_CLASSIFIER_WEIGHTS.is_file() and ultralytics_ready),
            "weights_found": DISEASE_CLASSIFIER_WEIGHTS.is_file(),
            "weights_path": str(DISEASE_CLASSIFIER_WEIGHTS) if DISEASE_CLASSIFIER_WEIGHTS.is_file() else None,
            "task": disease_metadata.get("task", "image_classification"),
            "task_zh": task_to_zh(disease_metadata.get("task", "image_classification")),
            "label_scope": disease_metadata.get("label_scope", "unknown"),
            "label_scope_zh": scope_to_zh(disease_metadata.get("label_scope", "unknown")),
            "classes": disease_metadata.get("classes", []),
            "classes_zh": [label_to_zh(item) for item in (disease_metadata.get("classes", []) or [])],
            "dataset": disease_metadata.get("dataset"),
            "warning": disease_metadata.get("warning"),
            "status": "YOLOv11叶片病虫害分类已部署" if DISEASE_CLASSIFIER_WEIGHTS.is_file() and ultralytics_ready else "等待病虫害分类权重",
        },
        "sources": SOURCE_INFO,
    }


@lru_cache(maxsize=1)
def _dual_branch_class():
    """Build the optional gated CNN + Transformer model lazily."""
    import torch
    from torch import nn

    class ConvResidual(nn.Module):
        def __init__(self, channels: int):
            super().__init__()
            self.layers = nn.Sequential(
                nn.Conv2d(channels, channels, 3, padding=1, bias=False),
                nn.BatchNorm2d(channels), nn.SiLU(inplace=True),
                nn.Conv2d(channels, channels, 3, padding=1, bias=False),
                nn.BatchNorm2d(channels),
            )
            self.activation = nn.SiLU(inplace=True)

        def forward(self, x):
            return self.activation(x + self.layers(x))

    class OliveDualBranchNet(nn.Module):
        def __init__(self, num_classes: int):
            super().__init__()
            self.cnn = nn.Sequential(
                nn.Conv2d(3, 32, 3, stride=2, padding=1, bias=False),
                nn.BatchNorm2d(32), nn.SiLU(inplace=True),
                nn.Conv2d(32, 64, 3, stride=2, padding=1, bias=False),
                nn.BatchNorm2d(64), nn.SiLU(inplace=True),
                ConvResidual(64),
                nn.Conv2d(64, 128, 3, stride=2, padding=1, bias=False),
                nn.BatchNorm2d(128), nn.SiLU(inplace=True),
                ConvResidual(128), nn.AdaptiveAvgPool2d(1), nn.Flatten(),
            )
            self.patch_embed = nn.Conv2d(3, 128, kernel_size=16, stride=16)
            self.cls_token = nn.Parameter(torch.zeros(1, 1, 128))
            self.position = nn.Parameter(torch.zeros(1, 197, 128))
            layer = nn.TransformerEncoderLayer(
                d_model=128, nhead=4, dim_feedforward=256, dropout=0.1,
                batch_first=True, norm_first=True,
            )
            self.transformer = nn.TransformerEncoder(layer, num_layers=2)
            self.gate = nn.Sequential(nn.Linear(256, 128), nn.Sigmoid())
            self.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(128, num_classes))
            nn.init.trunc_normal_(self.cls_token, std=0.02)
            nn.init.trunc_normal_(self.position, std=0.02)

        def forward(self, x):
            local_features = self.cnn(x)
            patches = self.patch_embed(x).flatten(2).transpose(1, 2)
            cls = self.cls_token.expand(x.shape[0], -1, -1)
            tokens = torch.cat((cls, patches), dim=1) + self.position
            global_features = self.transformer(tokens)[:, 0]
            gate = self.gate(torch.cat((local_features, global_features), dim=1))
            fused = gate * local_features + (1.0 - gate) * global_features
            return self.classifier(fused)

    return OliveDualBranchNet


@lru_cache(maxsize=4)
def _load_dual_branch(weights_path: str):
    import torch

    try:
        checkpoint = torch.load(weights_path, map_location="cpu", weights_only=True)
    except TypeError:
        checkpoint = torch.load(weights_path, map_location="cpu")
    if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("classes"), list):
        raise ValueError("双分支权重缺少训练类别元数据")
    classes = [str(name) for name in checkpoint["classes"]]
    state_dict = checkpoint.get("state_dict")
    if not classes or not isinstance(state_dict, dict):
        raise ValueError("双分支权重格式无效")
    model = _dual_branch_class()(len(classes))
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    return model, classes


def dual_branch_assist(image: Any) -> Dict[str, Any]:
    """Run the trained gated fusion branch when an olive checkpoint exists."""
    status = model_status()["dual_branch_detail"]
    if not status["ready"]:
        return {
            "status": status["status"], "trained": False,
            "source": SOURCE_INFO["dual_branch"],
            "note": "当前没有油橄榄标注训练权重，不生成双分支病种预测。",
        }
    try:
        import torch

        rgb = image.convert("RGB").resize((224, 224))
        tensor = torch.frombuffer(bytearray(rgb.tobytes()), dtype=torch.uint8)
        tensor = tensor.reshape(224, 224, 3).permute(2, 0, 1).float().div_(255.0)
        mean = torch.tensor((0.485, 0.456, 0.406)).view(3, 1, 1)
        std = torch.tensor((0.229, 0.224, 0.225)).view(3, 1, 1)
        tensor = ((tensor - mean) / std).unsqueeze(0)
        model, classes = _load_dual_branch(status["weights_path"])
        with torch.inference_mode():
            probabilities = torch.softmax(model(tensor), dim=1)[0]
        index = int(torch.argmax(probabilities).item())
        return {
            "status": "CNN+Transformer双分支推理已执行", "trained": True,
            "raw_prediction": classes[index], "prediction": label_to_zh(classes[index]),
            "score": round(float(probabilities[index].item()), 4),
            "score_note": "模型Softmax输出，未经概率校准；不等同于农艺确诊概率",
            "source": SOURCE_INFO["dual_branch"],
        }
    except Exception as exc:
        return {
            "status": "双分支权重加载失败，已回退", "trained": False,
            "error": str(exc)[:300], "source": SOURCE_INFO["dual_branch"],
            "note": "未采用其他作物标签或权重输出油橄榄预测。",
        }


@lru_cache(maxsize=4)
def _load_yolo(weights_path: str):
    """Load a YOLO model only when the optional dependency is installed."""
    from ultralytics import YOLO  # type: ignore

    return YOLO(weights_path)


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    for method in ("tolist", "cpu"):
        try:
            value = getattr(value, method)()
        except (AttributeError, TypeError, ValueError):
            continue
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _one(value: Any, default: float = 0.0) -> float:
    values = _as_list(value)
    value = values[0] if values else value
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _class_name(names: Any, class_id: int) -> str:
    if isinstance(names, dict):
        return str(names.get(class_id, names.get(str(class_id), class_id)))
    if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
        return str(names[class_id])
    return str(class_id)


def _parse_result(result: Any) -> List[Dict[str, Any]]:
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []
    coordinates = _as_list(getattr(boxes, "xyxy", None))
    confidences = _as_list(getattr(boxes, "conf", None))
    classes = _as_list(getattr(boxes, "cls", None))
    names = getattr(result, "names", {})
    detections: List[Dict[str, Any]] = []
    for index, coordinate in enumerate(coordinates):
        values = _as_list(coordinate)
        if len(values) < 4:
            continue
        class_id = int(_one(classes[index] if index < len(classes) else 0))
        confidence = max(0.0, min(1.0, _one(confidences[index] if index < len(confidences) else 0)))
        detections.append({
            "class_id": class_id,
            "raw_label": _class_name(names, class_id),
            "label": label_to_zh(_class_name(names, class_id)),
            "confidence": round(confidence, 4),
            "box": [round(_one(values[position]), 2) for position in range(4)],
        })
    return detections


def run_yolo(data: bytes, filename: str) -> Dict[str, Any]:
    """Run YOLOv11 if available, otherwise return an explicit fallback state."""
    status = model_status()
    detail = status["yolo_detail"]
    if not detail["ready"]:
        return {"detections": [], "status": detail["status"], "model_status": status}

    suffix = Path(filename or "image.jpg").suffix.lower() or ".jpg"
    temporary_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(prefix="olive-pest-", suffix=suffix, delete=False) as handle:
            handle.write(data)
            temporary_path = handle.name
        model = _load_yolo(detail["weights_path"])
        results = model.predict(source=temporary_path, verbose=False)
        detections: List[Dict[str, Any]] = []
        for result in results or []:
            detections.extend(_parse_result(result))
        detections.sort(key=lambda item: item["confidence"], reverse=True)
        return {
            "detections": detections,
            "status": "YOLOv11检测已执行",
            "model_status": status,
        }
    except Exception as exc:
        # A bad/incompatible checkpoint should degrade to the existing rules,
        # while exposing the reason to the operator instead of hiding it.
        return {
            "detections": [],
            "status": "YOLO权重加载失败，已回退规则分析",
            "error": str(exc)[:300],
            "model_status": status,
        }
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


def run_disease_classifier(data: bytes, filename: str) -> Dict[str, Any]:
    """Classify an olive leaf image with the separately trained YOLOv11-cls model."""
    status = model_status()
    detail = status.get("disease_classifier_detail", {})
    if not detail.get("ready"):
        return {"prediction": None, "probabilities": [], "model_status": status, "status": detail.get("status")}
    temporary_path = None
    try:
        suffix = Path(filename or "image.jpg").suffix.lower() or ".jpg"
        with tempfile.NamedTemporaryFile(prefix="olive-disease-", suffix=suffix, delete=False) as handle:
            handle.write(data)
            temporary_path = handle.name
        from ultralytics import YOLO
        result = YOLO(detail["weights_path"])(temporary_path, verbose=False)[0]
        probs = getattr(result, "probs", None)
        values = getattr(probs, "data", None) if probs is not None else None
        if values is None:
            return {"prediction": None, "probabilities": [], "model_status": status, "status": "分类模型未返回概率"}
        scores = values.detach().cpu().tolist() if hasattr(values, "detach") else list(values)
        classes = detail.get("classes") or []
        probabilities = []
        for i, value in enumerate(scores):
            raw_label = classes[i] if i < len(classes) else str(i)
            probabilities.append({
                "raw_label": raw_label,
                "label": label_to_zh(raw_label),
                "confidence": round(float(value), 4),
            })
        probabilities.sort(key=lambda item: item["confidence"], reverse=True)
        return {"prediction": probabilities[0] if probabilities else None, "probabilities": probabilities, "model_status": status, "status": "YOLOv11病虫害分类已执行"}
    except Exception as exc:
        return {"prediction": None, "probabilities": [], "model_status": status, "status": "病虫害分类降级", "error": str(exc)[:300]}
    finally:
        if temporary_path:
            try: os.unlink(temporary_path)
            except OSError: pass


def dual_branch_status() -> Dict[str, Any]:
    """Expose the GL-MobFormer-inspired interface without unsafe inference."""
    return model_status()["dual_branch_detail"]
