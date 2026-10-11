"""Prepare the Kaggle olive-fruit YOLO dataset for a reproducible train/val split.

The attached notebook only visualizes the Kaggle dataset.  This helper turns
its ``train/images`` and ``train/labels`` folders into the directory layout
expected by Ultralytics.  It uses hard links when the filesystem allows them,
so the 224 MB source archive is not copied again.
"""
from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _link_or_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    try:
        target.hardlink_to(source)
    except (OSError, NotImplementedError):
        shutil.copy2(source, target)


def prepare(source: Path, output: Path, validation_fraction: float = 0.2, seed: int = 42) -> dict:
    image_dir = source / "images"
    label_dir = source / "labels"
    if not image_dir.is_dir() or not label_dir.is_dir():
        raise SystemExit(f"Expected images/ and labels/ under {source}")
    images = sorted(path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
    pairs = [(image, label_dir / f"{image.stem}.txt") for image in images]
    missing = [image.name for image, label in pairs if not label.is_file()]
    if missing:
        raise SystemExit(f"Missing labels for {len(missing)} images; first: {missing[:3]}")
    if len(pairs) < 10:
        raise SystemExit("At least 10 labelled images are required")

    # The raw Kaggle split contains multiple augmented files per source image.
    # Keep all variants of a source image in one split to avoid leakage.
    groups: dict[str, list[tuple[Path, Path]]] = {}
    for pair in pairs:
        source_key = pair[0].name.split(".rf.", 1)[0]
        groups.setdefault(source_key, []).append(pair)
    group_items = list(groups.values())
    random.Random(seed).shuffle(group_items)
    validation_group_count = max(1, round(len(group_items) * validation_fraction))
    validation = [pair for group in group_items[:validation_group_count] for pair in group]
    training = [pair for group in group_items[validation_group_count:] for pair in group]
    for split, split_pairs in (("train", training), ("val", validation)):
        for kind in ("images", "labels"):
            shutil.rmtree(output / kind / split, ignore_errors=True)
        (output / "labels" / f"{split}.cache").unlink(missing_ok=True)
        for image, label in split_pairs:
            _link_or_copy(image, output / "images" / split / image.name)
            _link_or_copy(label, output / "labels" / split / label.name)

    yaml_text = (
        f"path: {output.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        "  0: olive_fruit\n"
    )
    (output / "data.yaml").parent.mkdir(parents=True, exist_ok=True)
    (output / "data.yaml").write_text(yaml_text, encoding="utf-8")
    return {"images": len(pairs), "train": len(training), "val": len(validation), "data": str(output / "data.yaml")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare olive fruit images and YOLO labels")
    parser.add_argument("source", type=Path, help="Folder containing images/ and labels/")
    parser.add_argument("--output", type=Path, required=True, help="YOLO dataset output folder")
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not 0.05 <= args.val_fraction <= 0.5:
        raise SystemExit("--val-fraction must be between 0.05 and 0.5")
    print(prepare(args.source, args.output, args.val_fraction, args.seed))


if __name__ == "__main__":
    main()
