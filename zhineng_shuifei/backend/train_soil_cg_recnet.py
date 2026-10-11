"""Train a soil-texture CG-RecNet-inspired model from available soil data.

The supplied China Soil Characteristics Dataset has sand/clay rasters but no
human texture labels.  This trainer therefore creates labels with the same
USDA rule used by the API and records that fact in the checkpoint metadata.
The network is a tabular adaptation of the paper's gated feature-fusion idea,
not a claim that the original microscopy model transfers unchanged.
"""
from __future__ import annotations

import argparse
import json
import random
import struct
from pathlib import Path


CLASSES = ["砂土", "砂壤土", "壤土", "粉壤土", "粉土", "黏壤土", "砂质黏壤土", "黏土", "砂质黏土"]


def texture_label(sand: float, clay: float) -> int:
    silt = 100.0 - sand - clay
    if clay >= 40 and sand <= 45 and silt <= 40:
        name = "黏土"
    elif clay >= 27 and clay < 40 and sand > 20 and sand <= 45:
        name = "黏壤土"
    elif clay >= 27 and sand > 45:
        name = "砂质黏壤土"
    elif silt >= 80 and clay < 12:
        name = "粉土"
    elif silt >= 50 and clay < 27:
        name = "粉壤土"
    elif sand >= 85 and clay < 10:
        name = "砂土"
    elif sand >= 70 and clay < 20:
        name = "砂壤土"
    elif clay < 27 and sand < 52 and silt < 50:
        name = "壤土"
    else:
        name = "砂质黏土"
    if name not in CLASSES:
        CLASSES.append(name)
    return CLASSES.index(name)


def raster_samples(root: Path, count: int, seed: int):
    random.seed(seed)
    # psd.hdr is the authoritative raster dimensions for this dataset.
    cols, rows = 7389, 4247
    sand_path, clay_path = root / "flt" / "sand1.flt", root / "flt" / "clay1.flt"
    if not sand_path.is_file() or not clay_path.is_file():
        raise FileNotFoundError("需要 A China Soil Characteristics Dataset/flt/sand1.flt 与 clay1.flt")
    with sand_path.open("rb") as sand_file, clay_path.open("rb") as clay_file:
        for _ in range(count):
            row, col = random.randrange(rows), random.randrange(cols)
            offset = (row * cols + col) * 4
            sand_file.seek(offset); clay_file.seek(offset)
            raw_s, raw_c = sand_file.read(4), clay_file.read(4)
            if len(raw_s) < 4 or len(raw_c) < 4:
                continue
            sand, clay = struct.unpack("<f", raw_s)[0], struct.unpack("<f", raw_c)[0]
            if sand <= -9998 or clay <= -9998:
                continue
            if sand <= 1: sand *= 100
            if clay <= 1: clay *= 100
            if 0 <= sand <= 100 and 0 <= clay <= 100 and sand + clay <= 100:
                yield (sand / 100.0, clay / 100.0), texture_label(sand, clay)


class SoilNetSpec:
    """Architecture description kept dependency-free for dataset validation."""
    name = "CG-RecNet-inspired gated attention tabular classifier"
    input_features = ["sand_pct", "clay_pct", "silt_pct"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("models/soil_cg_recnet/best.pt"))
    parser.add_argument("--samples", type=int, default=20000)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset, random_split

    rows = list(raster_samples(args.data_root, args.samples, args.seed))
    if len(rows) < 100:
        raise SystemExit("有效栅格样本少于100条，不能训练")
    x = torch.tensor([[a, b, 1.0 - a - b] for (a, b), _ in rows], dtype=torch.float32)
    y = torch.tensor([label for _, label in rows], dtype=torch.long)
    dataset = TensorDataset(x, y)
    valid_size = max(1, int(len(dataset) * 0.2))
    train_set, valid_set = random_split(dataset, [len(dataset) - valid_size, valid_size], generator=torch.Generator().manual_seed(args.seed))
    train_loader = DataLoader(train_set, batch_size=256, shuffle=True)
    valid_loader = DataLoader(valid_set, batch_size=512)

    class CGRecNetSoil(nn.Module):
        def __init__(self):
            super().__init__()
            self.local = nn.Sequential(nn.Linear(3, 64), nn.LayerNorm(64), nn.GELU(), nn.Linear(64, 64))
            self.context = nn.Sequential(nn.Linear(3, 64), nn.LayerNorm(64), nn.GELU(), nn.Linear(64, 64))
            self.gate = nn.Sequential(nn.Linear(128, 64), nn.Sigmoid())
            self.head = nn.Sequential(nn.Linear(64, 32), nn.GELU(), nn.Linear(32, len(CLASSES)))
        def forward(self, values):
            local, context = self.local(values), self.context(values)
            gate = self.gate(torch.cat([local, context], dim=1))
            return self.head(gate * local + (1 - gate) * context)

    model = CGRecNetSoil()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    best = -1.0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, args.epochs + 1):
        model.train()
        for values, labels in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(values), labels)
            loss.backward(); optimizer.step()
        model.eval(); correct = total = 0
        with torch.inference_mode():
            for values, labels in valid_loader:
                correct += int((model(values).argmax(1) == labels).sum())
                total += len(labels)
        accuracy = correct / max(total, 1)
        print(f"epoch={epoch} validation_pseudo_accuracy={accuracy:.4f}")
        if accuracy >= best:
            best = accuracy
            torch.save({"state_dict": model.state_dict(), "classes": CLASSES, "architecture": SoilNetSpec.name,
                        "input_features": SoilNetSpec.input_features, "validation_pseudo_accuracy": accuracy,
                        "label_source": "USDA rule pseudo-label", "supervised_ground_truth": False,
                        "paper_accuracy_not_transferred": True}, args.output)
    metadata = {"architecture": SoilNetSpec.name, "classes": CLASSES, "samples": len(rows),
                "validation_pseudo_accuracy": best, "label_source": "USDA rule pseudo-label",
                "supervised_ground_truth": False, "paper_accuracy_not_transferred": True}
    args.output.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved={args.output} pseudo_accuracy={best:.4f}")


if __name__ == "__main__":
    main()
