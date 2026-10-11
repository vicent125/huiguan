"""Train and install an Ultralytics YOLOv11 olive-fruit detector.

The resulting checkpoint is copied to ``models/pest_yolo/best.pt`` and is
loaded by the existing pest-analysis API.  This dataset contains one class,
``olive_fruit``.  It does not train an olive disease or pest classifier.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parent
DEFAULT_SOURCE = BACKEND / "models" / "olive-fruit-dataset" / "olive_detection_raw" / "olive_detection_raw" / "train"
DEFAULT_DATASET = BACKEND / "models" / "olive-fruit-yolo"
DEFAULT_OUTPUT = BACKEND / "models" / "pest_yolo"


def _find_best(run_root: Path) -> Path:
    candidates = sorted(run_root.glob("**/weights/best.pt"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError(f"Training finished without best.pt under {run_root}")
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv11 on the olive fruit dataset")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--device", default=None, help="cpu, 0, or leave empty for auto")
    parser.add_argument("--skip-prepare", action="store_true")
    args = parser.parse_args()
    if args.epochs < 1 or args.imgsz < 160 or args.batch < 1:
        raise SystemExit("epochs, imgsz and batch must be positive (imgsz >= 160)")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("ultralytics is required; install backend/requirements-ml.txt") from exc

    if not args.skip_prepare:
        from prepare_olive_yolo_dataset import prepare

        summary = prepare(args.source, args.dataset)
        print(f"prepared={summary}")
    data_yaml = args.dataset / "data.yaml"
    if not data_yaml.is_file():
        raise SystemExit(f"Missing {data_yaml}; run without --skip-prepare first")

    args.output.mkdir(parents=True, exist_ok=True)
    run_root = args.output / "runs"
    device = args.device or ("0" if __import__("torch").cuda.is_available() else "cpu")
    model = YOLO("yolo11n.pt")
    results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        device=device,
        project=str(run_root),
        name="olive_fruit_yolo11n",
        exist_ok=True,
        pretrained=True,
        cache=False,
        plots=False,
        verbose=True,
    )
    best = _find_best(run_root)
    installed = args.output / "best.pt"
    shutil.copy2(best, installed)
    installed_data = args.output / "data.yaml"
    shutil.copy2(data_yaml, installed_data)
    raw_metrics = getattr(results, "results_dict", {}) or {}
    metrics = {}
    for key, value in raw_metrics.items():
        try:
            metrics[key] = float(value)
        except (TypeError, ValueError):
            metrics[key] = str(value)
    metadata = {
        "task": "object_detection",
        "label_scope": "olive_fruit_detection",
        "classes": ["olive_fruit"],
        "architecture": "YOLOv11n",
        "dataset": "danielvalyano/olive-fruit-object-detection",
        "dataset_license": "CC BY-NC-SA 4.0",
        "source_images": str(args.source),
        "data_yaml": str(installed_data),
        "installed_weights": str(installed),
        "device": device,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "warning": "This checkpoint detects olive fruit, not disease or pest classes.",
        "metrics": metrics,
    }
    (args.output / "model_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"installed={installed}")
    print(f"metadata={args.output / 'model_metadata.json'}")


if __name__ == "__main__":
    main()
