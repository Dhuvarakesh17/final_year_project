"""
YOLOv8 Weed Detection Model Fine-Tuning Pipeline
Trains Ultralytics YOLOv8n on the DeepWeeds spatial dataset.
Saves best model weights to ml_models/weights/yolov8_weeds.pt
"""
import os
import sys
import shutil
import json
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure Ultralytics config is local
os.environ["YOLO_CONFIG_DIR"] = str(BASE_DIR / "ml_models")

from ultralytics import YOLO
import torch

def train_weed_yolo(epochs: int = 15, batch_size: int = 16, imgsz: int = 256):
    data_yaml = BASE_DIR / "data" / "datasets" / "weed_detection" / "data.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"Weed detection dataset config not found at {data_yaml}")

    weights_dir = BASE_DIR / "ml_models" / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    target_weights = weights_dir / "yolov8_weeds.pt"

    device = 0 if torch.cuda.is_available() else "cpu"
    print(f"Initializing YOLOv8 training on device: {device} (GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    # Load foundation model
    model = YOLO("yolov8n.pt")

    print(f"\n--- Commencing YOLOv8 Weed Fine-Tuning ({epochs} epochs, imgsz={imgsz}, batch={batch_size}) ---")
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        project=str(BASE_DIR / "ml_models" / "training"),
        name="yolo_weeds",
        exist_ok=True,
        workers=2,
        optimizer="AdamW",
        lr0=0.001,
        save=True,
        plots=True,
        verbose=True
    )

    # Locate and copy best weights
    best_pt = BASE_DIR / "ml_models" / "training" / "yolo_weeds" / "weights" / "best.pt"
    if best_pt.exists():
        shutil.copy2(best_pt, target_weights)
        print(f"\nSuccessfully saved fine-tuned YOLOv8 weed model to {target_weights}")
    else:
        print("Warning: best.pt was not found in training output directory.")

    print("YOLOv8 training and validation completed.")
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=256, help="Image resolution")
    args = parser.parse_args()

    train_weed_yolo(epochs=args.epochs, batch_size=args.batch_size, imgsz=args.imgsz)

