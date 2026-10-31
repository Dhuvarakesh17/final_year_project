"""
Agronomic Prescription & Treatment Advisory Engine
Translates diagnosed foliar pathogens, lesion damage, and weed pressure
into actionable chemical, biological, and cultural agronomic interventions.
"""
from typing import Dict, Any, List

ADVISORY_DATABASE: Dict[str, Dict[str, Any]] = {
    "Tomato_Early_blight": {
        "common_name": "Early Blight (Alternaria solani)",
        "urgency": "HIGH",
        "chemical_control": [
            {"treatment": "Chlorothalonil 75% WP", "dosage": "2.0 - 2.5 g/L", "spray_interval": "7 - 10 days"},
            {"treatment": "Mancozeb 75% WP", "dosage": "2.0 g/L", "spray_interval": "10 days"},
            {"treatment": "Azoxystrobin 23% SC", "dosage": "1.0 mL/L", "spray_interval": "14 days"}
        ],
        "biological_control": [
            {"treatment": "Bacillus subtilis (QST 713 strain)", "dosage": "3 - 5 mL/L", "mode": "Foliar colonization & antagonism"},
            {"treatment": "Trichoderma harzianum", "dosage": "5 g/L", "mode": "Root & canopy bio-shield"}
        ],
        "cultural_practices": [
            "Prune lower infected canopy foliage to restrict soil-splash spore transmission.",
            "Switch from overhead sprinkler to drip irrigation to prevent foliar wetness.",
            "Maintain 3-year crop rotation with non-Solanaceous crops."
        ],
        "spot_spray_cost_savings_pct": 52.0
    },
    "Tomato_Late_blight": {
        "common_name": "Late Blight (Phytophthora infestans)",
        "urgency": "CRITICAL",
        "chemical_control": [
            {"treatment": "Metalaxyl 8% + Mancozeb 64% WP", "dosage": "2.5 g/L", "spray_interval": "5 - 7 days"},
            {"treatment": "Dimethomorph 50% WP", "dosage": "1.5 g/L", "spray_interval": "7 days"},
            {"treatment": "Cymoxanil 8% + Mancozeb 64% WP", "dosage": "2.0 g/L", "spray_interval": "7 days"}
        ],
        "biological_control": [
            {"treatment": "Copper Hydroxide 53.8% DF (Organic certified)", "dosage": "2.0 g/L", "mode": "Surface spore preventative"},
            {"treatment": "Potassium Phosphite", "dosage": "3.0 mL/L", "mode": "Systemic acquired resistance (SAR) booster"}
        ],
        "cultural_practices": [
            "Immediate rogueing and destruction of heavily blighted host plants.",
            "Avoid field entry when foliage is damp to prevent mechanical spore dispersal.",
            "Ensure wide row spacing (minimum 75 cm) for cross-canopy airflow."
        ],
        "spot_spray_cost_savings_pct": 58.0
    },
    "Tomato_Bacterial_spot": {
        "common_name": "Bacterial Spot (Xanthomonas perforans)",
        "urgency": "HIGH",
        "chemical_control": [
            {"treatment": "Copper Oxychloride 50% WP + Streptomycin Sulphate (90:10)", "dosage": "2.5 g/L + 0.5 g/L", "spray_interval": "7 days"},
            {"treatment": "Kasugamycin 3% SL", "dosage": "1.5 mL/L", "spray_interval": "10 days"}
        ],
        "biological_control": [
            {"treatment": "Bacteriophage cocktail (AgriPhage)", "dosage": "1.0 - 2.0 L/ha", "mode": "Lytic pathogen bacterial lysis"},
            {"treatment": "Bacillus amyloliquefaciens", "dosage": "2.5 g/L", "mode": "Foliar colonization"}
        ],
        "cultural_practices": [
            "Use certified pathogen-free treated seed stocks.",
            "Eliminate volunteer solanaceous weeds along borders.",
            "Sterilize pruning shears with 10% sodium hypochlorite between rows."
        ],
        "spot_spray_cost_savings_pct": 45.0
    },
    "Tomato_Septoria_leaf_spot": {
        "common_name": "Septoria Leaf Spot (Septoria lycopersici)",
        "urgency": "HIGH",
        "chemical_control": [
            {"treatment": "Chlorothalonil 720 SC", "dosage": "2.0 mL/L", "spray_interval": "7 - 10 days"},
            {"treatment": "Propiconazole 25% EC", "dosage": "1.0 mL/L", "spray_interval": "14 days"}
        ],
        "biological_control": [
            {"treatment": "Copper Octanoate (Copper Soap)", "dosage": "5 mL/L", "mode": "Broad-spectrum contact fungicide"},
            {"treatment": "Neem seed kernel extract (NSKE 5%)", "dosage": "50 mL/L", "mode": "Foliar fungal spore suppressor"}
        ],
        "cultural_practices": [
            "Mulch field beds with black plastic or organic straw to stop rain-splash.",
            "Stake and trellis vines upright off the soil bed.",
            "Destroy all post-harvest crop debris."
        ],
        "spot_spray_cost_savings_pct": 48.0
    },
    "Tomato_Leaf_Mold": {
        "common_name": "Leaf Mold (Passalora fulva)",
        "urgency": "MODERATE",
        "chemical_control": [
            {"treatment": "Difenoconazole 25% EC", "dosage": "0.5 mL/L", "spray_interval": "10 days"},
            {"treatment": "Boscalid + Pyraclostrobin", "dosage": "1.2 g/L", "spray_interval": "12 days"}
        ],
        "biological_control": [
            {"treatment": "Aureobasidium pullulans", "dosage": "2.0 g/L", "mode": "Nutrient competition on foliar surface"},
            {"treatment": "Potassium Bicarbonate", "dosage": "3.0 g/L", "mode": "Foliar pH alteration against spore germination"}
        ],
        "cultural_practices": [
            "Maintain greenhouse/field relative humidity below 85%.",
            "Increase ventilation and vent open top tunnels during high dew periods."
        ],
        "spot_spray_cost_savings_pct": 40.0
    },
    "Tomato_Spider_mites_Two_spotted_spider_mite": {
        "common_name": "Two-Spotted Spider Mite (Tetranychus urticae)",
        "urgency": "HIGH",
        "chemical_control": [
            {"treatment": "Abamectin 1.9% EC", "dosage": "1.0 mL/L", "spray_interval": "7 days"},
            {"treatment": "Spiromesifen 22.9% SC", "dosage": "0.8 mL/L", "spray_interval": "14 days"}
        ],
        "biological_control": [
            {"treatment": "Phytoseiulus persimilis (Predatory Mites)", "dosage": "5 - 10 mites/m²", "mode": "Active biological predation"},
            {"treatment": "Beauveria bassiana (Entomopathogenic fungus)", "dosage": "2.0 g/L", "mode": "Arthropod infection"}
        ],
        "cultural_practices": [
            "Avoid water-stress; maintain adequate canopy misting/irrigation.",
            "Suppresses dust on field perimeter access roads."
        ],
        "spot_spray_cost_savings_pct": 60.0
    },
    "Tomato__Target_Spot": {
        "common_name": "Target Spot (Corynespora cassiicola)",
        "urgency": "HIGH",
        "chemical_control": [
            {"treatment": "Fluxapyroxad + Pyraclostrobin", "dosage": "0.8 mL/L", "spray_interval": "10 days"},
            {"treatment": "Famoxadone + Cymoxanil", "dosage": "1.5 g/L", "spray_interval": "10 days"}
        ],
        "biological_control": [
            {"treatment": "Bacillus subtilis", "dosage": "3 mL/L", "mode": "Bio-fungicidal spray"},
            {"treatment": "Copper sulfate pentahydrate", "dosage": "2.0 g/L", "mode": "Protective film"}
        ],
        "cultural_practices": [
            "De-leaf lower senescent canopy.",
            "Avoid planting downwind from infected cucurbit or legume fields."
        ],
        "spot_spray_cost_savings_pct": 46.0
    },
    "Tomato__Tomato_YellowLeaf__Curl_Virus": {
        "common_name": "Tomato Yellow Leaf Curl Virus (TYLCV)",
        "urgency": "CRITICAL",
        "chemical_control": [
            {"treatment": "Thiamethoxam 25% WG (Vector Whitefly control)", "dosage": "0.3 g/L", "spray_interval": "10 days"},
            {"treatment": "Pyriproxyfen 10% EC", "dosage": "1.0 mL/L", "spray_interval": "14 days"}
        ],
        "biological_control": [
            {"treatment": "Encarsia formosa (Parasitoid wasp)", "dosage": "2 - 3 wasps/m²", "mode": "Whitefly biological parasite"},
            {"treatment": "Yellow sticky cards / traps", "dosage": "20 traps/ha", "mode": "Vector monitoring & mass trapping"}
        ],
        "cultural_practices": [
            "Immediate removal and bagging of infected stunted plants to stop vector feeding.",
            "Install 50-mesh insect-proof netting over nursery beds.",
            "Implement a mandatory 60-day host-free period before Solanaceae planting."
        ],
        "spot_spray_cost_savings_pct": 65.0
    },
    "Tomato__Tomato_mosaic_virus": {
        "common_name": "Tomato Mosaic Virus (ToMV)",
        "urgency": "HIGH",
        "chemical_control": [
            {"treatment": "No direct virucide available", "dosage": "N/A", "spray_interval": "Focus on sanitation & vector barrier"}
        ],
        "biological_control": [
            {"treatment": "Chitosan (Bio-stimulant)", "dosage": "2.5 mL/L", "mode": "Induces plant systemic resistance against viral spread"},
            {"treatment": "Skim milk solution (20%)", "dosage": "200 mL/L", "mode": "Inactivates mechanical virus transfer during handling"}
        ],
        "cultural_practices": [
            "No tobacco use by workers inside field or packing areas.",
            "Wash hands thoroughly with soap or 3% trisodium phosphate before handling plants.",
            "Rogue and incinerate infected mosaic plants."
        ],
        "spot_spray_cost_savings_pct": 50.0
    },
    "Tomato_healthy": {
        "common_name": "Healthy Solanaceae Canopy (Nominal)",
        "urgency": "NONE",
        "chemical_control": [],
        "biological_control": [
            {"treatment": "Preventative seaweed extract (Ascophyllum nodosum)", "dosage": "2.0 mL/L", "mode": "Growth vigor & stress tolerance"}
        ],
        "cultural_practices": [
            "Continue scheduled regular weekly scouting.",
            "Maintain balanced N-P-K fertigation and soil pH between 6.0 - 6.8.",
            "Monitor perimeter for weed encroachments."
        ],
        "spot_spray_cost_savings_pct": 0.0
    },
    "Potato___Early_blight": {
        "common_name": "Potato Early Blight (Alternaria solani)",
        "urgency": "HIGH",
        "chemical_control": [
            {"treatment": "Mancozeb 75% WP", "dosage": "2.5 g/L", "spray_interval": "7 - 10 days"},
            {"treatment": "Difenoconazole 25% EC", "dosage": "0.5 mL/L", "spray_interval": "10 days"}
        ],
        "biological_control": [
            {"treatment": "Trichoderma viride", "dosage": "5 g/L", "mode": "Soil and foliar antagonist"}
        ],
        "cultural_practices": [
            "Ensure proper hill mounding to protect developing tubers from spore wash-down.",
            "Avoid nitrogen deficiency which accelerates foliar senescence."
        ],
        "spot_spray_cost_savings_pct": 49.0
    },
    "Potato___Late_blight": {
        "common_name": "Potato Late Blight (Phytophthora infestans)",
        "urgency": "CRITICAL",
        "chemical_control": [
            {"treatment": "Cymoxanil + Mancozeb", "dosage": "2.5 g/L", "spray_interval": "5 - 7 days"},
            {"treatment": "Fluopicolide + Propamocarb HCl", "dosage": "2.0 mL/L", "spray_interval": "7 days"}
        ],
        "biological_control": [
            {"treatment": "Copper Oxychloride 50% WP", "dosage": "2.5 g/L", "mode": "Surface spore preventative"}
        ],
        "cultural_practices": [
            "Burn or haul off cull potato piles.",
            "Kill vines 14 days prior to harvest to prevent tuber rot during digging."
        ],
        "spot_spray_cost_savings_pct": 55.0
    },
    "Potato___healthy": {
        "common_name": "Healthy Potato Canopy (Nominal)",
        "urgency": "NONE",
        "chemical_control": [],
        "biological_control": [],
        "cultural_practices": ["Standard agronomic scouting and moisture monitoring."],
        "spot_spray_cost_savings_pct": 0.0
    },
    "Pepper__bell___Bacterial_spot": {
        "common_name": "Bell Pepper Bacterial Spot (Xanthomonas)",
        "urgency": "HIGH",
        "chemical_control": [
            {"treatment": "Fixed copper + Mancozeb mix", "dosage": "2.0 g/L each", "spray_interval": "7 days"},
            {"treatment": "Kasugamycin 3% SL", "dosage": "1.5 mL/L", "spray_interval": "10 days"}
        ],
        "biological_control": [
            {"treatment": "Bacillus subtilis", "dosage": "3 mL/L", "mode": "Foliar barrier"}
        ],
        "cultural_practices": [
            "Avoid overhead irrigation; use drip lines.",
            "Sanitize trellising stakes and tools."
        ],
        "spot_spray_cost_savings_pct": 46.0
    },
    "Pepper__bell___healthy": {
        "common_name": "Healthy Bell Pepper (Nominal)",
        "urgency": "NONE",
        "chemical_control": [],
        "biological_control": [],
        "cultural_practices": ["Standard scouting and nutrient fertigation schedule."],
        "spot_spray_cost_savings_pct": 0.0
    }
}

class TreatmentAdvisoryEngine:
    @staticmethod
    def get_prescription(disease_name: str, lesion_pct: float = 0.0, health_score: float = 100.0) -> Dict[str, Any]:
        """
        Generates comprehensive treatment advisory for the diagnosed disease.
        """
        # Look up matching class
        advisory = ADVISORY_DATABASE.get(disease_name)
        if not advisory:
            # Fallback search by partial name
            for key, val in ADVISORY_DATABASE.items():
                if key.lower() in disease_name.lower() or disease_name.lower() in key.lower():
                    advisory = val
                    break

        if not advisory:
            advisory = {
                "common_name": disease_name.replace("_", " ").title(),
                "urgency": "MODERATE" if health_score < 70 else "LOW",
                "chemical_control": [{"treatment": "Broad-spectrum Protective Fungicide (Mancozeb)", "dosage": "2.0 g/L", "spray_interval": "10 days"}],
                "biological_control": [{"treatment": "Bacillus subtilis bio-fungicide", "dosage": "3 mL/L", "mode": "Foliar colonization"}],
                "cultural_practices": ["Prune damaged leaves", "Maintain balanced irrigation", "Sanitize tools between passes"],
                "spot_spray_cost_savings_pct": 40.0
            }

        # Dynamically scale savings & urgency based on measured lesion percentage
        urgency = advisory["urgency"]
        if lesion_pct > 25.0:
            urgency = "CRITICAL"
        elif lesion_pct > 10.0 and urgency != "CRITICAL":
            urgency = "HIGH"

        return {
            "disease_class": disease_name,
            "common_name": advisory["common_name"],
            "urgency": urgency,
            "lesion_severity_pct": round(lesion_pct, 2),
            "health_score": round(health_score, 1),
            "chemical_control": advisory.get("chemical_control", []),
            "biological_control": advisory.get("biological_control", []),
            "cultural_practices": advisory.get("cultural_practices", []),
            "spot_spray_cost_savings_pct": advisory.get("spot_spray_cost_savings_pct", 45.0)
        }

