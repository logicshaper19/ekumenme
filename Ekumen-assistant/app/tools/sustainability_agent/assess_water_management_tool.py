"""
Assess Water Management Tool - Single Purpose Tool

Job: Assess water management efficiency and sustainability of agricultural practices.
Input: water_usage, irrigation_system, water_quality, efficiency_measures
Output: JSON string with water management assessment

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
class WaterManagementIndicator:
    """Structured water management indicator."""
    indicator_type: str
    current_value: float
    optimal_range: Dict[str, float]
    efficiency_status: str
    improvement_measures: List[str]

class AssessWaterManagementTool(BaseTool):
    """
    Tool: Assess water management efficiency and sustainability of agricultural practices.
    
    Job: Take water management data and assess efficiency and sustainability.
    Input: water_usage, irrigation_system, water_quality, efficiency_measures
    Output: JSON string with water management assessment
    """
    
    name: str = "assess_water_management_tool"
    description: str = "Évalue l'efficacité et la durabilité de la gestion de l'eau"
    
    def _run(
        self,
        water_usage: Dict[str, float] = None,
        irrigation_system: str = None,
        water_quality: Dict[str, float] = None,
        efficiency_measures: List[str] = None,
        **kwargs
    ) -> str:
        """
        Assess water management efficiency and sustainability of agricultural practices.
        
        Args:
            water_usage: Dictionary of water usage data (total_usage, per_hectare, etc.)
            irrigation_system: Type of irrigation system (drip, sprinkler, flood, etc.)
            water_quality: Dictionary of water quality indicators (pH, salinity, etc.)
            efficiency_measures: List of water efficiency measures implemented
        """
        try:
            # Get water management database
            water_database = self._get_water_database()
            
            # Assess water management indicators
            water_indicators = self._assess_water_indicators(water_usage or {}, water_quality or {}, water_database)
            
            # Calculate water efficiency score
            water_efficiency_score = self._calculate_water_efficiency_score(water_indicators, irrigation_system, efficiency_measures or [])
            
            # Assess irrigation system efficiency
            irrigation_efficiency = self._assess_irrigation_efficiency(irrigation_system, water_database)
            
            # Generate water management recommendations
            water_recommendations = self._generate_water_recommendations(water_indicators, irrigation_efficiency, efficiency_measures or [])
            
            result = {
                "water_usage": water_usage or {},
                "irrigation_system": irrigation_system,
                "water_quality": water_quality or {},
                "efficiency_measures": efficiency_measures or [],
                "water_indicators": [asdict(indicator) for indicator in water_indicators],
                "water_efficiency_score": water_efficiency_score,
                "irrigation_efficiency": irrigation_efficiency,
                "water_recommendations": water_recommendations,
                "total_indicators": len(water_indicators)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Assess water management error: {e}")
            return json.dumps({"error": f"Erreur lors de l'évaluation de la gestion de l'eau: {str(e)}"})
    
    def _get_water_database(self) -> Dict[str, Any]:
        """Get water management database with optimal ranges and efficiency measures."""
        water_database = {
            "water_usage": {
                "per_hectare": {
                    "optimal_range": {"min": 300.0, "max": 600.0},
                    "improvement_measures": ["irrigation_précision", "système_drip", "gestion_demandes"]
                },
                "efficiency_ratio": {
                    "optimal_range": {"min": 0.8, "max": 1.0},
                    "improvement_measures": ["système_contrôlé", "capteurs_sol", "gestion_temps"]
                }
            },
            "water_quality": {
                "ph": {
                    "optimal_range": {"min": 6.5, "max": 8.5},
                    "improvement_measures": ["traitement_eau", "filtrage", "ajustement_ph"]
                },
                "salinity": {
                    "optimal_range": {"min": 0.0, "max": 2.0},
                    "improvement_measures": ["dessalement", "mélange_eau", "sélection_cultures"]
                },
                "turbidity": {
                    "optimal_range": {"min": 0.0, "max": 5.0},
                    "improvement_measures": ["filtrage", "décantation", "traitement_eau"]
                }
            },
            "irrigation_systems": {
                "drip": {"efficiency": 0.95, "water_savings": 0.3},
                "sprinkler": {"efficiency": 0.85, "water_savings": 0.15},
                "flood": {"efficiency": 0.60, "water_savings": 0.0},
                "center_pivot": {"efficiency": 0.90, "water_savings": 0.25}
            }
        }
        
        return water_database
    
    def _assess_water_indicators(self, water_usage: Dict[str, float], water_quality: Dict[str, float], water_database: Dict[str, Any]) -> List[WaterManagementIndicator]:
        """Assess water management indicators."""
        indicators = []
        
        # Assess water usage indicators
        for usage_type, current_value in water_usage.items():
            if usage_type in water_database["water_usage"]:
                indicator_data = water_database["water_usage"][usage_type]
                optimal_range = indicator_data["optimal_range"]
                
                efficiency_status = self._determine_efficiency_status(current_value, optimal_range)
                
                indicator = WaterManagementIndicator(
                    indicator_type=f"water_usage_{usage_type}",
                    current_value=current_value,
                    optimal_range=optimal_range,
                    efficiency_status=efficiency_status,
                    improvement_measures=indicator_data["improvement_measures"]
                )
                indicators.append(indicator)
        
        # Assess water quality indicators
        for quality_type, current_value in water_quality.items():
            if quality_type in water_database["water_quality"]:
                indicator_data = water_database["water_quality"][quality_type]
                optimal_range = indicator_data["optimal_range"]
                
                efficiency_status = self._determine_efficiency_status(current_value, optimal_range)
                
                indicator = WaterManagementIndicator(
                    indicator_type=f"water_quality_{quality_type}",
                    current_value=current_value,
                    optimal_range=optimal_range,
                    efficiency_status=efficiency_status,
                    improvement_measures=indicator_data["improvement_measures"]
                )
                indicators.append(indicator)
        
        return indicators
    
    def _determine_efficiency_status(self, current_value: float, optimal_range: Dict[str, float]) -> str:
        """Determine efficiency status based on current value and optimal range."""
        min_optimal = optimal_range["min"]
        max_optimal = optimal_range["max"]
        
        if min_optimal <= current_value <= max_optimal:
            return "optimal"
        elif current_value < min_optimal * 0.8 or current_value > max_optimal * 1.2:
            return "poor"
        else:
            return "moderate"
    
    def _calculate_water_efficiency_score(self, water_indicators: List[WaterManagementIndicator], irrigation_system: str, efficiency_measures: List[str]) -> Dict[str, Any]:
        """Calculate overall water efficiency score."""
        if not water_indicators:
            return {"score": 0.0, "level": "unknown"}
        
        # Calculate base score from indicators
        total_score = 0.0
        for indicator in water_indicators:
            if indicator.efficiency_status == "optimal":
                total_score += 1.0
            elif indicator.efficiency_status == "moderate":
                total_score += 0.6
            else:  # poor
                total_score += 0.2
        
        base_score = total_score / len(water_indicators)
        
        # Adjust score based on irrigation system
        irrigation_adjustment = 0.0
        if irrigation_system:
            irrigation_efficiency = self._get_irrigation_efficiency(irrigation_system)
            irrigation_adjustment = irrigation_efficiency * 0.2
        
        # Adjust score based on efficiency measures
        measures_adjustment = len(efficiency_measures) * 0.1
        
        final_score = min(base_score + irrigation_adjustment + measures_adjustment, 1.0)
        
        # Determine efficiency level
        if final_score > 0.8:
            level = "excellent"
        elif final_score > 0.6:
            level = "good"
        elif final_score > 0.4:
            level = "moderate"
        else:
            level = "poor"
        
        return {
            "score": round(final_score, 2),
            "level": level
        }
    
    def _get_irrigation_efficiency(self, irrigation_system: str) -> float:
        """Get irrigation system efficiency."""
        irrigation_efficiencies = {
            "drip": 0.95,
            "sprinkler": 0.85,
            "flood": 0.60,
            "center_pivot": 0.90
        }
        
        return irrigation_efficiencies.get(irrigation_system.lower(), 0.70)
    
    def _assess_irrigation_efficiency(self, irrigation_system: str, water_database: Dict[str, Any]) -> Dict[str, Any]:
        """Assess irrigation system efficiency."""
        if not irrigation_system or irrigation_system not in water_database["irrigation_systems"]:
            return {"efficiency": 0.0, "water_savings": 0.0, "recommendation": "Système d'irrigation non identifié"}
        
        system_data = water_database["irrigation_systems"][irrigation_system]
        
        # Generate recommendation based on efficiency
        if system_data["efficiency"] > 0.9:
            recommendation = "Système d'irrigation très efficace - Maintenir"
        elif system_data["efficiency"] > 0.8:
            recommendation = "Système d'irrigation efficace - Optimiser si possible"
        else:
            recommendation = "Système d'irrigation peu efficace - Améliorer recommandé"
        
        return {
            "efficiency": system_data["efficiency"],
            "water_savings": system_data["water_savings"],
            "recommendation": recommendation
        }
    
    def _generate_water_recommendations(self, water_indicators: List[WaterManagementIndicator], irrigation_efficiency: Dict[str, Any], efficiency_measures: List[str]) -> List[str]:
        """Generate water management recommendations."""
        recommendations = []
        
        # Recommendations based on water indicators
        for indicator in water_indicators:
            if indicator.efficiency_status == "poor":
                recommendations.append(f"🚨 {indicator.indicator_type}: Efficacité faible ({indicator.current_value}) - Action urgente requise")
                recommendations.extend([f"Amélioration: {measure}" for measure in indicator.improvement_measures[:2]])
            elif indicator.efficiency_status == "moderate":
                recommendations.append(f"⚠️ {indicator.indicator_type}: Efficacité modérée ({indicator.current_value}) - Amélioration recommandée")
                recommendations.extend([f"Amélioration: {measure}" for measure in indicator.improvement_measures[:1]])
        
        # Recommendations based on irrigation efficiency
        if irrigation_efficiency["efficiency"] < 0.8:
            recommendations.append(f"💧 Système d'irrigation: {irrigation_efficiency['recommendation']}")
            recommendations.append("Considérer l'upgrade vers un système plus efficace")
        
        # Recommendations based on efficiency measures
        if len(efficiency_measures) < 3:
            recommendations.append("🔧 Implémenter plus de mesures d'efficacité de l'eau")
            recommendations.append("Considérer: capteurs de sol, gestion des demandes, systèmes de contrôle")
        
        # General water management recommendations
        recommendations.append("💧 Implémenter un système d'irrigation de précision")
        recommendations.append("📊 Utiliser des capteurs de sol pour optimiser l'irrigation")
        recommendations.append("🔄 Recycler et réutiliser l'eau quand possible")
        recommendations.append("🌱 Sélectionner des cultures adaptées aux conditions hydriques")
        recommendations.append("📅 Planifier l'irrigation selon les besoins réels des cultures")
        
        return recommendations
