"""
Macro Foliar & Weed Inspection Video Generator (1080p Full HD)
Generates high-definition agricultural video showcasing prominent, clear-cut leaves
with actual PlantVillage disease lesions and surrounding DeepWeeds clusters.
"""
import os
import cv2
import numpy as np
from pathlib import Path

def create_macro_leaf_video(
    output_path: str = r"d:\final_year_project\data\raw_videos\macro_leaf_disease_inspection_1080p.mp4",
    duration_sec: int = 10,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080
):
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    base_pv = Path(r"d:\final_year_project\data\datasets\leaf_disease\processed\train")
    
    # Categories to showcase
    categories = [
        "Tomato_Early_blight",
        "Tomato_healthy",
        "Tomato_Late_blight",
        "Tomato_Septoria_leaf_spot",
        "Tomato_Bacterial_spot",
        "Potato___Early_blight",
        "Tomato_healthy",
    ]

    leaf_assets = []
    for cat in categories:
        cat_dir = base_pv / cat
        if cat_dir.exists():
            files = [f for f in cat_dir.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
            if files:
                img = cv2.imread(str(files[0]))
                if img is not None:
                    leaf_assets.append((cat, img))

    # Fallback if some folders are missing
    if not leaf_assets:
        print("Warning: No PlantVillage images found, using fallback synthetic leaves.")
        fallback = np.full((500, 500, 3), (35, 160, 45), dtype=np.uint8)
        leaf_assets.append(("Tomato_healthy", fallback))

    # Fetch DeepWeeds
    dw_dir = Path(r"d:\final_year_project\data\datasets\deepweeds\images")
    weed_assets = []
    if dw_dir.exists():
        w_files = [f for f in dw_dir.iterdir() if f.suffix.lower() in [".jpg", ".png"]][:8]
        for wf in w_files:
            img = cv2.imread(str(wf))
            if img is not None:
                weed_assets.append(img)

    # Function to create clean, sharp, natural circular-masked plant patches
    def prepare_macro_asset(img, target_size=(560, 560)):
        resized = cv2.resize(img, target_size, interpolation=cv2.INTER_LANCZOS4)
        mask = np.zeros((target_size[1], target_size[0]), dtype=np.uint8)
        cv2.ellipse(
            mask,
            (target_size[0] // 2, target_size[1] // 2),
            (target_size[0] // 2 - 15, target_size[1] // 2 - 15),
            0, 0, 360, 255, -1
        )
        mask = cv2.GaussianBlur(mask, (19, 19), 0)
        return resized, mask

    prepared_leaves = [(cat, prepare_macro_asset(img, (620, 620))) for cat, img in leaf_assets]
    prepared_weeds = [prepare_macro_asset(img, (280, 280)) for img in weed_assets] if weed_assets else []

    total_frames = duration_sec * fps
    virtual_width = 7500  # Virtual length of the plant row bed

    # Place macro leaves spaced evenly along the central ridge
    leaf_instances = []
    spacing = 800
    for i in range(len(prepared_leaves)):
        lx = 600 + i * spacing
        ly = height // 2
        leaf_instances.append({
            "x": lx,
            "y": ly,
            "category": prepared_leaves[i][0],
            "asset": prepared_leaves[i][1]
        })

    # Place weeds in furrows above and below the leaf bed
    weed_instances = []
    if prepared_weeds:
        for i in range(12):
            wx = 400 + i * 550 + np.random.randint(-40, 40)
            wy = 180 if (i % 2 == 0) else height - 180
            weed_instances.append({
                "x": wx,
                "y": wy,
                "asset": prepared_weeds[i % len(prepared_weeds)]
            })

    # Create Video Writer (H.264 / MP4V)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(out_file), fourcc, fps, (width, height))

    print(f"Generating 1080p Macro Foliar Inspection Video: {total_frames} frames ({duration_sec}s @ {fps}fps)...")

    for f_idx in range(total_frames):
        t = f_idx / float(total_frames)
        cam_x = int(t * (virtual_width - width))

        # Gentle camera breathing jitter
        jitter_x = int(np.sin(f_idx * 0.1) * 3)
        jitter_y = int(np.cos(f_idx * 0.08) * 4)

        # 1. Warm organic agricultural soil bed
        frame = np.full((height, width, 3), (35, 60, 85), dtype=np.uint8)

        # Furrow depth shading
        cv2.rectangle(frame, (0, 0), (width, 240), (26, 45, 68), -1)
        cv2.rectangle(frame, (0, height - 240), (width, height), (26, 45, 68), -1)

        # Natural soil granular noise
        noise = np.random.randint(-6, 6, (height, width, 3), dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # 2. Render Weeds in the outer furrows
        for weed in weed_instances:
            sx = weed["x"] - cam_x + jitter_x
            sy = weed["y"] + jitter_y
            w_img, w_mask = weed["asset"]
            wh, ww = w_img.shape[:2]

            x1 = sx - ww // 2
            y1 = sy - wh // 2
            x2 = x1 + ww
            y2 = y1 + wh

            if x2 > 0 and x1 < width and y2 > 0 and y1 < height:
                src_x1 = max(0, -x1)
                src_y1 = max(0, -y1)
                src_x2 = ww - max(0, x2 - width)
                src_y2 = wh - max(0, y2 - height)

                dst_x1 = max(0, x1)
                dst_y1 = max(0, y1)
                dst_x2 = min(width, x2)
                dst_y2 = min(height, y2)

                if (dst_x2 > dst_x1) and (dst_y2 > dst_y1):
                    alpha = w_mask[src_y1:src_y2, src_x1:src_x2].astype(float) / 255.0
                    alpha = np.expand_dims(alpha, axis=-1)
                    roi = frame[dst_y1:dst_y2, dst_x1:dst_x2]
                    patch = w_img[src_y1:src_y2, src_x1:src_x2]
                    frame[dst_y1:dst_y2, dst_x1:dst_x2] = (patch * alpha + roi * (1.0 - alpha)).astype(np.uint8)

        # 3. Render Large, Prominent Macro Crop Leaves along Center
        for leaf in leaf_instances:
            sx = leaf["x"] - cam_x + jitter_x
            sy = leaf["y"] + jitter_y
            l_img, l_mask = leaf["asset"]
            lh, lw = l_img.shape[:2]

            x1 = sx - lw // 2
            y1 = sy - lh // 2
            x2 = x1 + lw
            y2 = y1 + lh

            if x2 > 0 and x1 < width and y2 > 0 and y1 < height:
                src_x1 = max(0, -x1)
                src_y1 = max(0, -y1)
                src_x2 = lw - max(0, x2 - width)
                src_y2 = lh - max(0, y2 - height)

                dst_x1 = max(0, x1)
                dst_y1 = max(0, y1)
                dst_x2 = min(width, x2)
                dst_y2 = min(height, y2)

                if (dst_x2 > dst_x1) and (dst_y2 > dst_y1):
                    alpha = l_mask[src_y1:src_y2, src_x1:src_x2].astype(float) / 255.0
                    alpha = np.expand_dims(alpha, axis=-1)
                    roi = frame[dst_y1:dst_y2, dst_x1:dst_x2]
                    patch = l_img[src_y1:src_y2, src_x1:src_x2]
                    frame[dst_y1:dst_y2, dst_x1:dst_x2] = (patch * alpha + roi * (1.0 - alpha)).astype(np.uint8)

        out.write(frame)

    out.release()
    print(f"Successfully generated macro foliar inspection video: {out_file} ({out_file.stat().st_size / (1024*1024):.2f} MB)")

    # Also update sample_video_for_upload.mp4 so the UI one-click Quick Load immediately uses this pristine video!
    sample_path = Path(r"d:\final_year_project\sample_video_for_upload.mp4")
    import shutil
    shutil.copyfile(str(out_file), str(sample_path))
    print(f"Updated {sample_path} with pristine 1080p macro video.")

if __name__ == "__main__":
    create_macro_leaf_video()

