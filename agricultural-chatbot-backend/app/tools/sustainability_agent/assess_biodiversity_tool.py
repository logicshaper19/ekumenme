"""
Assess Biodiversity Tool - Single Purpose Tool

Job: Assess biodiversity impact and conservation potential of agricultural practices.
Input: practice_type, land_use, conservation_measures
Output: JSON string with biodiversity assessment

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
class BiodiversityImpact:
    """Structured biodiversity impact."""
    impact_type: str
    species_affected: str
    impact_level: str
    conservation_value: float
    mitigation_measures: List[str]

class AssessBiodiversityTool(BaseTool):
    """
    Tool: Assess biodiversity impact and conservation potential of agricultural practices.
    
    Job: Take agricultural practice data and assess biodiversity impact.
    Input: practice_type, land_use, conservation_measures
    Output: JSON string with biodiversity assessment
    """
    
    name: str = "assess_biodiversity_tool"
    description: str = "Évalue l'impact sur la biodiversité des pratiques agricoles"
    
    def _run(
        self,
        practice_type: str,
        land_use: str = None,
        conservation_measures: List[str] = None,
        **kwargs
    ) -> str:
        """
        Assess biodiversity impact and conservation potential of agricultural practices.
        
        Args:
            practice_type: Type of agricultural practice (spraying, fertilization, etc.)
            land_use: Type of land use (arable, grassland, forest, etc.)
            conservation_measures: List of conservation measures implemented
        """
        try:
            # Get biodiversity database
            biodiversity_database = self._get_biodiversity_database()
            
            # Assess biodiversity impacts
            biodiversity_impacts = self._assess_biodiversity_impacts(practice_type, land_use, conservation_measures or [], biodiversity_database)
            
            # Calculate biodiversity score
            biodiversity_score = self._calculate_biodiversity_score(biodiversity_impacts)
            
            # Generate conservation recommendations
            conservation_recommendations = self._generate_conservation_recommendations(biodiversity_impacts)
            
            result = {
                "practice_type": practice_type,
                "land_use": land_use,
                "conservation_measures": conservation_measures or [],
                "biodiversity_impacts": [asdict(impact) for impact in biodiversity_impacts],
                "biodiversity_score": biodiversity_score,
                "conservation_recommendations": conservation_recommendations,
                "total_impacts": len(biodiversity_impacts)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Assess biodiversity error: {e}")
            return json.dumps({"error": f"Erreur lors de l'évaluation de la biodiversité: {str(e)}"})
    
    def _get_biodiversity_database(self) -> Dict[str, Any]:
        """Get biodiversity database with impact assessments."""
        biodiversity_database = {
            "spraying": {
                "insects": {
                    "impact_level": "high",
                    "conservation_value": 0.8,
                    "mitigation_measures": ["éviter_floraison", "alternatives_biologiques", "bandes_enherbées"]
                },
                "birds": {
                    "impact_level": "moderate",
                    "conservation_value": 0.6,
                    "mitigation_measures": ["éviter_nidification", "haies", "zones_refuge"]
                },
                "soil_fauna": {
                    "impact_level": "moderate",
                    "conservation_value": 0.7,
                    "mitigation_measures": ["réduction_doses", "alternatives_biologiques", "rotation_cultures"]
                }
            },
            "fertilization": {
                "water_quality": {
                    "impact_level": "high",
                    "conservation_value": 0.9,
                    "mitigation_measures": ["plafond_azote", "bandes_enherbées", "rotation_légumineuses"]
                },
                "soil_health": {
                    "impact_level": "moderate",
                    "conservation_value": 0.8,
                    "mitigation_measures": ["apport_organique", "rotation_cultures", "couverture_sol"]
                },
                "aquatic_ecosystems": {
                    "impact_level": "high",
                    "conservation_value": 0.9,
                    "mitigation_measures": ["ZNT", "éviter_ruissellement", "traitement_eaux"]
                }
            },
            "irrigation": {
                "water_resources": {
                    "impact_level": "moderate",
                    "conservation_value": 0.7,
                    "mitigation_measures": ["efficacité_irrigation", "récupération_eau", "alternatives_sécheresse"]
                },
                "wetland_ecosystems": {
                    "impact_level": "moderate",
                    "conservation_value": 0.8,
                    "mitigation_measures": ["gestion_durable", "protection_zones", "restauration_écosystèmes"]
                }
            },
            "harvesting": {
                "wildlife": {
                    "impact_level": "moderate",
                    "conservation_value": 0.6,
                    "mitigation_measures": ["éviter_périodes_sensibles", "zones_refuge", "haies"]
                },
                "soil_structure": {
                    "impact_level": "moderate",
                    "conservation_value": 0.7,
                    "mitigation_measures": ["techniques_conservation", "rotation_cultures", "couverture_sol"]
                }
            }
        }
        
        return biodiversity_database
    
    def _assess_biodiversity_impacts(self, practice_type: str, land_use: str, conservation_measures: List[str], biodiversity_database: Dict[str, Any]) -> List[BiodiversityImpact]:
        """Assess biodiversity impacts for specific practice."""
        impacts = []
        
        if practice_type not in biodiversity_database:
            return impacts
        
        practice_impacts = biodiversity_database[practice_type]
        
        for impact_type, impact_data in practice_impacts.items():
            # Adjust impact level based on conservation measures
            adjusted_impact_level = self._adjust_impact_level(impact_data["impact_level"], conservation_measures)
            
            # Adjust conservation value based on land use
            adjusted_conservation_value = self._adjust_conservation_value(impact_data["conservation_value"], land_use)
            
            impact = BiodiversityImpact(
                impact_type=impact_type,
                species_affected=impact_type,
                impact_level=adjusted_impact_level,
                conservation_value=adjusted_conservation_value,
                mitigation_measures=impact_data["mitigation_measures"]
            )
            impacts.append(impact)
        
        return impacts
    
    def _adjust_impact_level(self, base_impact_level: str, conservation_measures: List[str]) -> str:
        """Adjust impact level based on conservation measures."""
        if not conservation_measures:
            return base_impact_level
        
        # Count relevant conservation measures
        relevant_measures = 0
        for measure in conservation_measures:
            if any(keyword in measure.lower() for keyword in ["biologique", "alternatives", "réduction", "rotation"]):
                relevant_measures += 1
        
        # Adjust impact level based on conservation measures
        if relevant_measures >= 3:
            if base_impact_level == "high":
                return "moderate"
            elif base_impact_level == "moderate":
                return "low"
        elif relevant_measures >= 1:
            if base_impact_level == "high":
                return "moderate"
        
        return base_impact_level
    
    def _adjust_conservation_value(self, base_conservation_value: float, land_use: str) -> float:
        """Adjust conservation value based on land use."""
        if not land_use:
            return base_conservation_value
        
        land_use_multipliers = {
            "arable": 1.0,
            "grassland": 1.2,
            "forest": 1.5,
            "wetland": 1.8,
            "organic": 1.3
        }
        
        multiplier = land_use_multipliers.get(land_use.lower(), 1.0)
        return min(base_conservation_value * multiplier, 1.0)
    
    def _calculate_biodiversity_score(self, biodiversity_impacts: List[BiodiversityImpact]) -> Dict[str, Any]:
        """Calculate overall biodiversity score."""
        if not biodiversity_impacts:
            return {"score": 0.0, "level": "unknown"}
        
        # Calculate weighted score based on conservation value and impact level
        total_score = 0.0
        total_weight = 0.0
        
        for impact in biodiversity_impacts:
            # Weight based on conservation value
            weight = impact.conservation_value
            
            # Score based on impact level (inverse)
            if impact.impact_level == "low":
                score = 0.8
            elif impact.impact_level == "moderate":
                score = 0.5
            else:  # high
                score = 0.2
            
            total_score += score * weight
            total_weight += weight
        
        average_score = total_score / total_weight if total_weight > 0 else 0.0
        
        # Determine biodiversity level
        if average_score > 0.7:
            level = "high"
        elif average_score > 0.4:
            level = "moderate"
        else:
            level = "low"
        
        return {
            "score": round(average_score, 2),
            "level": level
        }
    
    def _generate_conservation_recommendations(self, biodiversity_impacts: List[BiodiversityImpact]) -> List[str]:
        """Generate conservation recommendations based on biodiversity impacts."""
        recommendations = []
        
        # Sort impacts by conservation value (highest first)
        sorted_impacts = sorted(biodiversity_impacts, key=lambda x: x.conservation_value, reverse=True)
        
        for impact in sorted_impacts:
            if impact.conservation_value > 0.7:  # High conservation value
                if impact.impact_level == "high":
                    recommendations.append(f"🚨 Impact élevé sur {impact.impact_type} - Action urgente requise")
                    recommendations.extend([f"Mesure d'atténuation: {measure}" for measure in impact.mitigation_measures[:2]])
                elif impact.impact_level == "moderate":
                    recommendations.append(f"⚠️ Impact modéré sur {impact.impact_type} - Surveillance nécessaire")
                    recommendations.extend([f"Mesure d'amélioration: {measure}" for measure in impact.mitigation_measures[:1]])
        
        # General conservation recommendations
        recommendations.append("🌿 Implémenter des pratiques agroécologiques")
        recommendations.append("🦋 Créer des zones de refuge pour la biodiversité")
        recommendations.append("🌱 Diversifier les cultures et les variétés")
        recommendations.append("💧 Protéger les zones humides et les cours d'eau")
        
        return recommendations
