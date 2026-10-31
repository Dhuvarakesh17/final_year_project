"""
DeepWeeds Dataset to YOLO Format Converter
Reads official train/val subsets and formats into YOLO dataset layout with images and labels.
Uses high-performance file hardlinks (instant 0-overhead) with copy fallback.
"""
import os
import shutil
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def fast_link_or_copy(src: Path, dst: Path):
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)

def prepare_deepweeds_yolo(
    deepweeds_dir: str = r"d:\final_year_project\data\datasets\deepweeds",
    target_dir: str = r"d:\final_year_project\data\datasets\weed_detection",
    fold: int = 0,
    binary_mode: bool = True
):
    base_path = Path(deepweeds_dir)
    images_dir = base_path / "images"
    labels_csv_dir = base_path / "labels"

    train_csv_path = labels_csv_dir / f"train_subset{fold}.csv"
    val_csv_path = labels_csv_dir / f"val_subset{fold}.csv"

    if not train_csv_path.exists() or not val_csv_path.exists():
        print(f"Subset CSVs for fold {fold} not found. Reading labels.csv...")
        full_csv = labels_csv_dir / "labels.csv"
        df = pd.read_csv(full_csv)
        train_df = df.sample(frac=0.8, random_state=42)
        val_df = df.drop(train_df.index)
    else:
        train_df = pd.read_csv(train_csv_path)
        val_df = pd.read_csv(val_csv_path)

    dst_path = Path(target_dir)
    img_train_dir = dst_path / "images" / "train"
    img_val_dir = dst_path / "images" / "val"
    lbl_train_dir = dst_path / "labels" / "train"
    lbl_val_dir = dst_path / "labels" / "val"

    for d in [img_train_dir, img_val_dir, lbl_train_dir, lbl_val_dir]:
        d.mkdir(parents=True, exist_ok=True)

    def process_subset(df: pd.DataFrame, target_img_dir: Path, target_lbl_dir: Path, desc: str):
        count = 0
        for _, row in tqdm(df.iterrows(), total=len(df), desc=desc):
            fname = row["Filename"]
            lbl = int(row["Label"])
            src_img = images_dir / fname

            if not src_img.exists():
                continue

            dst_img = target_img_dir / fname
            fast_link_or_copy(src_img, dst_img)

            txt_name = Path(fname).stem + ".txt"
            dst_lbl = target_lbl_dir / txt_name

            if binary_mode:
                # Class 8 is Negative (crop/pasture), classes 0-7 are weed species
                if lbl == 8:
                    yolo_class = 0  # crop
                    box_str = f"{yolo_class} 0.5 0.5 0.90 0.90\n"
                else:
                    yolo_class = 1  # weed
                    box_str = f"{yolo_class} 0.5 0.5 0.85 0.85\n"
            else:
                yolo_class = lbl
                box_str = f"{yolo_class} 0.5 0.5 0.85 0.85\n"

            with open(dst_lbl, "w") as f:
                f.write(box_str)

            count += 1
        return count

    print(f"Processing Train Split (Fold {fold})...")
    train_count = process_subset(train_df, img_train_dir, lbl_train_dir, "Train Split")

    print(f"Processing Validation Split (Fold {fold})...")
    val_count = process_subset(val_df, img_val_dir, lbl_val_dir, "Val Split")

    # Update data.yaml
    yaml_content = f"""# YOLO Dataset Configuration - DeepWeeds
path: {dst_path.as_posix()}
train: images/train
val: images/val

names:
  0: crop
  1: weed
""" if binary_mode else f"""# YOLO Dataset Configuration - DeepWeeds Multi-Class
path: {dst_path.as_posix()}
train: images/train
val: images/val

names:
  0: Chinee apple
  1: Lantana
  2: Parkinsonia
  3: Parthenium
  4: Prickly acacia
  5: Rubber vine
  6: Siam weed
  7: Snake weed
  8: Negative_Crop
"""

    with open(dst_path / "data.yaml", "w") as f:
        f.write(yaml_content)

    print("\n--- DeepWeeds YOLO Preparation Complete ---")
    print(f"Train samples: {train_count}")
    print(f"Val samples:   {val_count}")
    print(f"data.yaml updated at: {dst_path / 'data.yaml'}")

if __name__ == "__main__":
    prepare_deepweeds_yolo()
