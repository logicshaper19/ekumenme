"""
French Crop Disease Database
Comprehensive database of French agricultural crop diseases with symptoms and treatments.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DiseaseSeverity(Enum):
    """Disease severity levels."""
    LOW = "faible"
    MEDIUM = "modérée"
    HIGH = "élevée"
    CRITICAL = "critique"


class GrowthStage(Enum):
    """Crop growth stages."""
    GERMINATION = "germination"
    LEAF_DEVELOPMENT = "développement_foliaire"
    TILLERING = "tallage"
    STEM_ELONGATION = "montaison"
    HEADING = "épiaison"
    FLOWERING = "floraison"
    GRAIN_FILLING = "remplissage"
    MATURITY = "maturité"


@dataclass
class DiseaseSymptom:
    """Disease symptom definition."""
    name: str
    description: str
    severity_indicator: str
    affected_organs: List[str]


@dataclass
class Treatment:
    """Treatment recommendation."""
    name: str
    active_ingredient: str
    dosage: str
    application_timing: str
    restrictions: List[str]
    amm_number: Optional[str] = None
    effectiveness: float = 0.0  # 0-1 scale


@dataclass
class CropDisease:
    """Crop disease definition."""
    name: str
    scientific_name: str
    crop_types: List[str]
    symptoms: List[DiseaseSymptom]
    treatments: List[Treatment]
    severity: DiseaseSeverity
    favorable_conditions: List[str]
    prevention_methods: List[str]
    economic_impact: str


class FrenchCropDiseaseDatabase:
    """Database of French crop diseases."""
    
    def __init__(self):
        self.diseases = self._load_disease_database()
        self.symptom_keywords = self._build_symptom_keywords()
    
    def _load_disease_database(self) -> Dict[str, CropDisease]:
        """Load the comprehensive disease database."""
        diseases = {}
        
        # Wheat diseases
        diseases["septoriose"] = CropDisease(
            name="Septoriose",
            scientific_name="Zymoseptoria tritici",
            crop_types=["blé", "triticale"],
            symptoms=[
                DiseaseSymptom(
                    name="taches_brunes",
                    description="Taches brunes ovales avec centre gris sur les feuilles",
                    severity_indicator="nombre_taches",
                    affected_organs=["feuilles", "gaines"]
                ),
                DiseaseSymptom(
                    name="dessèchement_feuilles",
                    description="Dessèchement progressif des feuilles du bas vers le haut",
                    severity_indicator="pourcentage_dessèchement",
                    affected_organs=["feuilles"]
                )
            ],
            treatments=[
                Treatment(
                    name="Prosaro",
                    active_ingredient="Prothioconazole + Tebuconazole",
                    dosage="1.0 L/ha",
                    application_timing="T1-T2 (montaison-épiaison)",
                    restrictions=["ZNT 5m", "Délai avant récolte: 35 jours"],
                    amm_number="2000300",
                    effectiveness=0.85
                ),
                Treatment(
                    name="Elatus Era",
                    active_ingredient="Azoxystrobine + Prothioconazole",
                    dosage="1.5 L/ha",
                    application_timing="T1-T2",
                    restrictions=["ZNT 5m", "Délai avant récolte: 35 jours"],
                    amm_number="2000301",
                    effectiveness=0.90
                )
            ],
            severity=DiseaseSeverity.HIGH,
            favorable_conditions=["humidité élevée", "température 15-25°C", "pluies fréquentes"],
            prevention_methods=["rotation des cultures", "variétés résistantes", "drainage"],
            economic_impact="Réduction de rendement de 10-30%"
        )
        
        diseases["oïdium"] = CropDisease(
            name="Oïdium",
            scientific_name="Blumeria graminis",
            crop_types=["blé", "orge", "triticale"],
            symptoms=[
                DiseaseSymptom(
                    name="poudre_blanche",
                    description="Poudre blanche sur les feuilles et tiges",
                    severity_indicator="pourcentage_couverture",
                    affected_organs=["feuilles", "tiges", "épis"]
                ),
                DiseaseSymptom(
                    name="décoloration_verte",
                    description="Décoloration vert-jaune des tissus affectés",
                    severity_indicator="intensité_décoloration",
                    affected_organs=["feuilles"]
                )
            ],
            treatments=[
                Treatment(
                    name="Swing Gold",
                    active_ingredient="Epoxiconazole + Kresoxim-méthyl",
                    dosage="1.0 L/ha",
                    application_timing="T1-T2",
                    restrictions=["ZNT 5m", "Délai avant récolte: 35 jours"],
                    amm_number="2000302",
                    effectiveness=0.80
                )
            ],
            severity=DiseaseSeverity.MEDIUM,
            favorable_conditions=["humidité modérée", "température 15-20°C", "vent faible"],
            prevention_methods=["variétés résistantes", "densité de semis adaptée"],
            economic_impact="Réduction de rendement de 5-15%"
        )
        
        diseases["rouille_jaune"] = CropDisease(
            name="Rouille jaune",
            scientific_name="Puccinia striiformis",
            crop_types=["blé", "orge"],
            symptoms=[
                DiseaseSymptom(
                    name="pustules_jaunes",
                    description="Pustules jaune-orange alignées sur les feuilles",
                    severity_indicator="nombre_pustules",
                    affected_organs=["feuilles", "gaines", "épis"]
                ),
                DiseaseSymptom(
                    name="décoloration_jaune",
                    description="Décoloration jaune autour des pustules",
                    severity_indicator="surface_affectée",
                    affected_organs=["feuilles"]
                )
            ],
            treatments=[
                Treatment(
                    name="Amistar Xtra",
                    active_ingredient="Azoxystrobine + Cyproconazole",
                    dosage="1.0 L/ha",
                    application_timing="T1-T2",
                    restrictions=["ZNT 5m", "Délai avant récolte: 35 jours"],
                    amm_number="2000303",
                    effectiveness=0.88
                )
            ],
            severity=DiseaseSeverity.HIGH,
            favorable_conditions=["température 10-15°C", "humidité élevée", "rosée"],
            prevention_methods=["variétés résistantes", "semis tardif"],
            economic_impact="Réduction de rendement de 15-40%"
        )
        
        # Corn diseases
        diseases["helminthosporiose"] = CropDisease(
            name="Helminthosporiose",
            scientific_name="Helminthosporium turcicum",
            crop_types=["maïs"],
            symptoms=[
                DiseaseSymptom(
                    name="taches_allongées",
                    description="Taches allongées gris-brun sur les feuilles",
                    severity_indicator="longueur_taches",
                    affected_organs=["feuilles"]
                ),
                DiseaseSymptom(
                    name="dessèchement_limbe",
                    description="Dessèchement du limbe foliaire",
                    severity_indicator="pourcentage_dessèchement",
                    affected_organs=["feuilles"]
                )
            ],
            treatments=[
                Treatment(
                    name="Tilt",
                    active_ingredient="Propiconazole",
                    dosage="0.5 L/ha",
                    application_timing="8-10 feuilles",
                    restrictions=["ZNT 5m", "Délai avant récolte: 30 jours"],
                    amm_number="2000304",
                    effectiveness=0.75
                )
            ],
            severity=DiseaseSeverity.MEDIUM,
            favorable_conditions=["humidité élevée", "température 20-30°C"],
            prevention_methods=["rotation", "résidus broyés", "variétés résistantes"],
            economic_impact="Réduction de rendement de 10-25%"
        )
        
        # Rapeseed diseases
        diseases["sclerotinia"] = CropDisease(
            name="Sclérotinia",
            scientific_name="Sclerotinia sclerotiorum",
            crop_types=["colza", "tournesol"],
            symptoms=[
                DiseaseSymptom(
                    name="pourriture_blanche",
                    description="Pourriture blanche cotonneuse sur tiges et siliques",
                    severity_indicator="nombre_foyers",
                    affected_organs=["tiges", "siliques", "feuilles"]
                ),
                DiseaseSymptom(
                    name="sclérotes_noirs",
                    description="Sclérotes noirs dans les tissus infectés",
                    severity_indicator="nombre_sclérotes",
                    affected_organs=["tiges", "racines"]
                )
            ],
            treatments=[
                Treatment(
                    name="Proline",
                    active_ingredient="Prothioconazole",
                    dosage="0.8 L/ha",
                    application_timing="Début floraison",
                    restrictions=["ZNT 5m", "Délai avant récolte: 35 jours"],
                    amm_number="2000305",
                    effectiveness=0.70
                )
            ],
            severity=DiseaseSeverity.HIGH,
            favorable_conditions=["humidité élevée", "température 15-25°C", "floraison"],
            prevention_methods=["rotation longue", "densité adaptée", "variétés résistantes"],
            economic_impact="Réduction de rendement de 20-50%"
        )
        
        return diseases
    
    def _build_symptom_keywords(self) -> Dict[str, List[str]]:
        """Build keyword mapping for symptom recognition."""
        return {
            "taches": ["taches", "tache", "macules", "macule", "tâches", "tâche"],
            "brunes": ["brunes", "brune", "marron", "brun", "brunâtre"],
            "jaunes": ["jaunes", "jaune", "jaunâtre", "jaunissement"],
            "blanches": ["blanches", "blanche", "blanchâtre", "blanchiment"],
            "poudre": ["poudre", "poudreux", "poudreuse", "farineux", "farineuse"],
            "pourriture": ["pourriture", "pourri", "pourrie", "décomposition"],
            "dessèchement": ["dessèchement", "desséché", "desséchée", "sécheresse"],
            "pustules": ["pustules", "pustule", "boutons", "bouton"],
            "décoloration": ["décoloration", "décoloré", "décolorée", "décolorer"],
            "taches_allongées": ["allongées", "allongé", "linéaires", "linéaire"],
            "sclérotes": ["sclérotes", "sclérote", "noirs", "noir", "noires", "noire"]
        }
    
    def find_diseases_by_symptoms(self, crop_type: str, symptoms: List[str]) -> List[CropDisease]:
        """Find diseases based on crop type and symptoms."""
        matching_diseases = []
        
        for disease in self.diseases.values():
            if crop_type.lower() in [c.lower() for c in disease.crop_types]:
                # Check if symptoms match
                symptom_matches = 0
                for symptom in symptoms:
                    for disease_symptom in disease.symptoms:
                        if self._symptom_matches(symptom, disease_symptom):
                            symptom_matches += 1
                            break
                
                # If at least one symptom matches, include the disease
                if symptom_matches > 0:
                    matching_diseases.append(disease)
        
        # Sort by number of matching symptoms (descending)
        matching_diseases.sort(key=lambda d: self._count_symptom_matches(d, symptoms), reverse=True)
        return matching_diseases
    
    def _symptom_matches(self, user_symptom: str, disease_symptom: DiseaseSymptom) -> bool:
        """Check if user symptom matches disease symptom."""
        user_symptom_lower = user_symptom.lower()
        
        # Check symptom name
        if disease_symptom.name.lower() in user_symptom_lower:
            return True
        
        # Check description keywords
        for keyword in disease_symptom.description.lower().split():
            if keyword in user_symptom_lower:
                return True
        
        # Check keyword mapping
        for category, keywords in self.symptom_keywords.items():
            if any(keyword in user_symptom_lower for keyword in keywords):
                if category in disease_symptom.name.lower() or category in disease_symptom.description.lower():
                    return True
        
        return False
    
    def _count_symptom_matches(self, disease: CropDisease, symptoms: List[str]) -> int:
        """Count how many symptoms match a disease."""
        matches = 0
        for symptom in symptoms:
            for disease_symptom in disease.symptoms:
                if self._symptom_matches(symptom, disease_symptom):
                    matches += 1
                    break
        return matches
    
    def get_treatment_recommendations(self, disease_name: str, crop_stage: GrowthStage) -> List[Treatment]:
        """Get treatment recommendations for a disease at specific growth stage."""
        disease = self.diseases.get(disease_name.lower())
        if not disease:
            return []
        
        # Filter treatments based on growth stage and effectiveness
        suitable_treatments = []
        for treatment in disease.treatments:
            # Check if treatment is suitable for current growth stage
            if self._is_treatment_suitable(treatment, crop_stage):
                suitable_treatments.append(treatment)
        
        # Sort by effectiveness (descending)
        suitable_treatments.sort(key=lambda t: t.effectiveness, reverse=True)
        return suitable_treatments
    
    def _is_treatment_suitable(self, treatment: Treatment, crop_stage: GrowthStage) -> bool:
        """Check if treatment is suitable for current growth stage."""
        # This is a simplified check - in reality, you'd have more complex logic
        stage_restrictions = {
            GrowthStage.GERMINATION: ["T1", "T2"],
            GrowthStage.LEAF_DEVELOPMENT: ["T1", "T2"],
            GrowthStage.TILLERING: ["T1", "T2"],
            GrowthStage.STEM_ELONGATION: ["T1", "T2"],
            GrowthStage.HEADING: ["T1", "T2"],
            GrowthStage.FLOWERING: ["T2"],
            GrowthStage.GRAIN_FILLING: [],
            GrowthStage.MATURITY: []
        }
        
        allowed_timings = stage_restrictions.get(crop_stage, [])
        return any(timing in treatment.application_timing for timing in allowed_timings)
    
    def assess_disease_severity(self, disease_name: str, symptoms: Dict[str, Any]) -> DiseaseSeverity:
        """Assess disease severity based on symptoms."""
        disease = self.diseases.get(disease_name.lower())
        if not disease:
            return DiseaseSeverity.LOW
        
        # This is a simplified assessment - in reality, you'd have more complex logic
        severity_score = 0
        
        for symptom_name, severity_value in symptoms.items():
            for disease_symptom in disease.symptoms:
                if symptom_name in disease_symptom.name:
                    # Convert severity value to score (simplified)
                    if isinstance(severity_value, (int, float)):
                        severity_score += min(severity_value / 100, 1.0)
                    elif isinstance(severity_value, str):
                        if "élevé" in severity_value.lower() or "fort" in severity_value.lower():
                            severity_score += 0.8
                        elif "modéré" in severity_value.lower():
                            severity_score += 0.5
                        else:
                            severity_score += 0.2
        
        # Determine severity level
        if severity_score >= 0.8:
            return DiseaseSeverity.CRITICAL
        elif severity_score >= 0.6:
            return DiseaseSeverity.HIGH
        elif severity_score >= 0.3:
            return DiseaseSeverity.MEDIUM
        else:
            return DiseaseSeverity.LOW
    
    def get_prevention_advice(self, disease_name: str) -> List[str]:
        """Get prevention advice for a disease."""
        disease = self.diseases.get(disease_name.lower())
        if not disease:
            return []
        return disease.prevention_methods
    
    def get_favorable_conditions(self, disease_name: str) -> List[str]:
        """Get favorable conditions for disease development."""
        disease = self.diseases.get(disease_name.lower())
        if not disease:
            return []
        return disease.favorable_conditions


# Global instance
disease_db = FrenchCropDiseaseDatabase()
