"""
Explainable AI (XAI) Service: Grad-CAM Implementation for EfficientNet-B0
Computes Gradient-weighted Class Activation Mapping to visualize foliar disease attention.
"""
import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
from typing import Tuple, Dict, Any, Optional
from pathlib import Path

class GradCAMExplainer:
    def __init__(self, model: torch.nn.Module, target_layer: Optional[torch.nn.Module] = None, device: Optional[torch.device] = None):
        self.model = model
        self.device = device or next(model.parameters()).device
        self.model.eval()

        # Target the last convolutional block in EfficientNet-B0 (model.features[-1])
        if target_layer is None:
            if hasattr(model, 'features'):
                self.target_layer = model.features[-1]
            else:
                # Fallback to last child in features
                self.target_layer = list(model.children())[0][-1]
        else:
            self.target_layer = target_layer

        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, input_tensor: torch.Tensor, class_idx: Optional[int] = None) -> np.ndarray:
        """
        Generates 2D heatmap [0, 1] for the specified class index.
        """
        input_tensor = input_tensor.to(self.device)
        if input_tensor.dim() == 3:
            input_tensor = input_tensor.unsqueeze(0)

        input_tensor.requires_grad = True
        self.model.zero_grad()

        logits = self.model(input_tensor)

        if class_idx is None:
            class_idx = int(torch.argmax(logits, dim=1).item())

        score = logits[0, class_idx]
        score.backward()

        # Global average pooling of gradients across spatial dimensions
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        # Weighted combination of forward activation maps
        cam = torch.sum(weights * self.activations, dim=1).squeeze(0)
        # Apply ReLU to retain only features that have a positive influence on the class
        cam = F.relu(cam)

        cam_np = cam.cpu().numpy()
        # Normalize between 0 and 1
        cam_min, cam_max = cam_np.min(), cam_np.max()
        if cam_max - cam_min > 1e-8:
            cam_np = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            cam_np = np.zeros_like(cam_np)

        return cam_np

    def overlay_heatmap(
        self,
        original_bgr: np.ndarray,
        heatmap: np.ndarray,
        colormap: int = cv2.COLORMAP_JET,
        alpha: float = 0.55
    ) -> np.ndarray:
        """
        Resizes heatmap to match original image dimensions and blends with colormap.
        """
        h, w = original_bgr.shape[:2]
        heatmap_resized = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_CUBIC)
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        colored_heatmap = cv2.applyColorMap(heatmap_uint8, colormap)

        overlay = cv2.addWeighted(colored_heatmap, alpha, original_bgr, 1 - alpha, 0)
        return overlay

