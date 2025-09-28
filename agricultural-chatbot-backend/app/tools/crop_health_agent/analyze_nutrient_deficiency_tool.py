"""
Analyze Nutrient Deficiency Tool - Single Purpose Tool

Job: Analyze nutrient deficiencies from plant symptoms and soil conditions.
Input: crop_type, plant_symptoms, soil_conditions
Output: JSON string with nutrient deficiency analysis

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class NutrientDeficiency:
    """Structured nutrient deficiency analysis."""
    nutrient: str
    deficiency_level: str
    confidence: float
    symptoms_matched: List[str]
    soil_indicators: List[str]
    treatment_recommendations: List[str]
    prevention_measures: List[str]

class AnalyzeNutrientDeficiencyTool(BaseTool):
    """
    Tool: Analyze nutrient deficiencies from plant symptoms and soil conditions.
    
    Job: Take plant symptoms and soil conditions to analyze nutrient deficiencies.
    Input: crop_type, plant_symptoms, soil_conditions
    Output: JSON string with nutrient deficiency analysis
    """
    
    name: str = "analyze_nutrient_deficiency_tool"
    description: str = "Analyse les carences nutritionnelles à partir des symptômes des plantes"
    
    def _run(
        self,
        crop_type: str,
        plant_symptoms: List[str],
        soil_conditions: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        Analyze nutrient deficiencies from plant symptoms and soil conditions.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            plant_symptoms: List of observed plant symptoms
            soil_conditions: Soil conditions (pH, organic_matter, etc.)
        """
        try:
            # Get nutrient deficiency knowledge base
            deficiency_knowledge = self._get_deficiency_knowledge_base(crop_type)
            
            # Analyze nutrient deficiencies
            deficiencies = self._analyze_nutrient_deficiencies(plant_symptoms, soil_conditions or {}, deficiency_knowledge)
            
            # Calculate analysis confidence
            analysis_confidence = self._calculate_analysis_confidence(deficiencies)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(deficiencies)
            
            result = {
                "crop_type": crop_type,
                "plant_symptoms": plant_symptoms,
                "soil_conditions": soil_conditions or {},
                "nutrient_deficiencies": [asdict(deficiency) for deficiency in deficiencies],
                "analysis_confidence": analysis_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_deficiencies": len(deficiencies)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Analyze nutrient deficiency error: {e}")
            return json.dumps({"error": f"Erreur lors de l'analyse des carences: {str(e)}"})
    
    def _get_deficiency_knowledge_base(self, crop_type: str) -> Dict[str, Any]:
        """Get nutrient deficiency knowledge base for specific crop."""
        deficiency_knowledge = {
            "blé": {
                "azote": {
                    "symptoms": ["feuilles_jaunes", "croissance_ralentie", "épis_petits"],
                    "soil_indicators": ["azote_faible", "matière_organique_faible"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_azoté", "compost", "engrais_vert"],
                    "prevention": ["rotation_légumineuses", "apport_organique"]
                },
                "phosphore": {
                    "symptoms": ["feuilles_violettes", "racines_faibles", "croissance_ralentie"],
                    "soil_indicators": ["phosphore_faible", "ph_acide"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_phosphoré", "chaulage"],
                    "prevention": ["apport_phosphore", "correction_ph"]
                },
                "potassium": {
                    "symptoms": ["feuilles_brunies", "bords_brûlés", "résistance_faible"],
                    "soil_indicators": ["potassium_faible", "drainage_excessif"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_potassique", "compost"],
                    "prevention": ["apport_potassium", "amélioration_sol"]
                },
                "magnésium": {
                    "symptoms": ["feuilles_jaunes_veines_vertes", "croissance_ralentie"],
                    "soil_indicators": ["magnésium_faible", "ph_acide"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_magnésien", "chaulage"],
                    "prevention": ["apport_magnésium", "correction_ph"]
                }
            },
            "maïs": {
                "azote": {
                    "symptoms": ["feuilles_jaunes", "croissance_ralentie", "épis_petits"],
                    "soil_indicators": ["azote_faible", "matière_organique_faible"],
                    "deficiency_level": "high",
                    "treatment": ["engrais_azoté", "compost"],
                    "prevention": ["rotation_légumineuses", "apport_organique"]
                },
                "phosphore": {
                    "symptoms": ["feuilles_violettes", "racines_faibles", "croissance_ralentie"],
                    "soil_indicators": ["phosphore_faible", "ph_acide"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_phosphoré", "chaulage"],
                    "prevention": ["apport_phosphore", "correction_ph"]
                },
                "zinc": {
                    "symptoms": ["feuilles_blanches", "croissance_ralentie", "épis_petits"],
                    "soil_indicators": ["zinc_faible", "ph_alcalin"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_zinc", "correction_ph"],
                    "prevention": ["apport_zinc", "correction_ph"]
                }
            },
            "colza": {
                "azote": {
                    "symptoms": ["feuilles_jaunes", "croissance_ralentie", "fleurs_petites"],
                    "soil_indicators": ["azote_faible", "matière_organique_faible"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_azoté", "compost"],
                    "prevention": ["rotation_légumineuses", "apport_organique"]
                },
                "soufre": {
                    "symptoms": ["feuilles_jaunes", "croissance_ralentie", "fleurs_petites"],
                    "soil_indicators": ["soufre_faible", "drainage_excessif"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_soufré", "compost"],
                    "prevention": ["apport_soufre", "amélioration_sol"]
                },
                "bore": {
                    "symptoms": ["feuilles_épaisses", "croissance_anormale", "fleurs_abîmées"],
                    "soil_indicators": ["bore_faible", "ph_alcalin"],
                    "deficiency_level": "moderate",
                    "treatment": ["engrais_boré", "correction_ph"],
                    "prevention": ["apport_bore", "correction_ph"]
                }
            }
        }
        
        return deficiency_knowledge.get(crop_type, {})
    
    def _analyze_nutrient_deficiencies(self, plant_symptoms: List[str], soil_conditions: Dict[str, Any], deficiency_knowledge: Dict[str, Any]) -> List[NutrientDeficiency]:
        """Analyze nutrient deficiencies based on symptoms and soil conditions."""
        deficiencies = []
        
        for nutrient, nutrient_info in deficiency_knowledge.items():
            # Calculate symptom match
            symptom_matches = [symptom for symptom in plant_symptoms if symptom in nutrient_info["symptoms"]]
            symptom_match_ratio = len(symptom_matches) / len(nutrient_info["symptoms"]) if nutrient_info["symptoms"] else 0
            
            # Calculate soil indicator match
            soil_matches = [indicator for indicator in soil_conditions.keys() if indicator in nutrient_info["soil_indicators"]]
            soil_match_ratio = len(soil_matches) / len(nutrient_info["soil_indicators"]) if nutrient_info["soil_indicators"] else 0
            
            # Calculate overall confidence
            confidence = (symptom_match_ratio * 0.7 + soil_match_ratio * 0.3)
            
            if confidence > 0.3:  # Only include deficiencies with reasonable confidence
                deficiency = NutrientDeficiency(
                    nutrient=nutrient,
                    deficiency_level=nutrient_info["deficiency_level"],
                    confidence=round(confidence, 2),
                    symptoms_matched=symptom_matches,
                    soil_indicators=soil_matches,
                    treatment_recommendations=nutrient_info["treatment"],
                    prevention_measures=nutrient_info["prevention"]
                )
                deficiencies.append(deficiency)
        
        # Sort by confidence
        deficiencies.sort(key=lambda x: x.confidence, reverse=True)
        
        return deficiencies
    
    def _calculate_analysis_confidence(self, deficiencies: List[NutrientDeficiency]) -> str:
        """Calculate overall analysis confidence."""
        if not deficiencies:
            return "low"
        
        max_confidence = max(deficiency.confidence for deficiency in deficiencies)
        
        if max_confidence > 0.8:
            return "high"
        elif max_confidence > 0.6:
            return "moderate"
        else:
            return "low"
    
    def _generate_treatment_recommendations(self, deficiencies: List[NutrientDeficiency]) -> List[str]:
        """Generate treatment recommendations based on nutrient deficiencies."""
        recommendations = []
        
        if not deficiencies:
            recommendations.append("Aucune carence nutritionnelle identifiée - Surveillance continue recommandée")
            return recommendations
        
        # Get top deficiency
        top_deficiency = deficiencies[0]
        
        if top_deficiency.confidence > 0.7:
            recommendations.append(f"Carence principale: {top_deficiency.nutrient} (confiance: {top_deficiency.confidence:.0%})")
            recommendations.extend([f"Traitement: {treatment}" for treatment in top_deficiency.treatment_recommendations])
            recommendations.extend([f"Prévention: {prevention}" for prevention in top_deficiency.prevention_measures])
        else:
            recommendations.append("Analyse incertaine - Analyse de sol recommandée")
            recommendations.append("Surveillance accrue des symptômes")
        
        return recommendations
