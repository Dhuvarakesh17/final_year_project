"""
EfficientNet-B0 Leaf Disease Classifier Training Pipeline
Trains on 15-class Solanaceae subset of PlantVillage dataset.
Saves model weights to ml_models/weights/efficientnet_disease.pt
Includes temperature scaling calibration.
"""
import os
import sys
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.services.ml_inference.disease_classifier import PLANTVILLAGE_CLASSES

def get_data_loaders(data_dir: Path, batch_size: int = 32, num_workers: int = 2):
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(f"Processed dataset directories not found in {data_dir}")

    train_transforms = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transforms)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transforms)

    print(f"Loaded {len(train_dataset)} training samples, {len(val_dataset)} validation samples.")
    print(f"Dataset classes ({len(train_dataset.classes)}): {train_dataset.classes}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    return train_loader, val_loader, train_dataset.classes

def build_model(num_classes: int = 15, device: str = "cpu") -> nn.Module:
    print("Initializing EfficientNet-B0 with pre-trained ImageNet weights...")
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(in_features, num_classes)
    )
    
    return model.to(device)

def train_epoch(model, loader, criterion, optimizer, scaler, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for i, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()

        if scaler and device.type == "cuda":
            with torch.cuda.amp.autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)

        if (i + 1) % 50 == 0 or (i + 1) == len(loader):
            print(f"  Batch [{i+1}/{len(loader)}] - Loss: {loss.item():.4f} - Acc: {(correct/total)*100:.2f}%")

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc

def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_logits = []
    all_labels = []

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

            all_logits.append(outputs.cpu())
            all_labels.append(labels.cpu())

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc, torch.cat(all_logits), torch.cat(all_labels)

def calibrate_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """Calculates optimal Platt scaling temperature parameter via NLL optimization"""
    temperature = nn.Parameter(torch.ones(1) * 1.5)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.LBFGS([temperature], lr=0.01, max_iter=50)

    def eval():
        optimizer.zero_grad()
        loss = criterion(logits / temperature, labels)
        loss.backward()
        return loss

    optimizer.step(eval)
    calibrated = float(temperature.item())
    print(f"Optimal temperature calibration factor: {calibrated:.4f}")
    return max(0.5, min(2.5, calibrated))

def main(epochs: int = 10, batch_size: int = 32, lr: float = 1e-3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Starting training on device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    data_dir = BASE_DIR / "data" / "datasets" / "leaf_disease" / "processed"
    weights_dir = BASE_DIR / "ml_models" / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    target_weights_path = weights_dir / "efficientnet_disease.pt"

    train_loader, val_loader, class_names = get_data_loaders(data_dir, batch_size=batch_size)
    num_classes = len(class_names)

    model = build_model(num_classes=num_classes, device=device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    scaler = torch.cuda.amp.GradScaler() if torch.cuda.is_available() else None

    best_val_acc = 0.0
    best_logits = None
    best_labels = None
    history = []

    print(f"\n--- Commencing EfficientNet-B0 Fine-Tuning for {epochs} Epochs ---")
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        print(f"\nEpoch {epoch}/{epochs} (lr={scheduler.get_last_lr()[0]:.6f})")

        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, scaler, device)
        val_loss, val_acc, val_logits, val_lbls = validate(model, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - epoch_start
        print(f"Epoch {epoch} complete in {elapsed:.1f}s | Train Loss: {train_loss:.4f}, Train Acc: {train_acc*100:.2f}% | Val Loss: {val_loss:.4f}, Val Acc: {val_acc*100:.2f}%")

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc
        })

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_logits = val_logits
            best_labels = val_lbls
            print(f"--> Validation accuracy improved to {best_val_acc*100:.2f}%. Saving checkpoint to {target_weights_path}...")
            torch.save(model.state_dict(), target_weights_path)

    total_time = time.time() - start_time
    print(f"\nTraining completed in {total_time/60:.2f} minutes. Best Validation Accuracy: {best_val_acc*100:.2f}%")

    if best_logits is not None and best_labels is not None:
        calib_temp = calibrate_temperature(best_logits, best_labels)
    else:
        calib_temp = 1.15

    # Save training history & metadata
    metadata = {
        "architecture": "EfficientNet-B0",
        "dataset": "PlantVillage-15-Classes",
        "num_classes": num_classes,
        "classes": class_names,
        "best_val_accuracy": round(best_val_acc * 100, 2),
        "temperature_scaling": round(calib_temp, 4),
        "total_training_epochs": epochs,
        "training_time_sec": round(total_time, 1),
        "history": history
    }

    meta_path = weights_dir / "disease_classifier_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model training metadata to {meta_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    args = parser.parse_args()

    main(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)

