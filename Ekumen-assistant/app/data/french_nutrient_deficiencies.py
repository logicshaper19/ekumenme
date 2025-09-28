"""
French Nutrient Deficiency Database
Comprehensive database of French agricultural nutrient deficiencies with symptoms and treatments.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DeficiencySeverity(Enum):
    """Deficiency severity levels."""
    LOW = "faible"
    MEDIUM = "modérée"
    HIGH = "élevée"
    CRITICAL = "critique"


class NutrientType(Enum):
    """Nutrient types."""
    MACRO = "macronutriment"
    MICRO = "micronutriment"
    SECONDARY = "nutriment_secondaire"


@dataclass
class DeficiencySymptom:
    """Nutrient deficiency symptom definition."""
    name: str
    description: str
    affected_organs: List[str]
    appearance_order: int  # Order in which symptoms appear


@dataclass
class FertilizerRecommendation:
    """Fertilizer recommendation."""
    name: str
    nutrient_content: str
    dosage: str
    application_timing: str
    application_method: str
    restrictions: List[str]
    effectiveness: float = 0.0  # 0-1 scale


@dataclass
class NutrientDeficiency:
    """Nutrient deficiency definition."""
    name: str
    nutrient_symbol: str
    nutrient_type: NutrientType
    crop_types: List[str]
    symptoms: List[DeficiencySymptom]
    fertilizers: List[FertilizerRecommendation]
    severity: DeficiencySeverity
    favorable_conditions: List[str]
    prevention_methods: List[str]
    economic_impact: str


class FrenchNutrientDeficiencyDatabase:
    """Database of French nutrient deficiencies."""
    
    def __init__(self):
        self.deficiencies = self._load_deficiency_database()
        self.symptom_keywords = self._build_symptom_keywords()
    
    def _load_deficiency_database(self) -> Dict[str, NutrientDeficiency]:
        """Load the comprehensive deficiency database."""
        deficiencies = {}
        
        # Nitrogen deficiency
        deficiencies["azote"] = NutrientDeficiency(
            name="Déficience en azote",
            nutrient_symbol="N",
            nutrient_type=NutrientType.MACRO,
            crop_types=["blé", "orge", "maïs", "colza", "tournesol"],
            symptoms=[
                DeficiencySymptom(
                    name="jaunissement_feuilles_anciennes",
                    description="Jaunissement des feuilles anciennes du bas vers le haut",
                    affected_organs=["feuilles"],
                    appearance_order=1
                ),
                DeficiencySymptom(
                    name="croissance_réduite",
                    description="Croissance réduite et plantes chétives",
                    affected_organs=["plantes"],
                    appearance_order=2
                ),
                DeficiencySymptom(
                    name="épis_petits",
                    description="Épis plus petits et moins denses",
                    affected_organs=["épis"],
                    appearance_order=3
                )
            ],
            fertilizers=[
                FertilizerRecommendation(
                    name="Urée 46",
                    nutrient_content="46% N",
                    dosage="200-300 kg/ha",
                    application_timing="Début de végétation",
                    application_method="Épandage au sol",
                    restrictions=["Éviter les pertes par volatilisation"],
                    effectiveness=0.90
                ),
                FertilizerRecommendation(
                    name="Ammonitrate 33.5",
                    nutrient_content="33.5% N",
                    dosage="250-350 kg/ha",
                    application_timing="Début de végétation",
                    application_method="Épandage au sol",
                    restrictions=["Éviter les pertes par lessivage"],
                    effectiveness=0.85
                )
            ],
            severity=DeficiencySeverity.HIGH,
            favorable_conditions=["sol pauvre en matière organique", "pluies abondantes", "température élevée"],
            prevention_methods=["apport de matière organique", "engrais verts", "rotation avec légumineuses"],
            economic_impact="Réduction de rendement de 20-50%"
        )
        
        # Phosphorus deficiency
        deficiencies["phosphore"] = NutrientDeficiency(
            name="Déficience en phosphore",
            nutrient_symbol="P",
            nutrient_type=NutrientType.MACRO,
            crop_types=["blé", "orge", "maïs", "colza", "tournesol"],
            symptoms=[
                DeficiencySymptom(
                    name="coloration_pourpre",
                    description="Coloration pourpre des feuilles et tiges",
                    affected_organs=["feuilles", "tiges"],
                    appearance_order=1
                ),
                DeficiencySymptom(
                    name="racines_peu_développées",
                    description="Système racinaire peu développé",
                    affected_organs=["racines"],
                    appearance_order=2
                ),
                DeficiencySymptom(
                    name="maturité_retardée",
                    description="Maturité retardée des cultures",
                    affected_organs=["plantes"],
                    appearance_order=3
                )
            ],
            fertilizers=[
                FertilizerRecommendation(
                    name="Superphosphate 18",
                    nutrient_content="18% P2O5",
                    dosage="200-300 kg/ha",
                    application_timing="Avant semis",
                    application_method="Incorporation au sol",
                    restrictions=["Éviter le contact avec les graines"],
                    effectiveness=0.80
                ),
                FertilizerRecommendation(
                    name="Phosphate d'ammonium",
                    nutrient_content="20% P2O5 + 18% N",
                    dosage="250-350 kg/ha",
                    application_timing="Avant semis",
                    application_method="Incorporation au sol",
                    restrictions=["Éviter le contact avec les graines"],
                    effectiveness=0.85
                )
            ],
            severity=DeficiencySeverity.HIGH,
            favorable_conditions=["sol acide", "température basse", "sol compacté"],
            prevention_methods=["chaulage", "travail du sol", "apport de phosphore"],
            economic_impact="Réduction de rendement de 15-40%"
        )
        
        # Potassium deficiency
        deficiencies["potassium"] = NutrientDeficiency(
            name="Déficience en potassium",
            nutrient_symbol="K",
            nutrient_type=NutrientType.MACRO,
            crop_types=["blé", "orge", "maïs", "colza", "tournesol"],
            symptoms=[
                DeficiencySymptom(
                    name="brûlure_marges_feuilles",
                    description="Brûlure des marges des feuilles anciennes",
                    affected_organs=["feuilles"],
                    appearance_order=1
                ),
                DeficiencySymptom(
                    name="feuilles_retombantes",
                    description="Feuilles retombantes et molles",
                    affected_organs=["feuilles"],
                    appearance_order=2
                ),
                DeficiencySymptom(
                    name="résistance_maladies_faible",
                    description="Résistance aux maladies réduite",
                    affected_organs=["plantes"],
                    appearance_order=3
                )
            ],
            fertilizers=[
                FertilizerRecommendation(
                    name="Chlorure de potassium",
                    nutrient_content="60% K2O",
                    dosage="150-250 kg/ha",
                    application_timing="Avant semis",
                    application_method="Épandage au sol",
                    restrictions=["Éviter sur cultures sensibles au chlore"],
                    effectiveness=0.90
                ),
                FertilizerRecommendation(
                    name="Sulfate de potassium",
                    nutrient_content="50% K2O",
                    dosage="200-300 kg/ha",
                    application_timing="Avant semis",
                    application_method="Épandage au sol",
                    restrictions=["Plus cher que le chlorure"],
                    effectiveness=0.85
                )
            ],
            severity=DeficiencySeverity.MEDIUM,
            favorable_conditions=["sol sableux", "pluies abondantes", "température élevée"],
            prevention_methods=["apport de potassium", "matière organique", "chaulage"],
            economic_impact="Réduction de rendement de 10-30%"
        )
        
        # Magnesium deficiency
        deficiencies["magnésium"] = NutrientDeficiency(
            name="Déficience en magnésium",
            nutrient_symbol="Mg",
            nutrient_type=NutrientType.SECONDARY,
            crop_types=["blé", "orge", "maïs", "colza", "tournesol"],
            symptoms=[
                DeficiencySymptom(
                    name="jaunissement_interveinal",
                    description="Jaunissement entre les nervures des feuilles",
                    affected_organs=["feuilles"],
                    appearance_order=1
                ),
                DeficiencySymptom(
                    name="feuilles_cassantes",
                    description="Feuilles cassantes et fragiles",
                    affected_organs=["feuilles"],
                    appearance_order=2
                )
            ],
            fertilizers=[
                FertilizerRecommendation(
                    name="Sulfate de magnésium",
                    nutrient_content="16% MgO",
                    dosage="100-200 kg/ha",
                    application_timing="Avant semis",
                    application_method="Épandage au sol",
                    restrictions=["Éviter le surdosage"],
                    effectiveness=0.80
                ),
                FertilizerRecommendation(
                    name="Kiesérite",
                    nutrient_content="27% MgO",
                    dosage="150-250 kg/ha",
                    application_timing="Avant semis",
                    application_method="Épandage au sol",
                    restrictions=["Éviter le surdosage"],
                    effectiveness=0.85
                )
            ],
            severity=DeficiencySeverity.MEDIUM,
            favorable_conditions=["sol acide", "apport excessif de potassium", "pluies abondantes"],
            prevention_methods=["chaulage magnésien", "équilibre K/Mg", "matière organique"],
            economic_impact="Réduction de rendement de 5-20%"
        )
        
        # Iron deficiency
        deficiencies["fer"] = NutrientDeficiency(
            name="Déficience en fer",
            nutrient_symbol="Fe",
            nutrient_type=NutrientType.MICRO,
            crop_types=["blé", "orge", "maïs", "colza", "tournesol"],
            symptoms=[
                DeficiencySymptom(
                    name="jaunissement_jeunes_feuilles",
                    description="Jaunissement des jeunes feuilles avec nervures vertes",
                    affected_organs=["feuilles"],
                    appearance_order=1
                ),
                DeficiencySymptom(
                    name="croissance_ralentie",
                    description="Croissance ralentie des jeunes pousses",
                    affected_organs=["pousses"],
                    appearance_order=2
                )
            ],
            fertilizers=[
                FertilizerRecommendation(
                    name="Chélate de fer",
                    nutrient_content="6% Fe",
                    dosage="2-5 kg/ha",
                    application_timing="Début de végétation",
                    application_method="Pulvérisation foliaire",
                    restrictions=["Coût élevé", "Efficacité limitée"],
                    effectiveness=0.70
                ),
                FertilizerRecommendation(
                    name="Sulfate de fer",
                    nutrient_content="20% Fe",
                    dosage="10-20 kg/ha",
                    application_timing="Avant semis",
                    application_method="Incorporation au sol",
                    restrictions=["Peu efficace en sol calcaire"],
                    effectiveness=0.50
                )
            ],
            severity=DeficiencySeverity.MEDIUM,
            favorable_conditions=["sol calcaire", "pH élevé", "excès de phosphore"],
            prevention_methods=["acidification du sol", "matière organique", "variétés tolérantes"],
            economic_impact="Réduction de rendement de 5-15%"
        )
        
        return deficiencies
    
    def _build_symptom_keywords(self) -> Dict[str, List[str]]:
        """Build keyword mapping for symptom recognition."""
        return {
            "jaunissement": ["jaunissement", "jaune", "jaunâtre", "jaunir"],
            "pourpre": ["pourpre", "violet", "violette", "violacé", "violacée"],
            "brûlure": ["brûlure", "brûlé", "brûlée", "brûler", "nécrose"],
            "retombant": ["retombant", "retombante", "mou", "molle", "flasque"],
            "cassant": ["cassant", "cassante", "fragile", "crispé", "crispée"],
            "interveinal": ["interveinal", "entre_les_nervures", "nervures_vertes"],
            "croissance": ["croissance", "développement", "taille", "hauteur"],
            "épis": ["épis", "épi", "grains", "grain", "rendement"]
        }
    
    def find_deficiencies_by_symptoms(self, crop_type: str, symptoms: List[str]) -> List[NutrientDeficiency]:
        """Find deficiencies based on crop type and symptoms."""
        matching_deficiencies = []
        
        for deficiency in self.deficiencies.values():
            if crop_type.lower() in [c.lower() for c in deficiency.crop_types]:
                # Check if symptoms match
                symptom_matches = 0
                for symptom in symptoms:
                    for deficiency_symptom in deficiency.symptoms:
                        if self._symptom_matches(symptom, deficiency_symptom):
                            symptom_matches += 1
                            break
                
                # If at least one symptom matches, include the deficiency
                if symptom_matches > 0:
                    matching_deficiencies.append(deficiency)
        
        # Sort by number of matching symptoms (descending)
        matching_deficiencies.sort(key=lambda d: self._count_symptom_matches(d, symptoms), reverse=True)
        return matching_deficiencies
    
    def _symptom_matches(self, user_symptom: str, deficiency_symptom: DeficiencySymptom) -> bool:
        """Check if user symptom matches deficiency symptom."""
        user_symptom_lower = user_symptom.lower()
        
        # Check symptom name
        if deficiency_symptom.name.lower() in user_symptom_lower:
            return True
        
        # Check description keywords
        for keyword in deficiency_symptom.description.lower().split():
            if keyword in user_symptom_lower:
                return True
        
        # Check keyword mapping
        for category, keywords in self.symptom_keywords.items():
            if any(keyword in user_symptom_lower for keyword in keywords):
                if category in deficiency_symptom.name.lower() or category in deficiency_symptom.description.lower():
                    return True
        
        return False
    
    def _count_symptom_matches(self, deficiency: NutrientDeficiency, symptoms: List[str]) -> int:
        """Count how many symptoms match a deficiency."""
        matches = 0
        for symptom in symptoms:
            for deficiency_symptom in deficiency.symptoms:
                if self._symptom_matches(symptom, deficiency_symptom):
                    matches += 1
                    break
        return matches
    
    def get_fertilizer_recommendations(self, deficiency_name: str) -> List[FertilizerRecommendation]:
        """Get fertilizer recommendations for a deficiency."""
        deficiency = self.deficiencies.get(deficiency_name.lower())
        if not deficiency:
            return []
        
        # Sort by effectiveness (descending)
        fertilizers = deficiency.fertilizers.copy()
        fertilizers.sort(key=lambda f: f.effectiveness, reverse=True)
        return fertilizers
    
    def assess_deficiency_severity(self, deficiency_name: str, symptoms: Dict[str, Any]) -> DeficiencySeverity:
        """Assess deficiency severity based on symptoms."""
        deficiency = self.deficiencies.get(deficiency_name.lower())
        if not deficiency:
            return DeficiencySeverity.LOW
        
        # This is a simplified assessment
        severity_score = 0
        
        for symptom_name, severity_value in symptoms.items():
            for deficiency_symptom in deficiency.symptoms:
                if symptom_name in deficiency_symptom.name:
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
            return DeficiencySeverity.CRITICAL
        elif severity_score >= 0.6:
            return DeficiencySeverity.HIGH
        elif severity_score >= 0.3:
            return DeficiencySeverity.MEDIUM
        else:
            return DeficiencySeverity.LOW
    
    def get_prevention_advice(self, deficiency_name: str) -> List[str]:
        """Get prevention advice for a deficiency."""
        deficiency = self.deficiencies.get(deficiency_name.lower())
        if not deficiency:
            return []
        return deficiency.prevention_methods


# Global instance
deficiency_db = FrenchNutrientDeficiencyDatabase()
