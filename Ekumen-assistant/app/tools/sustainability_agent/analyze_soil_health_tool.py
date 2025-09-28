"""
Analyze Soil Health Tool - Single Purpose Tool

Job: Analyze soil health indicators and sustainability of agricultural practices.
Input: soil_indicators, practice_type, management_practices
Output: JSON string with soil health analysis

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
class SoilHealthIndicator:
    """Structured soil health indicator."""
    indicator_type: str
    current_value: float
    optimal_range: Dict[str, float]
    health_status: str
    improvement_measures: List[str]

class AnalyzeSoilHealthTool(BaseTool):
    """
    Tool: Analyze soil health indicators and sustainability of agricultural practices.
    
    Job: Take soil indicators and practice data to analyze soil health.
    Input: soil_indicators, practice_type, management_practices
    Output: JSON string with soil health analysis
    """
    
    name: str = "analyze_soil_health_tool"
    description: str = "Analyse la santé du sol et la durabilité des pratiques agricoles"
    
    def _run(
        self,
        soil_indicators: Dict[str, float] = None,
        practice_type: str = None,
        management_practices: List[str] = None,
        **kwargs
    ) -> str:
        """
        Analyze soil health indicators and sustainability of agricultural practices.
        
        Args:
            soil_indicators: Dictionary of soil health indicators (pH, organic_matter, etc.)
            practice_type: Type of agricultural practice
            management_practices: List of management practices implemented
        """
        try:
            # Get soil health database
            soil_health_database = self._get_soil_health_database()
            
            # Analyze soil health indicators
            soil_health_indicators = self._analyze_soil_indicators(soil_indicators or {}, soil_health_database)
            
            # Calculate overall soil health score
            soil_health_score = self._calculate_soil_health_score(soil_health_indicators)
            
            # Assess practice impact on soil health
            practice_impact = self._assess_practice_impact(practice_type, management_practices or [], soil_health_database)
            
            # Generate soil improvement recommendations
            improvement_recommendations = self._generate_improvement_recommendations(soil_health_indicators, practice_impact)
            
            result = {
                "soil_indicators": soil_indicators or {},
                "practice_type": practice_type,
                "management_practices": management_practices or [],
                "soil_health_indicators": [asdict(indicator) for indicator in soil_health_indicators],
                "soil_health_score": soil_health_score,
                "practice_impact": practice_impact,
                "improvement_recommendations": improvement_recommendations,
                "total_indicators": len(soil_health_indicators)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Analyze soil health error: {e}")
            return json.dumps({"error": f"Erreur lors de l'analyse de la santé du sol: {str(e)}"})
    
    def _get_soil_health_database(self) -> Dict[str, Any]:
        """Get soil health database with optimal ranges and improvement measures."""
        soil_health_database = {
            "ph": {
                "optimal_range": {"min": 6.0, "max": 7.5},
                "improvement_measures": ["chaulage", "apport_organique", "rotation_cultures"]
            },
            "organic_matter": {
                "optimal_range": {"min": 3.0, "max": 6.0},
                "improvement_measures": ["compost", "engrais_vert", "rotation_légumineuses"]
            },
            "nitrogen": {
                "optimal_range": {"min": 20.0, "max": 40.0},
                "improvement_measures": ["engrais_azoté", "rotation_légumineuses", "compost"]
            },
            "phosphorus": {
                "optimal_range": {"min": 15.0, "max": 30.0},
                "improvement_measures": ["engrais_phosphoré", "compost", "rotation_cultures"]
            },
            "potassium": {
                "optimal_range": {"min": 100.0, "max": 200.0},
                "improvement_measures": ["engrais_potassique", "compost", "rotation_cultures"]
            },
            "calcium": {
                "optimal_range": {"min": 2000.0, "max": 4000.0},
                "improvement_measures": ["chaulage", "compost", "rotation_cultures"]
            },
            "magnesium": {
                "optimal_range": {"min": 100.0, "max": 300.0},
                "improvement_measures": ["engrais_magnésien", "chaulage", "compost"]
            },
            "soil_structure": {
                "optimal_range": {"min": 7.0, "max": 10.0},
                "improvement_measures": ["rotation_cultures", "couverture_sol", "réduction_travail"]
            },
            "water_retention": {
                "optimal_range": {"min": 15.0, "max": 25.0},
                "improvement_measures": ["apport_organique", "couverture_sol", "rotation_cultures"]
            }
        }
        
        return soil_health_database
    
    def _analyze_soil_indicators(self, soil_indicators: Dict[str, float], soil_health_database: Dict[str, Any]) -> List[SoilHealthIndicator]:
        """Analyze soil health indicators."""
        indicators = []
        
        for indicator_type, current_value in soil_indicators.items():
            if indicator_type in soil_health_database:
                indicator_data = soil_health_database[indicator_type]
                optimal_range = indicator_data["optimal_range"]
                
                # Determine health status
                health_status = self._determine_health_status(current_value, optimal_range)
                
                indicator = SoilHealthIndicator(
                    indicator_type=indicator_type,
                    current_value=current_value,
                    optimal_range=optimal_range,
                    health_status=health_status,
                    improvement_measures=indicator_data["improvement_measures"]
                )
                indicators.append(indicator)
        
        return indicators
    
    def _determine_health_status(self, current_value: float, optimal_range: Dict[str, float]) -> str:
        """Determine health status based on current value and optimal range."""
        min_optimal = optimal_range["min"]
        max_optimal = optimal_range["max"]
        
        if min_optimal <= current_value <= max_optimal:
            return "optimal"
        elif current_value < min_optimal * 0.8 or current_value > max_optimal * 1.2:
            return "poor"
        else:
            return "moderate"
    
    def _calculate_soil_health_score(self, soil_health_indicators: List[SoilHealthIndicator]) -> Dict[str, Any]:
        """Calculate overall soil health score."""
        if not soil_health_indicators:
            return {"score": 0.0, "level": "unknown"}
        
        # Calculate score based on health status
        total_score = 0.0
        for indicator in soil_health_indicators:
            if indicator.health_status == "optimal":
                total_score += 1.0
            elif indicator.health_status == "moderate":
                total_score += 0.6
            else:  # poor
                total_score += 0.2
        
        average_score = total_score / len(soil_health_indicators)
        
        # Determine soil health level
        if average_score > 0.8:
            level = "excellent"
        elif average_score > 0.6:
            level = "good"
        elif average_score > 0.4:
            level = "moderate"
        else:
            level = "poor"
        
        return {
            "score": round(average_score, 2),
            "level": level
        }
    
    def _assess_practice_impact(self, practice_type: str, management_practices: List[str], soil_health_database: Dict[str, Any]) -> Dict[str, Any]:
        """Assess impact of agricultural practices on soil health."""
        practice_impacts = {
            "spraying": {"impact": "negative", "severity": "moderate"},
            "fertilization": {"impact": "positive", "severity": "high"},
            "irrigation": {"impact": "neutral", "severity": "low"},
            "harvesting": {"impact": "negative", "severity": "low"},
            "tillage": {"impact": "negative", "severity": "moderate"},
            "rotation": {"impact": "positive", "severity": "high"},
            "cover_crops": {"impact": "positive", "severity": "high"},
            "organic_amendments": {"impact": "positive", "severity": "high"}
        }
        
        # Get base impact for practice type
        base_impact = practice_impacts.get(practice_type, {"impact": "neutral", "severity": "low"})
        
        # Adjust impact based on management practices
        adjusted_impact = base_impact.copy()
        
        # Count positive management practices
        positive_practices = 0
        for practice in management_practices:
            if practice.lower() in ["rotation", "compost", "engrais_vert", "couverture_sol"]:
                positive_practices += 1
        
        # Adjust impact based on positive practices
        if positive_practices >= 2:
            if adjusted_impact["impact"] == "negative":
                adjusted_impact["impact"] = "neutral"
            elif adjusted_impact["impact"] == "neutral":
                adjusted_impact["impact"] = "positive"
        
        return adjusted_impact
    
    def _generate_improvement_recommendations(self, soil_health_indicators: List[SoilHealthIndicator], practice_impact: Dict[str, Any]) -> List[str]:
        """Generate soil improvement recommendations."""
        recommendations = []
        
        # Recommendations based on soil health indicators
        for indicator in soil_health_indicators:
            if indicator.health_status == "poor":
                recommendations.append(f"🚨 {indicator.indicator_type}: Valeur critique ({indicator.current_value}) - Action urgente requise")
                recommendations.extend([f"Amélioration: {measure}" for measure in indicator.improvement_measures[:2]])
            elif indicator.health_status == "moderate":
                recommendations.append(f"⚠️ {indicator.indicator_type}: Valeur modérée ({indicator.current_value}) - Amélioration recommandée")
                recommendations.extend([f"Amélioration: {measure}" for measure in indicator.improvement_measures[:1]])
        
        # Recommendations based on practice impact
        if practice_impact["impact"] == "negative":
            recommendations.append(f"🔧 Pratique {practice_impact['severity']}: Impact négatif sur la santé du sol")
            recommendations.append("Considérer des alternatives plus durables")
        elif practice_impact["impact"] == "positive":
            recommendations.append(f"✅ Pratique {practice_impact['severity']}: Impact positif sur la santé du sol")
            recommendations.append("Maintenir et renforcer ces pratiques")
        
        # General soil health recommendations
        recommendations.append("🌱 Implémenter une rotation des cultures diversifiée")
        recommendations.append("♻️ Augmenter la matière organique du sol (compost, engrais vert)")
        recommendations.append("🌿 Réduire le travail du sol pour préserver la structure")
        recommendations.append("💧 Améliorer la gestion de l'eau et du drainage")
        
        return recommendations
