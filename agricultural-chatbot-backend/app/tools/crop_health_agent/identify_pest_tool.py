"""
Identify Pest Tool - Single Purpose Tool

Job: Identify crop pests from symptoms and damage patterns.
Input: crop_type, damage_symptoms, pest_indicators
Output: JSON string with pest identification

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
class PestIdentification:
    """Structured pest identification."""
    pest_name: str
    confidence: float
    severity: str
    damage_patterns: List[str]
    treatment_recommendations: List[str]
    prevention_measures: List[str]

class IdentifyPestTool(BaseTool):
    """
    Tool: Identify crop pests from symptoms and damage patterns.
    
    Job: Take crop damage symptoms and pest indicators to identify pests.
    Input: crop_type, damage_symptoms, pest_indicators
    Output: JSON string with pest identification
    """
    
    name: str = "identify_pest_tool"
    description: str = "Identifie les ravageurs des cultures à partir des symptômes de dégâts"
    
    def _run(
        self,
        crop_type: str,
        damage_symptoms: List[str],
        pest_indicators: List[str] = None,
        **kwargs
    ) -> str:
        """
        Identify crop pests from damage symptoms and pest indicators.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            damage_symptoms: List of observed damage symptoms
            pest_indicators: List of pest indicators (eggs, larvae, adults)
        """
        try:
            # Get pest knowledge base
            pest_knowledge = self._get_pest_knowledge_base(crop_type)
            
            # Identify pests
            pest_identifications = self._identify_pests(damage_symptoms, pest_indicators or [], pest_knowledge)
            
            # Calculate identification confidence
            identification_confidence = self._calculate_identification_confidence(pest_identifications)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(pest_identifications)
            
            result = {
                "crop_type": crop_type,
                "damage_symptoms": damage_symptoms,
                "pest_indicators": pest_indicators or [],
                "pest_identifications": [asdict(identification) for identification in pest_identifications],
                "identification_confidence": identification_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_identifications": len(pest_identifications)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Identify pest error: {e}")
            return json.dumps({"error": f"Erreur lors de l'identification des ravageurs: {str(e)}"})
    
    def _get_pest_knowledge_base(self, crop_type: str) -> Dict[str, Any]:
        """Get pest knowledge base for specific crop."""
        pest_knowledge = {
            "blé": {
                "puceron": {
                    "damage_patterns": ["feuilles_jaunies", "croissance_ralentie", "miellat"],
                    "pest_indicators": ["pucerons_verts", "pucerons_noirs", "fourmis"],
                    "severity": "moderate",
                    "treatment": ["insecticide_systémique", "coccinelles"],
                    "prevention": ["variétés_résistantes", "rotation_cultures"]
                },
                "cécidomyie": {
                    "damage_patterns": ["épis_vides", "grains_abîmés", "croissance_anormale"],
                    "pest_indicators": ["larves_blanches", "mouches_jaunes"],
                    "severity": "high",
                    "treatment": ["insecticide_contact", "pièges_phéromones"],
                    "prevention": ["traitement_semences", "rotation_cultures"]
                },
                "limace": {
                    "damage_patterns": ["feuilles_rongées", "trous_irréguliers", "traces_visqueuses"],
                    "pest_indicators": ["limaces", "traces_argentées"],
                    "severity": "moderate",
                    "treatment": ["anti-limaces", "pièges_bière"],
                    "prevention": ["drainage", "paillage"]
                }
            },
            "maïs": {
                "pyrale": {
                    "damage_patterns": ["trous_tiges", "épis_abîmés", "croissance_ralentie"],
                    "pest_indicators": ["chenilles", "papillons_bruns"],
                    "severity": "high",
                    "treatment": ["insecticide_systémique", "trichogrammes"],
                    "prevention": ["variétés_bt", "rotation_cultures"]
                },
                "taupin": {
                    "damage_patterns": ["racines_rongées", "plants_flétris", "croissance_ralentie"],
                    "pest_indicators": ["larves_jaunes", "adultes_noirs"],
                    "severity": "moderate",
                    "treatment": ["insecticide_sol", "nématodes"],
                    "prevention": ["traitement_semences", "rotation_cultures"]
                }
            },
            "colza": {
                "altise": {
                    "damage_patterns": ["feuilles_trouées", "croissance_ralentie", "plants_flétris"],
                    "pest_indicators": ["coléoptères_noirs", "larves_blanches"],
                    "severity": "moderate",
                    "treatment": ["insecticide_contact", "pièges_jaunes"],
                    "prevention": ["traitement_semences", "rotation_cultures"]
                },
                "charançon": {
                    "damage_patterns": ["boutons_flétris", "fleurs_abîmées", "croissance_anormale"],
                    "pest_indicators": ["charançons_bruns", "larves_blanches"],
                    "severity": "high",
                    "treatment": ["insecticide_systémique", "pièges_phéromones"],
                    "prevention": ["variétés_résistantes", "rotation_cultures"]
                }
            }
        }
        
        return pest_knowledge.get(crop_type, {})
    
    def _identify_pests(self, damage_symptoms: List[str], pest_indicators: List[str], pest_knowledge: Dict[str, Any]) -> List[PestIdentification]:
        """Identify pests based on damage symptoms and indicators."""
        identifications = []
        
        for pest_name, pest_info in pest_knowledge.items():
            # Calculate damage pattern match
            damage_matches = [symptom for symptom in damage_symptoms if symptom in pest_info["damage_patterns"]]
            damage_match_ratio = len(damage_matches) / len(pest_info["damage_patterns"]) if pest_info["damage_patterns"] else 0
            
            # Calculate pest indicator match
            indicator_matches = [indicator for indicator in pest_indicators if indicator in pest_info["pest_indicators"]]
            indicator_match_ratio = len(indicator_matches) / len(pest_info["pest_indicators"]) if pest_info["pest_indicators"] else 0
            
            # Calculate overall confidence
            confidence = (damage_match_ratio * 0.6 + indicator_match_ratio * 0.4)
            
            if confidence > 0.3:  # Only include identifications with reasonable confidence
                identification = PestIdentification(
                    pest_name=pest_name,
                    confidence=round(confidence, 2),
                    severity=pest_info["severity"],
                    damage_patterns=damage_matches,
                    treatment_recommendations=pest_info["treatment"],
                    prevention_measures=pest_info["prevention"]
                )
                identifications.append(identification)
        
        # Sort by confidence
        identifications.sort(key=lambda x: x.confidence, reverse=True)
        
        return identifications
    
    def _calculate_identification_confidence(self, identifications: List[PestIdentification]) -> str:
        """Calculate overall identification confidence."""
        if not identifications:
            return "low"
        
        max_confidence = max(identification.confidence for identification in identifications)
        
        if max_confidence > 0.8:
            return "high"
        elif max_confidence > 0.6:
            return "moderate"
        else:
            return "low"
    
    def _generate_treatment_recommendations(self, identifications: List[PestIdentification]) -> List[str]:
        """Generate treatment recommendations based on pest identifications."""
        recommendations = []
        
        if not identifications:
            recommendations.append("Aucun ravageur identifié - Surveillance continue recommandée")
            return recommendations
        
        # Get top identification
        top_identification = identifications[0]
        
        if top_identification.confidence > 0.7:
            recommendations.append(f"Ravageur principal: {top_identification.pest_name} (confiance: {top_identification.confidence:.0%})")
            recommendations.extend([f"Traitement: {treatment}" for treatment in top_identification.treatment_recommendations])
            recommendations.extend([f"Prévention: {prevention}" for prevention in top_identification.prevention_measures])
        else:
            recommendations.append("Identification incertaine - Consultation d'un expert recommandée")
            recommendations.append("Surveillance accrue des dégâts")
        
        return recommendations
