"""
Foliar Lesion Spot Localization & Segmentation Service
Computes pixel-exact lesion area percentage:
    Lesion Area % = (Lesion Pixels / Leaf Pixels) * 100
Generates visual evidence: original leaf crop, binary lesion mask, and highlighted contour overlay.
"""
import os
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple
from pathlib import Path

class FoliarLesionSegmenter:
    def __init__(self, output_evidence_dir: str = r"d:\final_year_project\data\evidence"):
        self.output_dir = Path(output_evidence_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def segment_lesions(
        self,
        bgr_leaf_crop: np.ndarray,
        sample_id: str,
        save_artifacts: bool = True
    ) -> Dict[str, Any]:
        """
        Segments foliar lesions, calculates affected area percentage,
        and saves traceable evidence artifacts.
        """
        h, w = bgr_leaf_crop.shape[:2]
        total_pixels = h * w
        if total_pixels == 0:
            return {
                "lesion_area_pct": 0.0,
                "leaf_pixel_count": 0,
                "lesion_pixel_count": 0,
                "mask_overlay_path": None,
                "crop_image_path": None,
            }

        # 1. Isolate the Leaf Foliage from background
        hsv = cv2.cvtColor(bgr_leaf_crop, cv2.COLOR_BGR2HSV)
        
        # Broad foliage mask (greens, yellows, browns of crop leaves)
        # Excludes black/white background borders
        gray = cv2.cvtColor(bgr_leaf_crop, cv2.COLOR_BGR2GRAY)
        _, bg_mask = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
        
        # Clean morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        leaf_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_CLOSE, kernel)
        leaf_pixels = int(np.count_nonzero(leaf_mask))

        if leaf_pixels < 100:
            leaf_pixels = total_pixels
            leaf_mask = np.ones((h, w), dtype=np.uint8) * 255

        # 2. Segment Pathological Lesions (Necrosis, chlorosis, fungal spotting)
        # Necrotic tissue: brown, dark spots, yellow halos
        # Healthy green foliage: Hue 35 to 85, Saturation > 40
        healthy_green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
        
        # Lesion candidates are foliar pixels that deviate from healthy green
        lesion_candidates = cv2.bitwise_and(leaf_mask, cv2.bitwise_not(healthy_green_mask))
        
        # Further filter out pure white glare or shadow edges
        v_channel = hsv[:, :, 2]
        valid_tones = cv2.inRange(v_channel, 20, 240)
        lesion_mask = cv2.bitwise_and(lesion_candidates, valid_tones)
        
        # Remove small speckle noise
        lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_OPEN, kernel)
        lesion_pixels = int(np.count_nonzero(lesion_mask))

        # Calculate affected percentage
        lesion_area_pct = (lesion_pixels / float(leaf_pixels)) * 100.0
        lesion_area_pct = min(100.0, max(0.0, lesion_area_pct))

        # 3. Generate Highlighted Visual Evidence Overlay
        crop_path = None
        overlay_path = None

        if save_artifacts:
            # Save original leaf crop
            crop_path = str(self.output_dir / f"leaf_{sample_id}_crop.jpg")
            cv2.imwrite(crop_path, bgr_leaf_crop, [cv2.IMWRITE_JPEG_QUALITY, 95])

            # Create highlighted overlay: translucent red on lesions with bright yellow contours
            overlay = bgr_leaf_crop.copy()
            overlay[lesion_mask > 0] = [0, 0, 230]  # Red highlight
            highlighted = cv2.addWeighted(bgr_leaf_crop, 0.65, overlay, 0.35, 0)
            
            # Draw contours around lesions
            contours, _ = cv2.findContours(lesion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(highlighted, contours, -1, (0, 235, 255), 1)  # Yellow border

            overlay_path = str(self.output_dir / f"leaf_{sample_id}_lesion_mask.jpg")
            cv2.imwrite(overlay_path, highlighted, [cv2.IMWRITE_JPEG_QUALITY, 95])

        return {
            "lesion_area_pct": round(lesion_area_pct, 2),
            "leaf_pixel_count": leaf_pixels,
            "lesion_pixel_count": lesion_pixels,
            "crop_image_path": crop_path,
            "mask_overlay_path": overlay_path,
        }

