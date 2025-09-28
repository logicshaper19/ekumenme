"""
Get Safety Guidelines Tool - Single Purpose Tool

Job: Get safety guidelines for agricultural products and practices.
Input: product_type, practice_type, safety_level
Output: JSON string with safety guidelines

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
class SafetyGuideline:
    """Structured safety guideline."""
    guideline_type: str
    description: str
    safety_level: str
    required_equipment: List[str]
    safety_measures: List[str]
    emergency_procedures: List[str]

class GetSafetyGuidelinesTool(BaseTool):
    """
    Tool: Get safety guidelines for agricultural products and practices.
    
    Job: Take product and practice information to return safety guidelines.
    Input: product_type, practice_type, safety_level
    Output: JSON string with safety guidelines
    """
    
    name: str = "get_safety_guidelines_tool"
    description: str = "Récupère les consignes de sécurité pour les produits et pratiques agricoles"
    
    def _run(
        self,
        product_type: str = None,
        practice_type: str = None,
        safety_level: str = "standard",
        **kwargs
    ) -> str:
        """
        Get safety guidelines for agricultural products and practices.
        
        Args:
            product_type: Type of agricultural product (herbicide, insecticide, etc.)
            practice_type: Type of agricultural practice (spraying, fertilization, etc.)
            safety_level: Safety level required (basic, standard, high)
        """
        try:
            # Get safety guidelines database
            safety_database = self._get_safety_database()
            
            # Get relevant safety guidelines
            safety_guidelines = self._get_relevant_guidelines(product_type, practice_type, safety_level, safety_database)
            
            # Calculate safety priority
            safety_priority = self._calculate_safety_priority(safety_guidelines)
            
            # Generate safety recommendations
            safety_recommendations = self._generate_safety_recommendations(safety_guidelines)
            
            result = {
                "product_type": product_type,
                "practice_type": practice_type,
                "safety_level": safety_level,
                "safety_guidelines": [asdict(guideline) for guideline in safety_guidelines],
                "safety_priority": safety_priority,
                "safety_recommendations": safety_recommendations,
                "total_guidelines": len(safety_guidelines)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Get safety guidelines error: {e}")
            return json.dumps({"error": f"Erreur lors de la récupération des consignes de sécurité: {str(e)}"})
    
    def _get_safety_database(self) -> Dict[str, Any]:
        """Get safety guidelines database."""
        safety_database = {
            "herbicide": {
                "basic": {
                    "guideline_type": "herbicide_basic",
                    "description": "Consignes de sécurité de base pour les herbicides",
                    "safety_level": "basic",
                    "required_equipment": ["gants", "lunettes", "masque"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison"]
                },
                "standard": {
                    "guideline_type": "herbicide_standard",
                    "description": "Consignes de sécurité standard pour les herbicides",
                    "safety_level": "standard",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact", "ventilation"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison", "évacuer_zone"]
                },
                "high": {
                    "guideline_type": "herbicide_high",
                    "description": "Consignes de sécurité élevées pour les herbicides",
                    "safety_level": "high",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison", "bottes"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact", "ventilation", "isolation"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison", "évacuer_zone", "alerter_secours"]
                }
            },
            "insecticide": {
                "basic": {
                    "guideline_type": "insecticide_basic",
                    "description": "Consignes de sécurité de base pour les insecticides",
                    "safety_level": "basic",
                    "required_equipment": ["gants", "lunettes", "masque"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison"]
                },
                "standard": {
                    "guideline_type": "insecticide_standard",
                    "description": "Consignes de sécurité standard pour les insecticides",
                    "safety_level": "standard",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact", "ventilation"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison", "évacuer_zone"]
                },
                "high": {
                    "guideline_type": "insecticide_high",
                    "description": "Consignes de sécurité élevées pour les insecticides",
                    "safety_level": "high",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison", "bottes"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact", "ventilation", "isolation"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison", "évacuer_zone", "alerter_secours"]
                }
            },
            "fongicide": {
                "basic": {
                    "guideline_type": "fongicide_basic",
                    "description": "Consignes de sécurité de base pour les fongicides",
                    "safety_level": "basic",
                    "required_equipment": ["gants", "lunettes", "masque"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison"]
                },
                "standard": {
                    "guideline_type": "fongicide_standard",
                    "description": "Consignes de sécurité standard pour les fongicides",
                    "safety_level": "standard",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact", "ventilation"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison", "évacuer_zone"]
                },
                "high": {
                    "guideline_type": "fongicide_high",
                    "description": "Consignes de sécurité élevées pour les fongicides",
                    "safety_level": "high",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison", "bottes"],
                    "safety_measures": ["lire_étiquette", "respecter_doses", "éviter_contact", "ventilation", "isolation"],
                    "emergency_procedures": ["rincer_abondamment", "appeler_centre_antipoison", "évacuer_zone", "alerter_secours"]
                }
            },
            "spraying": {
                "basic": {
                    "guideline_type": "spraying_basic",
                    "description": "Consignes de sécurité de base pour la pulvérisation",
                    "safety_level": "basic",
                    "required_equipment": ["pulvérisateur", "gants", "lunettes"],
                    "safety_measures": ["vérifier_équipement", "respecter_doses", "éviter_dérive"],
                    "emergency_procedures": ["arrêter_pulvérisation", "rincer_équipement"]
                },
                "standard": {
                    "guideline_type": "spraying_standard",
                    "description": "Consignes de sécurité standard pour la pulvérisation",
                    "safety_level": "standard",
                    "required_equipment": ["pulvérisateur", "gants", "lunettes", "masque", "combinaison"],
                    "safety_measures": ["vérifier_équipement", "respecter_doses", "éviter_dérive", "ventilation"],
                    "emergency_procedures": ["arrêter_pulvérisation", "rincer_équipement", "évacuer_zone"]
                },
                "high": {
                    "guideline_type": "spraying_high",
                    "description": "Consignes de sécurité élevées pour la pulvérisation",
                    "safety_level": "high",
                    "required_equipment": ["pulvérisateur", "gants", "lunettes", "masque", "combinaison", "bottes"],
                    "safety_measures": ["vérifier_équipement", "respecter_doses", "éviter_dérive", "ventilation", "isolation"],
                    "emergency_procedures": ["arrêter_pulvérisation", "rincer_équipement", "évacuer_zone", "alerter_secours"]
                }
            }
        }
        
        return safety_database
    
    def _get_relevant_guidelines(self, product_type: str = None, practice_type: str = None, safety_level: str = "standard", safety_database: Dict[str, Any] = None) -> List[SafetyGuideline]:
        """Get relevant safety guidelines based on criteria."""
        guidelines = []
        
        # Get product-specific guidelines
        if product_type and product_type in safety_database:
            if safety_level in safety_database[product_type]:
                guideline_data = safety_database[product_type][safety_level]
                guideline = SafetyGuideline(
                    guideline_type=guideline_data["guideline_type"],
                    description=guideline_data["description"],
                    safety_level=guideline_data["safety_level"],
                    required_equipment=guideline_data["required_equipment"],
                    safety_measures=guideline_data["safety_measures"],
                    emergency_procedures=guideline_data["emergency_procedures"]
                )
                guidelines.append(guideline)
        
        # Get practice-specific guidelines
        if practice_type and practice_type in safety_database:
            if safety_level in safety_database[practice_type]:
                guideline_data = safety_database[practice_type][safety_level]
                guideline = SafetyGuideline(
                    guideline_type=guideline_data["guideline_type"],
                    description=guideline_data["description"],
                    safety_level=guideline_data["safety_level"],
                    required_equipment=guideline_data["required_equipment"],
                    safety_measures=guideline_data["safety_measures"],
                    emergency_procedures=guideline_data["emergency_procedures"]
                )
                guidelines.append(guideline)
        
        return guidelines
    
    def _calculate_safety_priority(self, safety_guidelines: List[SafetyGuideline]) -> str:
        """Calculate safety priority based on guidelines."""
        if not safety_guidelines:
            return "low"
        
        safety_levels = [guideline.safety_level for guideline in safety_guidelines]
        
        if "high" in safety_levels:
            return "high"
        elif "standard" in safety_levels:
            return "moderate"
        else:
            return "low"
    
    def _generate_safety_recommendations(self, safety_guidelines: List[SafetyGuideline]) -> List[str]:
        """Generate safety recommendations based on guidelines."""
        recommendations = []
        
        for guideline in safety_guidelines:
            recommendations.append(f"Consignes {guideline.safety_level}: {guideline.description}")
            recommendations.extend([f"Équipement requis: {equipment}" for equipment in guideline.required_equipment])
            recommendations.extend([f"Mesure de sécurité: {measure}" for measure in guideline.safety_measures])
        
        if not recommendations:
            recommendations.append("Aucune consigne de sécurité spécifique identifiée")
        
        return recommendations
