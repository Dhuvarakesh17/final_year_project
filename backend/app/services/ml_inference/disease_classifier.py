"""
Leaf Disease Classification Service
Uses EfficientNet-B0 with transfer learning on PlantVillage 15 classes.
Includes temperature scaling for calibrated softmax probabilities.
"""
import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from typing import Dict, Any, List, Tuple
from pathlib import Path

# 15 Classes from PlantVillage subset
PLANTVILLAGE_CLASSES = [
    "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Tomato_Bacterial_spot",
    "Tomato_Early_blight",
    "Tomato_Late_blight",
    "Tomato_Leaf_Mold",
    "Tomato_Septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite",
    "Tomato__Target_Spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus",
    "Tomato__Tomato_mosaic_virus",
    "Tomato_healthy",
]

class LeafDiseaseClassifier:
    def __init__(
        self,
        weights_path: str = r"d:\final_year_project\ml_models\weights\efficientnet_disease.pt",
        temperature: float = 1.15,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = torch.device(device)
        self.temperature = temperature
        
        meta_path = Path(weights_path).parent / "disease_classifier_metadata.json"
        if meta_path.exists():
            try:
                import json
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    self.temperature = float(meta.get("temperature_scaling", temperature))
                    print(f"Loaded calibrated temperature scaling parameter T = {self.temperature:.4f}")
            except Exception as e:
                print(f"Notice: using default temperature {temperature} ({e})")

        self.classes = PLANTVILLAGE_CLASSES
        self.num_classes = len(self.classes)
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        self.model = self._load_model(weights_path)

    def _load_model(self, weights_path: str) -> nn.Module:
        # Build EfficientNet-B0 architecture matching train_disease_classifier.py
        model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features, self.num_classes)
        )
        
        if os.path.exists(weights_path):
            try:
                state_dict = torch.load(weights_path, map_location=self.device)
                model.load_state_dict(state_dict)
                print(f"Loaded trained disease weights from {weights_path}")
            except Exception as e:
                print(f"Notice: Could not load weights ({e}). Operating with ImageNet pre-initialized backbone.")
        else:
            print(f"Weights file not found at {weights_path}. Initialized with transfer learning backbone.")

        model.to(self.device)
        model.eval()
        return model

    @torch.no_grad()
    def predict_leaf(self, pil_image: Image.Image) -> Dict[str, Any]:
        """
        Classifies leaf pathology and returns calibrated probabilities.
        """
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        
        # Apply temperature calibration
        calibrated_logits = logits / self.temperature
        probs = torch.softmax(calibrated_logits, dim=1).squeeze(0).cpu().numpy()

        top_indices = probs.argsort()[::-1]
        top_class_idx = top_indices[0]
        top_class_name = self.classes[top_class_idx]
        top_confidence = float(probs[top_class_idx])

        # Separate Crop Name from Condition
        parts = top_class_name.split("_")
        crop_name = parts[0]
        condition_name = "_".join(parts[1:]).replace("__", " ").strip("_")

        top_5 = [
            {"class": self.classes[idx], "probability": round(float(probs[idx]), 4)}
            for idx in top_indices[:5]
        ]

        return {
            "full_class": top_class_name,
            "crop_name": crop_name,
            "disease_name": condition_name,
            "confidence": round(top_confidence, 4),
            "is_healthy": "healthy" in top_class_name.lower(),
            "top_5": top_5,
        }

