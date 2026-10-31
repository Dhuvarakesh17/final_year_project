"""
Realistic Agricultural Video Generator
Uses actual empirical image assets from PlantVillage (Tomato Early Blight, Late Blight, Healthy)
and DeepWeeds to construct a camera panning footage of an agricultural crop row.
"""
import os
import cv2
import numpy as np
from pathlib import Path

def create_realistic_field_video(
    output_path: str = r"d:\final_year_project\data\raw_videos\field_crop_drone_inspection.mp4",
    duration_sec: int = 8,
    fps: int = 30,
    width: int = 1280,
    height: int = 720
):
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Fetch real PlantVillage images
    pv_dir = Path(r"d:\final_year_project\data\datasets\leaf_disease\processed\train")
    early_blight_dir = pv_dir / "Tomato_Early_blight"
    late_blight_dir = pv_dir / "Tomato_Late_blight"
    healthy_dir = pv_dir / "Tomato_healthy"

    def get_sample_images(folder: Path, count: int = 4):
        if not folder.exists():
            return []
        files = [f for f in folder.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
        return [cv2.imread(str(f)) for f in files[:count] if cv2.imread(str(f)) is not None]

    blight_imgs = get_sample_images(early_blight_dir, 3) + get_sample_images(late_blight_dir, 2)
    healthy_imgs = get_sample_images(healthy_dir, 3)

    # 2. Fetch real DeepWeeds images
    dw_dir = Path(r"d:\final_year_project\data\datasets\deepweeds\images")
    weed_imgs = []
    if dw_dir.exists():
        weed_files = [f for f in dw_dir.iterdir() if f.suffix.lower() in [".jpg", ".png"]][:5]
        weed_imgs = [cv2.imread(str(f)) for f in weed_files if cv2.imread(str(f)) is not None]

    # Pre-resize leaf images with soft alpha-masking (circular/foliage boundary)
    def prepare_asset(img, target_size=(220, 220)):
        resized = cv2.resize(img, target_size)
        # Create circular/oval soft mask
        mask = np.zeros((target_size[1], target_size[0]), dtype=np.uint8)
        cv2.ellipse(mask, (target_size[0]//2, target_size[1]//2), (target_size[0]//2 - 10, target_size[1]//2 - 10), 0, 0, 360, 255, -1)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        return resized, mask

    all_crops = []
    for img in blight_imgs + healthy_imgs:
        all_crops.append(prepare_asset(img, (220, 220)))

    all_weeds = []
    for img in weed_imgs:
        all_weeds.append(prepare_asset(img, (180, 180)))

    # If no images found, create fallbacks
    if not all_crops:
        fallback = np.full((220, 220, 3), (35, 160, 45), dtype=np.uint8)
        all_crops.append(prepare_asset(fallback))
    if not all_weeds:
        fallback = np.full((180, 180, 3), (40, 180, 120), dtype=np.uint8)
        all_weeds.append(prepare_asset(fallback))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
    total_frames = duration_sec * fps

    print(f"Synthesizing realistic agricultural drone footage: {total_frames} frames ({duration_sec}s @ {fps}fps)...")

    # Camera pans forward across an 8-meter virtual field bed
    # We define positions along the virtual track
    virtual_length = 3500  # pixels
    
    # Place crops along the central ridge
    crop_instances = []
    for i in range(8):
        x_pos = 200 + i * 400 + np.random.randint(-40, 40)
        y_pos = height // 2 + np.random.randint(-50, 50)
        crop_instances.append({
            "virtual_x": x_pos,
            "y": y_pos,
            "asset": all_crops[i % len(all_crops)]
        })

    # Place weeds randomly along the furrows (edges)
    weed_instances = []
    for i in range(5):
        x_pos = 350 + i * 650 + np.random.randint(-50, 50)
        y_pos = 130 if i % 2 == 0 else height - 160
        weed_instances.append({
            "virtual_x": x_pos,
            "y": y_pos,
            "asset": all_weeds[i % len(all_weeds)]
        })

    for f_idx in range(total_frames):
        # Camera advances forward along the virtual track
        t = f_idx / float(total_frames)
        cam_x = int(t * (virtual_length - width))
        
        # Subtle handheld / drone jitter
        jitter_x = int(np.sin(f_idx * 0.15) * 4)
        jitter_y = int(np.cos(f_idx * 0.12) * 5)

        # 1. Base Soil & Mulch Canvas (rich warm agricultural soil)
        frame = np.full((height, width, 3), (30, 55, 80), dtype=np.uint8)
        
        # Soil furrow gradients (darker shadows in irrigation furrows)
        cv2.rectangle(frame, (0, 0), (width, 160), (22, 42, 65), -1)
        cv2.rectangle(frame, (0, height - 160), (width, height), (22, 42, 65), -1)

        # Organic soil texture noise
        noise = np.random.randint(-8, 8, (height, width, 3), dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # 2. Render Crops that fall within current camera viewport
        for crop in crop_instances:
            screen_x = crop["virtual_x"] - cam_x + jitter_x
            screen_y = crop["y"] + jitter_y
            
            # Check if within visible bounds
            c_img, c_mask = crop["asset"]
            ch, cw = c_img.shape[:2]
            
            x1 = screen_x - cw // 2
            y1 = screen_y - ch // 2
            x2 = x1 + cw
            y2 = y1 + ch

            if x2 > 0 and x1 < width and y2 > 0 and y1 < height:
                # Calculate clipping
                src_x1 = max(0, -x1)
                src_y1 = max(0, -y1)
                src_x2 = cw - max(0, x2 - width)
                src_y2 = ch - max(0, y2 - height)

                dst_x1 = max(0, x1)
                dst_y1 = max(0, y1)
                dst_x2 = min(width, x2)
                dst_y2 = min(height, y2)

                if (dst_x2 > dst_x1) and (dst_y2 > dst_y1):
                    alpha_sub = c_mask[src_y1:src_y2, src_x1:src_x2].astype(float) / 255.0
                    alpha_sub = np.expand_dims(alpha_sub, axis=-1)
                    roi = frame[dst_y1:dst_y2, dst_x1:dst_x2]
                    patch = c_img[src_y1:src_y2, src_x1:src_x2]
                    blended = (patch * alpha_sub + roi * (1.0 - alpha_sub)).astype(np.uint8)
                    frame[dst_y1:dst_y2, dst_x1:dst_x2] = blended

        # 3. Render Invasive Weeds
        for weed in weed_instances:
            screen_x = weed["virtual_x"] - cam_x + jitter_x
            screen_y = weed["y"] + jitter_y

            w_img, w_mask = weed["asset"]
            wh, ww = w_img.shape[:2]

            x1 = screen_x - ww // 2
            y1 = screen_y - wh // 2
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
                    alpha_sub = w_mask[src_y1:src_y2, src_x1:src_x2].astype(float) / 255.0
                    alpha_sub = np.expand_dims(alpha_sub, axis=-1)
                    roi = frame[dst_y1:dst_y2, dst_x1:dst_x2]
                    patch = w_img[src_y1:src_y2, src_x1:src_x2]
                    blended = (patch * alpha_sub + roi * (1.0 - alpha_sub)).astype(np.uint8)
                    frame[dst_y1:dst_y2, dst_x1:dst_x2] = blended

        out.write(frame)

    out.release()
    print(f"Video synthesis complete: {output_path}")

    # Copy to project root for easy user access
    root_copy = Path(r"d:\final_year_project\sample_video_for_upload.mp4")
    import shutil
    shutil.copy2(output_path, root_copy)
    print(f"Easy-access upload copy created at: {root_copy}")

if __name__ == "__main__":
    create_realistic_field_video()

