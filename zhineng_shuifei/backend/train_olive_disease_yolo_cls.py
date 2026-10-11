"""Train a YOLOv11 classification model on the olive-leaf disease dataset.

Expected input (the structure used by 2nd-experiment-haythem.ipynb)::

    dataset/train/<class>/*.jpg
    dataset/test/<class>/*.jpg

This is a classification model, not a bounding-box detector.  It is kept
separate from ``models/pest_yolo`` which contains the olive-fruit detector.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parent
DEFAULT_OUTPUT = BACKEND / "models" / "pest_disease_cls"


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv11-cls on olive leaf disease images")
    parser.add_argument("data", type=Path, help="ImageFolder root containing train/ and test/ or class folders")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=224)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()
    if args.epochs < 1 or args.imgsz < 64 or args.batch < 1:
        raise SystemExit("epochs, batch must be positive and imgsz >= 64")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("ultralytics is required; install backend/requirements-ml.txt") from exc

    root = args.data
    train_dir = root / "train"
    val_dir = root / "test"
    if not train_dir.is_dir():
        train_dir = root
    if not val_dir.is_dir():
        raise SystemExit(f"Missing validation/test directory: {root / 'test'}")
    classes = sorted(p.name for p in train_dir.iterdir() if p.is_dir())
    if len(classes) < 2:
        raise SystemExit("At least two class directories are required")

    args.output.mkdir(parents=True, exist_ok=True)
    project = args.output / "runs"
    device = args.device or ("0" if __import__("torch").cuda.is_available() else "cpu")
    # Prefer the pretrained classifier when available.  In offline deployments
    # fall back to the bundled YOLOv11 classification graph and train from scratch.
    local_pretrained = BACKEND.parent / "yolo11n-cls.pt"
    if local_pretrained.is_file():
        model = YOLO(str(local_pretrained))
        pretrained = True
    else:
        model = YOLO("yolo11-cls.yaml")
        pretrained = False
    result = model.train(
        data=str(root), epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
        workers=args.workers, device=device, project=str(project),
        name="olive_disease_yolo11n_cls", exist_ok=True, pretrained=pretrained,
    )
    candidates = sorted(project.glob("**/weights/best.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit("Training finished without best.pt")
    installed = args.output / "best.pt"
    shutil.copy2(candidates[0], installed)
    metrics = {}
    for key, value in (getattr(result, "results_dict", {}) or {}).items():
        try:
            metrics[key] = float(value)
        except (TypeError, ValueError):
            metrics[key] = str(value)
    metadata = {
        "task": "image_classification",
        "label_scope": "olive_leaf_disease_classification",
        "architecture": "YOLOv11n-cls",
        "classes": classes,
        "dataset_root": str(root),
        "installed_weights": str(installed),
        "device": device,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "warning": "Classification result is not a disease bounding box; verify labels and review by a plant-protection expert.",
    }
    (args.output / "model_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"installed={installed}\nclasses={classes}\nmetrics={metrics}")


if __name__ == "__main__":
    main()
