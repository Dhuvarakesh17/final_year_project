"""
Crop Health Assessment Engine
Implements deterministic, agronomic scoring of leaf health.
Decouples model classification confidence from biological tissue damage percentage.
"""
from typing import Dict, Any, Tuple

class CropHealthEngine:
    # Pathogen virulence weighting factors (based on agronomic impact on photosynthetic capacity)
    PATHOGEN_VIRULENCE: Dict[str, float] = {
        # High virulence / systemic damage
        "Tomato_Late_blight": 1.25,
        "Potato___Late_blight": 1.25,
        "Tomato__Tomato_YellowLeaf__Curl_Virus": 1.20,
        "Tomato__Tomato_mosaic_virus": 1.15,
        "Tomato_Bacterial_spot": 1.10,
        "Pepper__bell___Bacterial_spot": 1.10,
        
        # Moderate foliar damage
        "Tomato_Early_blight": 1.00,
        "Potato___Early_blight": 1.00,
        "Tomato_Septoria_leaf_spot": 0.95,
        "Tomato__Target_Spot": 0.95,
        "Tomato_Spider_mites_Two_spotted_spider_mite": 0.90,
        "Tomato_Leaf_Mold": 0.85,
        
        # Healthy references
        "Tomato_healthy": 0.0,
        "Potato___healthy": 0.0,
        "Pepper__bell___healthy": 0.0,
    }

    @classmethod
    def evaluate_leaf_health(
        cls,
        disease_name: str,
        classification_confidence: float,
        lesion_area_pct: float
    ) -> Dict[str, Any]:
        """
        Calculates health score and categorization.
        
        Args:
            disease_name: Classified class label (e.g. "Tomato_Early_blight")
            classification_confidence: Softmax probability (0.0 to 1.0)
            lesion_area_pct: Percentage of leaf area covered by lesions (0.0 to 100.0)
        
        Returns:
            Dictionary with health_score, severity_category, and agronomic recommendations.
        """
        is_healthy = "healthy" in disease_name.lower()
        
        if is_healthy or lesion_area_pct <= 2.0:
            severity = "healthy"
            health_score = 100.0 if is_healthy else max(90.0, 100.0 - lesion_area_pct)
            recommendation = "No chemical intervention needed. Maintain routine irrigation and nutrient monitoring."
        elif lesion_area_pct <= 10.0:
            severity = "mild"
            weight = cls.PATHOGEN_VIRULENCE.get(disease_name, 1.0)
            health_score = max(70.0, 100.0 - (lesion_area_pct * weight * 2.0))
            recommendation = "Preventive organic spray or bio-fungicide recommended. Monitor field progression closely."
        elif lesion_area_pct <= 25.0:
            severity = "moderate"
            weight = cls.PATHOGEN_VIRULENCE.get(disease_name, 1.0)
            health_score = max(50.0, 100.0 - (lesion_area_pct * weight * 2.2))
            recommendation = "Targeted therapeutic spray required. Check neighboring plants for localized spread."
        elif lesion_area_pct <= 50.0:
            severity = "severe"
            weight = cls.PATHOGEN_VIRULENCE.get(disease_name, 1.0)
            health_score = max(30.0, 100.0 - (lesion_area_pct * weight * 1.5))
            recommendation = "Immediate chemical application required. Prune severely infected lower canopy foliage."
        else:
            severity = "critical"
            health_score = max(0.0, 30.0 - (lesion_area_pct - 50.0) * 0.6)
            recommendation = "Critical damage. Rogueing (removal and destruction) of infected plants advised to stop epidemic spread."

        return {
            "disease_name": disease_name,
            "classification_confidence": round(classification_confidence, 4),
            "lesion_area_pct": round(lesion_area_pct, 2),
            "severity_category": severity,
            "health_score": round(health_score, 1),
            "recommendation": recommendation,
        }

