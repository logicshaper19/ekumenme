"""
Diagnose Disease Tool - Single Purpose Tool

Job: Diagnose crop diseases from symptoms and conditions.
Input: crop_type, symptoms, environmental_conditions
Output: JSON string with disease diagnosis

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
class DiseaseDiagnosis:
    """Structured disease diagnosis."""
    disease_name: str
    confidence: float
    severity: str
    symptoms_matched: List[str]
    treatment_recommendations: List[str]
    prevention_measures: List[str]

class DiagnoseDiseaseTool(BaseTool):
    """
    Tool: Diagnose crop diseases from symptoms and conditions.
    
    Job: Take crop symptoms and environmental conditions to diagnose diseases.
    Input: crop_type, symptoms, environmental_conditions
    Output: JSON string with disease diagnosis
    """
    
    name: str = "diagnose_disease_tool"
    description: str = "Diagnostique les maladies des cultures à partir des symptômes"
    
    def _run(
        self,
        crop_type: str,
        symptoms: List[str],
        environmental_conditions: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        Diagnose crop diseases from symptoms and environmental conditions.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            symptoms: List of observed symptoms
            environmental_conditions: Environmental conditions (humidity, temperature, etc.)
        """
        try:
            # Get disease knowledge base
            disease_knowledge = self._get_disease_knowledge_base(crop_type)
            
            # Diagnose diseases
            diagnoses = self._diagnose_diseases(symptoms, disease_knowledge, environmental_conditions)
            
            # Calculate diagnosis confidence
            diagnosis_confidence = self._calculate_diagnosis_confidence(diagnoses)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(diagnoses)
            
            result = {
                "crop_type": crop_type,
                "symptoms_observed": symptoms,
                "environmental_conditions": environmental_conditions or {},
                "diagnoses": [asdict(diagnosis) for diagnosis in diagnoses],
                "diagnosis_confidence": diagnosis_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_diagnoses": len(diagnoses)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Diagnose disease error: {e}")
            return json.dumps({"error": f"Erreur lors du diagnostic: {str(e)}"})
    
    def _get_disease_knowledge_base(self, crop_type: str) -> Dict[str, Any]:
        """Get disease knowledge base for specific crop."""
        disease_knowledge = {
            "blé": {
                "rouille_jaune": {
                    "symptoms": ["taches_jaunes", "pustules_jaunes", "feuilles_jaunies"],
                    "conditions": {"humidity": "high", "temperature": "moderate"},
                    "severity": "moderate",
                    "treatment": ["fongicide_triazole", "rotation_cultures"],
                    "prevention": ["variétés_résistantes", "drainage_amélioré"]
                },
                "oïdium": {
                    "symptoms": ["poudre_blanche", "feuilles_blanches", "croissance_ralentie"],
                    "conditions": {"humidity": "high", "temperature": "cool"},
                    "severity": "moderate",
                    "treatment": ["fongicide_soufre", "aération"],
                    "prevention": ["espacement_plants", "irrigation_contrôlée"]
                },
                "septoriose": {
                    "symptoms": ["taches_brunes", "feuilles_brunies", "chute_feuilles"],
                    "conditions": {"humidity": "very_high", "temperature": "moderate"},
                    "severity": "high",
                    "treatment": ["fongicide_systémique", "défoliation"],
                    "prevention": ["rotation_cultures", "drainage"]
                }
            },
            "maïs": {
                "helminthosporiose": {
                    "symptoms": ["taches_brunes", "feuilles_brunies", "croissance_ralentie"],
                    "conditions": {"humidity": "high", "temperature": "warm"},
                    "severity": "moderate",
                    "treatment": ["fongicide_contact", "rotation_cultures"],
                    "prevention": ["variétés_résistantes", "drainage"]
                },
                "charbon": {
                    "symptoms": ["excroissances_noires", "grains_noirs", "croissance_anormale"],
                    "conditions": {"humidity": "high", "temperature": "warm"},
                    "severity": "high",
                    "treatment": ["fongicide_systémique", "destruction_plants"],
                    "prevention": ["traitement_semences", "rotation_cultures"]
                }
            },
            "colza": {
                "sclerotinia": {
                    "symptoms": ["taches_blanches", "pourriture_blanche", "chute_fleurs"],
                    "conditions": {"humidity": "very_high", "temperature": "moderate"},
                    "severity": "high",
                    "treatment": ["fongicide_systémique", "défoliation"],
                    "prevention": ["rotation_cultures", "drainage"]
                },
                "phoma": {
                    "symptoms": ["taches_noires", "feuilles_noires", "croissance_ralentie"],
                    "conditions": {"humidity": "high", "temperature": "cool"},
                    "severity": "moderate",
                    "treatment": ["fongicide_contact", "rotation_cultures"],
                    "prevention": ["variétés_résistantes", "drainage"]
                }
            }
        }
        
        return disease_knowledge.get(crop_type, {})
    
    def _diagnose_diseases(self, symptoms: List[str], disease_knowledge: Dict[str, Any], environmental_conditions: Dict[str, Any] = None) -> List[DiseaseDiagnosis]:
        """Diagnose diseases based on symptoms and conditions."""
        diagnoses = []
        
        for disease_name, disease_info in disease_knowledge.items():
            # Calculate symptom match
            symptom_matches = [symptom for symptom in symptoms if symptom in disease_info["symptoms"]]
            symptom_match_ratio = len(symptom_matches) / len(disease_info["symptoms"]) if disease_info["symptoms"] else 0
            
            # Calculate environmental match
            environmental_match = self._calculate_environmental_match(disease_info["conditions"], environmental_conditions or {})
            
            # Calculate overall confidence
            confidence = (symptom_match_ratio * 0.7 + environmental_match * 0.3)
            
            if confidence > 0.3:  # Only include diagnoses with reasonable confidence
                diagnosis = DiseaseDiagnosis(
                    disease_name=disease_name,
                    confidence=round(confidence, 2),
                    severity=disease_info["severity"],
                    symptoms_matched=symptom_matches,
                    treatment_recommendations=disease_info["treatment"],
                    prevention_measures=disease_info["prevention"]
                )
                diagnoses.append(diagnosis)
        
        # Sort by confidence
        diagnoses.sort(key=lambda x: x.confidence, reverse=True)
        
        return diagnoses
    
    def _calculate_environmental_match(self, disease_conditions: Dict[str, str], environmental_conditions: Dict[str, Any]) -> float:
        """Calculate environmental condition match."""
        if not environmental_conditions:
            return 0.5  # Neutral if no environmental data
        
        match_score = 0
        total_conditions = 0
        
        for condition, expected_value in disease_conditions.items():
            if condition in environmental_conditions:
                actual_value = environmental_conditions[condition]
                if self._condition_matches(expected_value, actual_value):
                    match_score += 1
                total_conditions += 1
        
        return match_score / total_conditions if total_conditions > 0 else 0.5
    
    def _condition_matches(self, expected: str, actual: Any) -> bool:
        """Check if environmental condition matches expected value."""
        if expected == "high" and actual > 70:
            return True
        elif expected == "moderate" and 40 <= actual <= 70:
            return True
        elif expected == "low" and actual < 40:
            return True
        elif expected == "very_high" and actual > 80:
            return True
        elif expected == "cool" and actual < 20:
            return True
        elif expected == "warm" and actual > 25:
            return True
        return False
    
    def _calculate_diagnosis_confidence(self, diagnoses: List[DiseaseDiagnosis]) -> str:
        """Calculate overall diagnosis confidence."""
        if not diagnoses:
            return "low"
        
        max_confidence = max(diagnosis.confidence for diagnosis in diagnoses)
        
        if max_confidence > 0.8:
            return "high"
        elif max_confidence > 0.6:
            return "moderate"
        else:
            return "low"
    
    def _generate_treatment_recommendations(self, diagnoses: List[DiseaseDiagnosis]) -> List[str]:
        """Generate treatment recommendations based on diagnoses."""
        recommendations = []
        
        if not diagnoses:
            recommendations.append("Aucune maladie identifiée - Surveillance continue recommandée")
            return recommendations
        
        # Get top diagnosis
        top_diagnosis = diagnoses[0]
        
        if top_diagnosis.confidence > 0.7:
            recommendations.append(f"Diagnostic principal: {top_diagnosis.disease_name} (confiance: {top_diagnosis.confidence:.0%})")
            recommendations.extend([f"Traitement: {treatment}" for treatment in top_diagnosis.treatment_recommendations])
            recommendations.extend([f"Prévention: {prevention}" for prevention in top_diagnosis.prevention_measures])
        else:
            recommendations.append("Diagnostic incertain - Consultation d'un expert recommandée")
            recommendations.append("Surveillance accrue des symptômes")
        
        return recommendations
