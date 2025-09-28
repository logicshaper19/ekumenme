"""
French Crop Pest Database
Comprehensive database of French agricultural crop pests with identification and treatments.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PestSeverity(Enum):
    """Pest severity levels."""
    LOW = "faible"
    MEDIUM = "modérée"
    HIGH = "élevée"
    CRITICAL = "critique"


class PestStage(Enum):
    """Pest development stages."""
    EGG = "œuf"
    LARVA = "larve"
    NYMPH = "nymphe"
    ADULT = "adulte"


@dataclass
class PestSymptom:
    """Pest damage symptom definition."""
    name: str
    description: str
    affected_organs: List[str]
    damage_type: str


@dataclass
class PestTreatment:
    """Pest treatment recommendation."""
    name: str
    active_ingredient: str
    dosage: str
    application_timing: str
    target_stages: List[PestStage]
    restrictions: List[str]
    amm_number: Optional[str] = None
    effectiveness: float = 0.0  # 0-1 scale


@dataclass
class CropPest:
    """Crop pest definition."""
    name: str
    scientific_name: str
    crop_types: List[str]
    symptoms: List[PestSymptom]
    treatments: List[PestTreatment]
    severity: PestSeverity
    lifecycle: Dict[str, str]
    threshold_levels: Dict[str, str]
    favorable_conditions: List[str]
    prevention_methods: List[str]
    economic_impact: str


class FrenchCropPestDatabase:
    """Database of French crop pests."""
    
    def __init__(self):
        self.pests = self._load_pest_database()
        self.symptom_keywords = self._build_symptom_keywords()
    
    def _load_pest_database(self) -> Dict[str, CropPest]:
        """Load the comprehensive pest database."""
        pests = {}
        
        # Wheat pests
        pests["puceron_vert"] = CropPest(
            name="Puceron vert du blé",
            scientific_name="Sitobion avenae",
            crop_types=["blé", "orge", "triticale"],
            symptoms=[
                PestSymptom(
                    name="décoloration_feuilles",
                    description="Décoloration jaune-rouge des feuilles",
                    affected_organs=["feuilles", "épis"],
                    damage_type="piqure_succeuse"
                ),
                PestSymptom(
                    name="miellat",
                    description="Miellat collant sur les feuilles",
                    affected_organs=["feuilles", "épis"],
                    damage_type="excrétion"
                ),
                PestSymptom(
                    name="fumagine",
                    description="Champignon noir sur le miellat",
                    affected_organs=["feuilles", "épis"],
                    damage_type="secondaire"
                )
            ],
            treatments=[
                PestTreatment(
                    name="Karate Zeon",
                    active_ingredient="Lambda-cyhalothrine",
                    dosage="0.15 L/ha",
                    application_timing="Seuil dépassé",
                    target_stages=[PestStage.ADULT, PestStage.NYMPH],
                    restrictions=["ZNT 5m", "Délai avant récolte: 21 jours"],
                    amm_number="2000306",
                    effectiveness=0.90
                ),
                PestTreatment(
                    name="Decis Protech",
                    active_ingredient="Deltaméthrine",
                    dosage="0.3 L/ha",
                    application_timing="Seuil dépassé",
                    target_stages=[PestStage.ADULT, PestStage.NYMPH],
                    restrictions=["ZNT 5m", "Délai avant récolte: 21 jours"],
                    amm_number="2000307",
                    effectiveness=0.85
                )
            ],
            severity=PestSeverity.HIGH,
            lifecycle={
                "hiver": "Œufs sur graminées",
                "printemps": "Colonisation des céréales",
                "été": "Reproduction asexuée",
                "automne": "Retour sur graminées"
            },
            threshold_levels={
                "tallage": "5-10 pucerons/plante",
                "montaison": "10-20 pucerons/plante",
                "épiaison": "5-10 pucerons/épi"
            },
            favorable_conditions=["température 15-25°C", "humidité modérée", "vent faible"],
            prevention_methods=["auxiliaires naturels", "variétés résistantes", "semis tardif"],
            economic_impact="Réduction de rendement de 10-30%"
        )
        
        pests["cécidomyie"] = CropPest(
            name="Cécidomyie du blé",
            scientific_name="Contarinia tritici",
            crop_types=["blé", "triticale"],
            symptoms=[
                PestSymptom(
                    name="épis_vides",
                    description="Épis partiellement ou totalement vides",
                    affected_organs=["épis"],
                    damage_type="alimentation_larvaire"
                ),
                PestSymptom(
                    name="déformation_épis",
                    description="Déformation des épis",
                    affected_organs=["épis"],
                    damage_type="alimentation_larvaire"
                )
            ],
            treatments=[
                PestTreatment(
                    name="Karate Zeon",
                    active_ingredient="Lambda-cyhalothrine",
                    dosage="0.15 L/ha",
                    application_timing="Vol des adultes",
                    target_stages=[PestStage.ADULT],
                    restrictions=["ZNT 5m", "Délai avant récolte: 21 jours"],
                    amm_number="2000306",
                    effectiveness=0.80
                )
            ],
            severity=PestSeverity.HIGH,
            lifecycle={
                "hiver": "Larves dans le sol",
                "printemps": "Émergence des adultes",
                "été": "Ponte dans les épis",
                "automne": "Développement larvaire"
            },
            threshold_levels={
                "épiaison": "1-2 adultes/épi"
            },
            favorable_conditions=["température 15-20°C", "humidité élevée", "vent faible"],
            prevention_methods=["travail du sol", "rotation", "variétés résistantes"],
            economic_impact="Réduction de rendement de 20-50%"
        )
        
        # Corn pests
        pests["pyrale_mais"] = CropPest(
            name="Pyrale du maïs",
            scientific_name="Ostrinia nubilalis",
            crop_types=["maïs"],
            symptoms=[
                PestSymptom(
                    name="galeries_tiges",
                    description="Galeries dans les tiges",
                    affected_organs=["tiges"],
                    damage_type="alimentation_larvaire"
                ),
                PestSymptom(
                    name="cassure_tiges",
                    description="Cassure des tiges au niveau des galeries",
                    affected_organs=["tiges"],
                    damage_type="affaiblissement"
                ),
                PestSymptom(
                    name="déformation_épis",
                    description="Déformation des épis",
                    affected_organs=["épis"],
                    damage_type="alimentation_larvaire"
                )
            ],
            treatments=[
                PestTreatment(
                    name="Dipel",
                    active_ingredient="Bacillus thuringiensis",
                    dosage="1.0 kg/ha",
                    application_timing="Vol des papillons",
                    target_stages=[PestStage.LARVA],
                    restrictions=["Délai avant récolte: 0 jour"],
                    amm_number="2000308",
                    effectiveness=0.75
                ),
                PestTreatment(
                    name="Karate Zeon",
                    active_ingredient="Lambda-cyhalothrine",
                    dosage="0.15 L/ha",
                    application_timing="Vol des papillons",
                    target_stages=[PestStage.ADULT],
                    restrictions=["ZNT 5m", "Délai avant récolte: 21 jours"],
                    amm_number="2000306",
                    effectiveness=0.85
                )
            ],
            severity=PestSeverity.HIGH,
            lifecycle={
                "hiver": "Larves dans les tiges",
                "printemps": "Nymphose",
                "été": "Vol des papillons et ponte",
                "automne": "Développement larvaire"
            },
            threshold_levels={
                "floraison": "5-10 papillons/parcelle"
            },
            favorable_conditions=["température 20-30°C", "humidité modérée"],
            prevention_methods=["Bacillus thuringiensis", "travail du sol", "rotation"],
            economic_impact="Réduction de rendement de 15-40%"
        )
        
        # Rapeseed pests
        pests["altise"] = CropPest(
            name="Altise d'hiver",
            scientific_name="Psylliodes chrysocephala",
            crop_types=["colza"],
            symptoms=[
                PestSymptom(
                    name="trous_feuilles",
                    description="Petits trous ronds dans les feuilles",
                    affected_organs=["feuilles"],
                    damage_type="alimentation_adultes"
                ),
                PestSymptom(
                    name="galeries_pétioles",
                    description="Galeries dans les pétioles",
                    affected_organs=["pétioles"],
                    damage_type="alimentation_larvaire"
                ),
                PestSymptom(
                    name="dessèchement_plantes",
                    description="Dessèchement des jeunes plantes",
                    affected_organs=["plantes"],
                    damage_type="affaiblissement"
                )
            ],
            treatments=[
                PestTreatment(
                    name="Decis Protech",
                    active_ingredient="Deltaméthrine",
                    dosage="0.3 L/ha",
                    application_timing="Seuil dépassé",
                    target_stages=[PestStage.ADULT, PestStage.LARVA],
                    restrictions=["ZNT 5m", "Délai avant récolte: 21 jours"],
                    amm_number="2000307",
                    effectiveness=0.80
                )
            ],
            severity=PestSeverity.MEDIUM,
            lifecycle={
                "hiver": "Adultes dans le sol",
                "printemps": "Reproduction et ponte",
                "été": "Développement larvaire",
                "automne": "Colonisation des jeunes plantes"
            },
            threshold_levels={
                "levée": "2-3 adultes/plante",
                "hiver": "5-10 adultes/plante"
            },
            favorable_conditions=["température 10-20°C", "humidité modérée"],
            prevention_methods=["semis précoce", "densité adaptée", "variétés résistantes"],
            economic_impact="Réduction de rendement de 5-20%"
        )
        
        return pests
    
    def _build_symptom_keywords(self) -> Dict[str, List[str]]:
        """Build keyword mapping for symptom recognition."""
        return {
            "trous": ["trous", "trou", "perforations", "perforation", "trouées", "trouée"],
            "galeries": ["galeries", "galerie", "tunnels", "tunnel", "minages", "minage"],
            "décoloration": ["décoloration", "décoloré", "décolorée", "décolorer"],
            "miellat": ["miellat", "collant", "collante", "sucré", "sucrée"],
            "fumagine": ["fumagine", "noir", "noire", "champignon", "moisissure"],
            "cassure": ["cassure", "cassé", "cassée", "casser", "brisé", "brisée"],
            "déformation": ["déformation", "déformé", "déformée", "déformer"],
            "dessèchement": ["dessèchement", "desséché", "desséchée", "dessécher"],
            "épis_vides": ["vides", "vide", "stériles", "stérile", "sans_grains"],
            "piqure": ["piqure", "piqûre", "piqué", "piquée", "succion"]
        }
    
    def find_pests_by_symptoms(self, crop_type: str, symptoms: List[str]) -> List[CropPest]:
        """Find pests based on crop type and symptoms."""
        matching_pests = []
        
        for pest in self.pests.values():
            if crop_type.lower() in [c.lower() for c in pest.crop_types]:
                # Check if symptoms match
                symptom_matches = 0
                for symptom in symptoms:
                    for pest_symptom in pest.symptoms:
                        if self._symptom_matches(symptom, pest_symptom):
                            symptom_matches += 1
                            break
                
                # If at least one symptom matches, include the pest
                if symptom_matches > 0:
                    matching_pests.append(pest)
        
        # Sort by number of matching symptoms (descending)
        matching_pests.sort(key=lambda p: self._count_symptom_matches(p, symptoms), reverse=True)
        return matching_pests
    
    def _symptom_matches(self, user_symptom: str, pest_symptom: PestSymptom) -> bool:
        """Check if user symptom matches pest symptom."""
        user_symptom_lower = user_symptom.lower()
        
        # Check symptom name
        if pest_symptom.name.lower() in user_symptom_lower:
            return True
        
        # Check description keywords
        for keyword in pest_symptom.description.lower().split():
            if keyword in user_symptom_lower:
                return True
        
        # Check keyword mapping
        for category, keywords in self.symptom_keywords.items():
            if any(keyword in user_symptom_lower for keyword in keywords):
                if category in pest_symptom.name.lower() or category in pest_symptom.description.lower():
                    return True
        
        return False
    
    def _count_symptom_matches(self, pest: CropPest, symptoms: List[str]) -> int:
        """Count how many symptoms match a pest."""
        matches = 0
        for symptom in symptoms:
            for pest_symptom in pest.symptoms:
                if self._symptom_matches(symptom, pest_symptom):
                    matches += 1
                    break
        return matches
    
    def get_treatment_recommendations(self, pest_name: str, crop_stage: str) -> List[PestTreatment]:
        """Get treatment recommendations for a pest at specific crop stage."""
        pest = self.pests.get(pest_name.lower())
        if not pest:
            return []
        
        # Filter treatments based on effectiveness
        suitable_treatments = pest.treatments.copy()
        
        # Sort by effectiveness (descending)
        suitable_treatments.sort(key=lambda t: t.effectiveness, reverse=True)
        return suitable_treatments
    
    def assess_pest_severity(self, pest_name: str, population_level: str) -> PestSeverity:
        """Assess pest severity based on population level."""
        pest = self.pests.get(pest_name.lower())
        if not pest:
            return PestSeverity.LOW
        
        # This is a simplified assessment
        if "élevé" in population_level.lower() or "fort" in population_level.lower():
            return PestSeverity.HIGH
        elif "modéré" in population_level.lower():
            return PestSeverity.MEDIUM
        else:
            return PestSeverity.LOW
    
    def get_threshold_levels(self, pest_name: str) -> Dict[str, str]:
        """Get threshold levels for a pest."""
        pest = self.pests.get(pest_name.lower())
        if not pest:
            return {}
        return pest.threshold_levels
    
    def get_prevention_advice(self, pest_name: str) -> List[str]:
        """Get prevention advice for a pest."""
        pest = self.pests.get(pest_name.lower())
        if not pest:
            return []
        return pest.prevention_methods


# Global instance
pest_db = FrenchCropPestDatabase()
