"""Train the local gated CNN + Transformer olive-leaf classifier.

The directory must be an ImageFolder dataset::

    dataset/healthy/*.jpg
    dataset/peacock_spot/*.jpg
    dataset/anthracnose/*.jpg

The output checkpoint contains the class names and state dict expected by
``pest_models.py``.  This script is optional and requires ``requirements-ml``.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the olive dual-branch classifier")
    parser.add_argument("data", type=Path, help="ImageFolder root")
    parser.add_argument("--output", type=Path, default=Path("models/pest_hybrid/best.pt"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--image-size", type=int, choices=(224,), default=224,
                        help="当前模型固定使用224；保留参数仅用于明确训练输入契约")
    args = parser.parse_args()

    import torch
    from torch import nn
    from torch.utils.data import DataLoader, random_split
    from torchvision import datasets, transforms

    from pest_models import _dual_branch_class

    transform = transforms.Compose([
        transforms.Resize((args.image_size, args.image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(8),
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])
    dataset = datasets.ImageFolder(str(args.data), transform=transform)
    if len(dataset.classes) < 2 or len(dataset) < 10:
        raise SystemExit("至少需要2个类别和10张图片；正式训练请使用专家复核的更大样本")
    validation_size = max(1, round(len(dataset) * 0.2))
    train_size = len(dataset) - validation_size
    train_set, validation_set = random_split(
        dataset, [train_size, validation_size],
        generator=torch.Generator().manual_seed(42),
    )
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=0)
    validation_loader = DataLoader(validation_set, batch_size=args.batch_size, shuffle=False, num_workers=0)
    model = _dual_branch_class()(len(dataset.classes))
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    best_accuracy = -1.0
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        for images, labels in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(images), labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        model.eval()
        correct = total = 0
        with torch.inference_mode():
            for images, labels in validation_loader:
                correct += int((model(images).argmax(1) == labels).sum().item())
                total += len(labels)
        accuracy = correct / max(1, total)
        print(f"epoch={epoch} validation_accuracy={accuracy:.4f}")
        if accuracy >= best_accuracy:
            best_accuracy = accuracy
            torch.save({
                "classes": dataset.classes,
                "state_dict": model.state_dict(),
                "validation_accuracy": accuracy,
                "architecture": "gated-cnn-transformer-v1",
            }, args.output)
    print(f"saved={args.output} classes={dataset.classes} best_validation_accuracy={best_accuracy:.4f}")


if __name__ == "__main__":
    main()
