"""
Generate Sustainability Report Tool - Single Purpose Tool

Job: Generate comprehensive sustainability reports from environmental analyses.
Input: JSON strings from other sustainability tools
Output: JSON string with comprehensive sustainability report

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
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SustainabilityMetric:
    """Structured sustainability metric."""
    metric_type: str
    current_value: float
    target_value: float
    performance_level: str
    improvement_potential: float

class GenerateSustainabilityReportTool(BaseTool):
    """
    Tool: Generate comprehensive sustainability reports from environmental analyses.
    
    Job: Take results from other sustainability tools and generate comprehensive report.
    Input: JSON strings from other sustainability tools
    Output: JSON string with comprehensive sustainability report
    """
    
    name: str = "generate_sustainability_report_tool"
    description: str = "Génère un rapport de durabilité complet"
    
    def _run(
        self,
        carbon_footprint_json: str = None,
        biodiversity_json: str = None,
        soil_health_json: str = None,
        water_management_json: str = None,
        **kwargs
    ) -> str:
        """
        Generate comprehensive sustainability report from environmental analyses.
        
        Args:
            carbon_footprint_json: JSON string from CalculateCarbonFootprintTool (optional)
            biodiversity_json: JSON string from AssessBiodiversityTool (optional)
            soil_health_json: JSON string from AnalyzeSoilHealthTool (optional)
            water_management_json: JSON string from AssessWaterManagementTool (optional)
        """
        try:
            # Parse input data
            carbon_footprint = json.loads(carbon_footprint_json) if carbon_footprint_json else None
            biodiversity = json.loads(biodiversity_json) if biodiversity_json else None
            soil_health = json.loads(soil_health_json) if soil_health_json else None
            water_management = json.loads(water_management_json) if water_management_json else None
            
            # Generate comprehensive sustainability report
            sustainability_report = self._generate_comprehensive_sustainability_report(
                carbon_footprint, biodiversity, soil_health, water_management
            )
            
            return json.dumps(sustainability_report, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Generate sustainability report error: {e}")
            return json.dumps({"error": f"Erreur lors de la génération du rapport de durabilité: {str(e)}"})
    
    def _generate_comprehensive_sustainability_report(self, carbon_footprint: Dict = None, biodiversity: Dict = None, soil_health: Dict = None, water_management: Dict = None) -> Dict[str, Any]:
        """Generate comprehensive sustainability report."""
        sustainability_report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "sustainability_assessment",
                "version": "1.0"
            },
            "executive_summary": self._generate_executive_summary(carbon_footprint, biodiversity, soil_health, water_management),
            "sustainability_metrics": self._generate_sustainability_metrics(carbon_footprint, biodiversity, soil_health, water_management),
            "environmental_impact": self._extract_environmental_impact(carbon_footprint, biodiversity, soil_health, water_management),
            "sustainability_score": self._calculate_sustainability_score(carbon_footprint, biodiversity, soil_health, water_management),
            "improvement_opportunities": self._identify_improvement_opportunities(carbon_footprint, biodiversity, soil_health, water_management),
            "sustainability_recommendations": self._generate_sustainability_recommendations(carbon_footprint, biodiversity, soil_health, water_management)
        }
        
        return sustainability_report
    
    def _generate_executive_summary(self, carbon_footprint: Dict = None, biodiversity: Dict = None, soil_health: Dict = None, water_management: Dict = None) -> Dict[str, Any]:
        """Generate executive summary of sustainability report."""
        summary = {
            "overall_sustainability_level": "moderate",
            "key_strengths": [],
            "key_challenges": [],
            "priority_actions": []
        }
        
        # Analyze carbon footprint
        if carbon_footprint:
            total_carbon = carbon_footprint.get("total_carbon_footprint", 0)
            if total_carbon < 50:
                summary["key_strengths"].append("Faible empreinte carbone")
            elif total_carbon > 100:
                summary["key_challenges"].append("Empreinte carbone élevée")
                summary["priority_actions"].append("Réduire l'empreinte carbone")
        
        # Analyze biodiversity
        if biodiversity:
            biodiversity_score = biodiversity.get("biodiversity_score", {})
            if biodiversity_score.get("level") == "high":
                summary["key_strengths"].append("Biodiversité bien préservée")
            elif biodiversity_score.get("level") == "low":
                summary["key_challenges"].append("Biodiversité menacée")
                summary["priority_actions"].append("Améliorer la biodiversité")
        
        # Analyze soil health
        if soil_health:
            soil_score = soil_health.get("soil_health_score", {})
            if soil_score.get("level") == "excellent":
                summary["key_strengths"].append("Santé du sol excellente")
            elif soil_score.get("level") == "poor":
                summary["key_challenges"].append("Santé du sol dégradée")
                summary["priority_actions"].append("Améliorer la santé du sol")
        
        # Analyze water management
        if water_management:
            water_score = water_management.get("water_efficiency_score", {})
            if water_score.get("level") == "excellent":
                summary["key_strengths"].append("Gestion de l'eau efficace")
            elif water_score.get("level") == "poor":
                summary["key_challenges"].append("Gestion de l'eau inefficace")
                summary["priority_actions"].append("Améliorer la gestion de l'eau")
        
        # Determine overall sustainability level
        if len(summary["key_strengths"]) >= 3 and len(summary["key_challenges"]) <= 1:
            summary["overall_sustainability_level"] = "high"
        elif len(summary["key_challenges"]) >= 3:
            summary["overall_sustainability_level"] = "low"
        
        return summary
    
    def _generate_sustainability_metrics(self, carbon_footprint: Dict = None, biodiversity: Dict = None, soil_health: Dict = None, water_management: Dict = None) -> List[Dict[str, Any]]:
        """Generate sustainability metrics from analyses."""
        metrics = []
        
        # Carbon footprint metrics
        if carbon_footprint:
            total_carbon = carbon_footprint.get("total_carbon_footprint", 0)
            carbon_intensity = carbon_footprint.get("carbon_intensity", 0)
            
            metrics.append({
                "metric_type": "carbon_footprint",
                "current_value": total_carbon,
                "target_value": 50.0,
                "performance_level": "good" if total_carbon < 50 else "moderate" if total_carbon < 100 else "poor",
                "improvement_potential": 0.3
            })
            
            metrics.append({
                "metric_type": "carbon_intensity",
                "current_value": carbon_intensity,
                "target_value": 25.0,
                "performance_level": "good" if carbon_intensity < 25 else "moderate" if carbon_intensity < 50 else "poor",
                "improvement_potential": 0.4
            })
        
        # Biodiversity metrics
        if biodiversity:
            biodiversity_score = biodiversity.get("biodiversity_score", {})
            score_value = biodiversity_score.get("score", 0)
            
            metrics.append({
                "metric_type": "biodiversity_score",
                "current_value": score_value,
                "target_value": 0.8,
                "performance_level": "good" if score_value > 0.8 else "moderate" if score_value > 0.6 else "poor",
                "improvement_potential": 0.5
            })
        
        # Soil health metrics
        if soil_health:
            soil_score = soil_health.get("soil_health_score", {})
            score_value = soil_score.get("score", 0)
            
            metrics.append({
                "metric_type": "soil_health_score",
                "current_value": score_value,
                "target_value": 0.8,
                "performance_level": "good" if score_value > 0.8 else "moderate" if score_value > 0.6 else "poor",
                "improvement_potential": 0.4
            })
        
        # Water management metrics
        if water_management:
            water_score = water_management.get("water_efficiency_score", {})
            score_value = water_score.get("score", 0)
            
            metrics.append({
                "metric_type": "water_efficiency_score",
                "current_value": score_value,
                "target_value": 0.8,
                "performance_level": "good" if score_value > 0.8 else "moderate" if score_value > 0.6 else "poor",
                "improvement_potential": 0.3
            })
        
        return metrics
    
    def _extract_environmental_impact(self, carbon_footprint: Dict = None, biodiversity: Dict = None, soil_health: Dict = None, water_management: Dict = None) -> Dict[str, Any]:
        """Extract environmental impact from analyses."""
        environmental_impact = {
            "carbon_impact": {},
            "biodiversity_impact": {},
            "soil_impact": {},
            "water_impact": {}
        }
        
        if carbon_footprint:
            environmental_impact["carbon_impact"] = {
                "total_emissions": carbon_footprint.get("total_carbon_footprint", 0),
                "carbon_intensity": carbon_footprint.get("carbon_intensity", 0),
                "main_sources": [comp.get("emission_source", "") for comp in carbon_footprint.get("carbon_components", [])]
            }
        
        if biodiversity:
            environmental_impact["biodiversity_impact"] = {
                "biodiversity_score": biodiversity.get("biodiversity_score", {}),
                "main_impacts": [impact.get("impact_type", "") for impact in biodiversity.get("biodiversity_impacts", [])]
            }
        
        if soil_health:
            environmental_impact["soil_impact"] = {
                "soil_health_score": soil_health.get("soil_health_score", {}),
                "main_indicators": [indicator.get("indicator_type", "") for indicator in soil_health.get("soil_health_indicators", [])]
            }
        
        if water_management:
            environmental_impact["water_impact"] = {
                "water_efficiency_score": water_management.get("water_efficiency_score", {}),
                "irrigation_efficiency": water_management.get("irrigation_efficiency", {})
            }
        
        return environmental_impact
    
    def _calculate_sustainability_score(self, carbon_footprint: Dict = None, biodiversity: Dict = None, soil_health: Dict = None, water_management: Dict = None) -> Dict[str, Any]:
        """Calculate overall sustainability score."""
        scores = []
        
        # Collect scores from different analyses
        if carbon_footprint:
            total_carbon = carbon_footprint.get("total_carbon_footprint", 0)
            carbon_score = max(0, 1 - (total_carbon / 100))  # Normalize to 0-1
            scores.append(carbon_score)
        
        if biodiversity:
            biodiversity_score = biodiversity.get("biodiversity_score", {}).get("score", 0)
            scores.append(biodiversity_score)
        
        if soil_health:
            soil_score = soil_health.get("soil_health_score", {}).get("score", 0)
            scores.append(soil_score)
        
        if water_management:
            water_score = water_management.get("water_efficiency_score", {}).get("score", 0)
            scores.append(water_score)
        
        # Calculate overall score
        if scores:
            overall_score = sum(scores) / len(scores)
            
            if overall_score > 0.8:
                level = "excellent"
            elif overall_score > 0.6:
                level = "good"
            elif overall_score > 0.4:
                level = "moderate"
            else:
                level = "poor"
        else:
            overall_score = 0.0
            level = "unknown"
        
        return {
            "overall_score": round(overall_score, 2),
            "sustainability_level": level,
            "component_scores": scores
        }
    
    def _identify_improvement_opportunities(self, carbon_footprint: Dict = None, biodiversity: Dict = None, soil_health: Dict = None, water_management: Dict = None) -> List[str]:
        """Identify improvement opportunities."""
        opportunities = []
        
        # Carbon footprint opportunities
        if carbon_footprint:
            total_carbon = carbon_footprint.get("total_carbon_footprint", 0)
            if total_carbon > 50:
                opportunities.append("Réduction de l'empreinte carbone (potentiel: 30-50%)")
        
        # Biodiversity opportunities
        if biodiversity:
            biodiversity_score = biodiversity.get("biodiversity_score", {}).get("score", 0)
            if biodiversity_score < 0.6:
                opportunities.append("Amélioration de la biodiversité (potentiel: 40-60%)")
        
        # Soil health opportunities
        if soil_health:
            soil_score = soil_health.get("soil_health_score", {}).get("score", 0)
            if soil_score < 0.6:
                opportunities.append("Amélioration de la santé du sol (potentiel: 30-50%)")
        
        # Water management opportunities
        if water_management:
            water_score = water_management.get("water_efficiency_score", {}).get("score", 0)
            if water_score < 0.6:
                opportunities.append("Amélioration de la gestion de l'eau (potentiel: 25-40%)")
        
        return opportunities
    
    def _generate_sustainability_recommendations(self, carbon_footprint: Dict = None, biodiversity: Dict = None, soil_health: Dict = None, water_management: Dict = None) -> List[str]:
        """Generate sustainability recommendations."""
        recommendations = []
        
        # Collect recommendations from different analyses
        if carbon_footprint:
            recommendations.extend(carbon_footprint.get("reduction_recommendations", []))
        
        if biodiversity:
            recommendations.extend(biodiversity.get("conservation_recommendations", []))
        
        if soil_health:
            recommendations.extend(soil_health.get("improvement_recommendations", []))
        
        if water_management:
            recommendations.extend(water_management.get("water_recommendations", []))
        
        # General sustainability recommendations
        recommendations.append("🌱 Implémenter des pratiques agroécologiques")
        recommendations.append("♻️ Développer une approche circulaire de l'agriculture")
        recommendations.append("📊 Mettre en place un système de monitoring de la durabilité")
        recommendations.append("🤝 Participer à des programmes de certification durable")
        recommendations.append("🔬 Investir dans la recherche et l'innovation durable")
        
        # Remove duplicates
        recommendations = list(set(recommendations))
        
        return recommendations
