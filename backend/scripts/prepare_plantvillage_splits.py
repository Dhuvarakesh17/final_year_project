"""
PlantVillage Dataset Preparation Script
Performs a deterministic, stratified 80% train / 20% validation split.
"""
import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm

def prepare_plantvillage(
    source_dir: str = r"d:\final_year_project\data\datasets\plant_village",
    target_dir: str = r"d:\final_year_project\data\datasets\leaf_disease\processed",
    train_ratio: float = 0.8,
    seed: int = 42
):
    random.seed(seed)
    src_path = Path(source_dir)
    dst_path = Path(target_dir)

    train_dir = dst_path / "train"
    val_dir = dst_path / "val"
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    class_folders = [f for f in src_path.iterdir() if f.is_dir()]
    print(f"Found {len(class_folders)} classes in {source_dir}")

    total_train = 0
    total_val = 0

    for folder in tqdm(sorted(class_folders), desc="Splitting classes"):
        class_name = folder.name
        images = [f for f in folder.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
        random.shuffle(images)

        split_idx = int(len(images) * train_ratio)
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]

        cls_train_dir = train_dir / class_name
        cls_val_dir = val_dir / class_name
        cls_train_dir.mkdir(parents=True, exist_ok=True)
        cls_val_dir.mkdir(parents=True, exist_ok=True)

        for img in train_imgs:
            dest = cls_train_dir / img.name
            if not dest.exists():
                shutil.copy2(img, dest)
            total_train += 1

        for img in val_imgs:
            dest = cls_val_dir / img.name
            if not dest.exists():
                shutil.copy2(img, dest)
            total_val += 1

    print("\n--- PlantVillage Split Complete ---")
    print(f"Training Images:   {total_train}")
    print(f"Validation Images: {total_val}")
    print(f"Total:             {total_train + total_val}")
    print(f"Output Directory:  {target_dir}")

if __name__ == "__main__":
    prepare_plantvillage()

