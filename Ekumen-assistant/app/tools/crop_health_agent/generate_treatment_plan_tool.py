"""
Generate Treatment Plan Tool - Single Purpose Tool

Job: Generate comprehensive treatment plans from disease, pest, and nutrient analyses.
Input: JSON strings from other crop health tools
Output: JSON string with comprehensive treatment plan

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
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class TreatmentStep:
    """Structured treatment step."""
    step_name: str
    description: str
    priority: str
    timing: str
    cost_estimate: float
    effectiveness: str

class GenerateTreatmentPlanTool(BaseTool):
    """
    Tool: Generate comprehensive treatment plans from disease, pest, and nutrient analyses.
    
    Job: Take results from other crop health tools and generate comprehensive treatment plan.
    Input: JSON strings from other crop health tools
    Output: JSON string with comprehensive treatment plan
    """
    
    name: str = "generate_treatment_plan_tool"
    description: str = "Génère un plan de traitement complet pour la santé des cultures"
    
    def _run(
        self,
        disease_analysis_json: str = None,
        pest_analysis_json: str = None,
        nutrient_analysis_json: str = None,
        crop_type: str = None,
        **kwargs
    ) -> str:
        """
        Generate comprehensive treatment plan from crop health analyses.
        
        Args:
            disease_analysis_json: JSON string from DiagnoseDiseaseTool (optional)
            pest_analysis_json: JSON string from IdentifyPestTool (optional)
            nutrient_analysis_json: JSON string from AnalyzeNutrientDeficiencyTool (optional)
            crop_type: Type of crop for crop-specific recommendations
        """
        try:
            # Parse input data
            disease_analysis = json.loads(disease_analysis_json) if disease_analysis_json else None
            pest_analysis = json.loads(pest_analysis_json) if pest_analysis_json else None
            nutrient_analysis = json.loads(nutrient_analysis_json) if nutrient_analysis_json else None
            
            # Generate comprehensive treatment plan
            treatment_plan = self._generate_comprehensive_treatment_plan(
                disease_analysis, pest_analysis, nutrient_analysis, crop_type
            )
            
            return json.dumps(treatment_plan, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Generate treatment plan error: {e}")
            return json.dumps({"error": f"Erreur lors de la génération du plan de traitement: {str(e)}"})
    
    def _generate_comprehensive_treatment_plan(self, disease_analysis: Dict = None, pest_analysis: Dict = None, nutrient_analysis: Dict = None, crop_type: str = None) -> Dict[str, Any]:
        """Generate comprehensive treatment plan from analyses."""
        treatment_plan = {
            "plan_metadata": {
                "generated_at": datetime.now().isoformat(),
                "plan_type": "crop_health_treatment",
                "version": "1.0",
                "crop_type": crop_type
            },
            "executive_summary": self._generate_executive_summary(disease_analysis, pest_analysis, nutrient_analysis),
            "treatment_steps": self._generate_treatment_steps(disease_analysis, pest_analysis, nutrient_analysis),
            "treatment_schedule": self._generate_treatment_schedule(disease_analysis, pest_analysis, nutrient_analysis),
            "cost_analysis": self._generate_cost_analysis(disease_analysis, pest_analysis, nutrient_analysis),
            "monitoring_plan": self._generate_monitoring_plan(disease_analysis, pest_analysis, nutrient_analysis),
            "prevention_measures": self._generate_prevention_measures(disease_analysis, pest_analysis, nutrient_analysis)
        }
        
        return treatment_plan
    
    def _generate_executive_summary(self, disease_analysis: Dict = None, pest_analysis: Dict = None, nutrient_analysis: Dict = None) -> Dict[str, Any]:
        """Generate executive summary of treatment plan."""
        summary = {
            "total_issues_identified": 0,
            "priority_level": "low",
            "estimated_treatment_duration": "1-2 weeks",
            "estimated_total_cost": 0.0
        }
        
        # Count issues
        if disease_analysis and "diagnoses" in disease_analysis:
            summary["total_issues_identified"] += len(disease_analysis["diagnoses"])
        
        if pest_analysis and "pest_identifications" in pest_analysis:
            summary["total_issues_identified"] += len(pest_analysis["pest_identifications"])
        
        if nutrient_analysis and "nutrient_deficiencies" in nutrient_analysis:
            summary["total_issues_identified"] += len(nutrient_analysis["nutrient_deficiencies"])
        
        # Determine priority level
        if summary["total_issues_identified"] > 5:
            summary["priority_level"] = "high"
            summary["estimated_treatment_duration"] = "3-4 weeks"
        elif summary["total_issues_identified"] > 2:
            summary["priority_level"] = "moderate"
            summary["estimated_treatment_duration"] = "2-3 weeks"
        
        return summary
    
    def _generate_treatment_steps(self, disease_analysis: Dict = None, pest_analysis: Dict = None, nutrient_analysis: Dict = None) -> List[Dict[str, Any]]:
        """Generate treatment steps based on analyses."""
        treatment_steps = []
        
        # Disease treatment steps
        if disease_analysis and "diagnoses" in disease_analysis:
            for diagnosis in disease_analysis["diagnoses"]:
                if diagnosis["confidence"] > 0.6:
                    for treatment in diagnosis["treatment_recommendations"]:
                        step = TreatmentStep(
                            step_name=f"Traitement maladie: {diagnosis['disease_name']}",
                            description=f"Application de {treatment}",
                            priority="high" if diagnosis["severity"] == "high" else "moderate",
                            timing="immédiat",
                            cost_estimate=self._estimate_treatment_cost(treatment),
                            effectiveness="high" if diagnosis["confidence"] > 0.8 else "moderate"
                        )
                        treatment_steps.append(asdict(step))
        
        # Pest treatment steps
        if pest_analysis and "pest_identifications" in pest_analysis:
            for identification in pest_analysis["pest_identifications"]:
                if identification["confidence"] > 0.6:
                    for treatment in identification["treatment_recommendations"]:
                        step = TreatmentStep(
                            step_name=f"Traitement ravageur: {identification['pest_name']}",
                            description=f"Application de {treatment}",
                            priority="high" if identification["severity"] == "high" else "moderate",
                            timing="immédiat",
                            cost_estimate=self._estimate_treatment_cost(treatment),
                            effectiveness="high" if identification["confidence"] > 0.8 else "moderate"
                        )
                        treatment_steps.append(asdict(step))
        
        # Nutrient treatment steps
        if nutrient_analysis and "nutrient_deficiencies" in nutrient_analysis:
            for deficiency in nutrient_analysis["nutrient_deficiencies"]:
                if deficiency["confidence"] > 0.6:
                    for treatment in deficiency["treatment_recommendations"]:
                        step = TreatmentStep(
                            step_name=f"Traitement carence: {deficiency['nutrient']}",
                            description=f"Application de {treatment}",
                            priority="moderate",
                            timing="prochain_arrosage",
                            cost_estimate=self._estimate_treatment_cost(treatment),
                            effectiveness="high" if deficiency["confidence"] > 0.8 else "moderate"
                        )
                        treatment_steps.append(asdict(step))
        
        # Sort by priority
        treatment_steps.sort(key=lambda x: 0 if x["priority"] == "high" else 1 if x["priority"] == "moderate" else 2)
        
        return treatment_steps
    
    def _generate_treatment_schedule(self, disease_analysis: Dict = None, pest_analysis: Dict = None, nutrient_analysis: Dict = None) -> Dict[str, Any]:
        """Generate treatment schedule."""
        schedule = {
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_actions": []
        }
        
        # Immediate actions (high priority)
        if disease_analysis and "diagnoses" in disease_analysis:
            for diagnosis in disease_analysis["diagnoses"]:
                if diagnosis["severity"] == "high" and diagnosis["confidence"] > 0.7:
                    schedule["immediate_actions"].append(f"Traitement urgent: {diagnosis['disease_name']}")
        
        if pest_analysis and "pest_identifications" in pest_analysis:
            for identification in pest_analysis["pest_identifications"]:
                if identification["severity"] == "high" and identification["confidence"] > 0.7:
                    schedule["immediate_actions"].append(f"Traitement urgent: {identification['pest_name']}")
        
        # Short-term actions (moderate priority)
        if nutrient_analysis and "nutrient_deficiencies" in nutrient_analysis:
            for deficiency in nutrient_analysis["nutrient_deficiencies"]:
                if deficiency["confidence"] > 0.6:
                    schedule["short_term_actions"].append(f"Correction carence: {deficiency['nutrient']}")
        
        # Long-term actions (prevention)
        schedule["long_term_actions"] = [
            "Mise en place de mesures préventives",
            "Surveillance accrue des cultures",
            "Amélioration des pratiques culturales"
        ]
        
        return schedule
    
    def _generate_cost_analysis(self, disease_analysis: Dict = None, pest_analysis: Dict = None, nutrient_analysis: Dict = None) -> Dict[str, Any]:
        """Generate cost analysis for treatment plan."""
        total_cost = 0.0
        cost_breakdown = {
            "disease_treatments": 0.0,
            "pest_treatments": 0.0,
            "nutrient_treatments": 0.0
        }
        
        # Calculate disease treatment costs
        if disease_analysis and "diagnoses" in disease_analysis:
            for diagnosis in disease_analysis["diagnoses"]:
                for treatment in diagnosis["treatment_recommendations"]:
                    cost = self._estimate_treatment_cost(treatment)
                    cost_breakdown["disease_treatments"] += cost
                    total_cost += cost
        
        # Calculate pest treatment costs
        if pest_analysis and "pest_identifications" in pest_analysis:
            for identification in pest_analysis["pest_identifications"]:
                for treatment in identification["treatment_recommendations"]:
                    cost = self._estimate_treatment_cost(treatment)
                    cost_breakdown["pest_treatments"] += cost
                    total_cost += cost
        
        # Calculate nutrient treatment costs
        if nutrient_analysis and "nutrient_deficiencies" in nutrient_analysis:
            for deficiency in nutrient_analysis["nutrient_deficiencies"]:
                for treatment in deficiency["treatment_recommendations"]:
                    cost = self._estimate_treatment_cost(treatment)
                    cost_breakdown["nutrient_treatments"] += cost
                    total_cost += cost
        
        return {
            "total_cost": round(total_cost, 2),
            "cost_breakdown": {k: round(v, 2) for k, v in cost_breakdown.items()},
            "cost_per_hectare": round(total_cost / 10, 2)  # Assuming 10 hectares
        }
    
    def _generate_monitoring_plan(self, disease_analysis: Dict = None, pest_analysis: Dict = None, nutrient_analysis: Dict = None) -> Dict[str, Any]:
        """Generate monitoring plan."""
        monitoring_plan = {
            "monitoring_frequency": "quotidien",
            "key_indicators": [],
            "monitoring_duration": "2-4 semaines"
        }
        
        # Add monitoring indicators based on analyses
        if disease_analysis and "diagnoses" in disease_analysis:
            monitoring_plan["key_indicators"].extend(["symptômes_maladies", "progression_maladies"])
        
        if pest_analysis and "pest_identifications" in pest_analysis:
            monitoring_plan["key_indicators"].extend(["présence_ravageurs", "dégâts_ravageurs"])
        
        if nutrient_analysis and "nutrient_deficiencies" in nutrient_analysis:
            monitoring_plan["key_indicators"].extend(["symptômes_carences", "croissance_plantes"])
        
        return monitoring_plan
    
    def _generate_prevention_measures(self, disease_analysis: Dict = None, pest_analysis: Dict = None, nutrient_analysis: Dict = None) -> List[str]:
        """Generate prevention measures."""
        prevention_measures = []
        
        # Disease prevention
        if disease_analysis and "diagnoses" in disease_analysis:
            for diagnosis in disease_analysis["diagnoses"]:
                prevention_measures.extend(diagnosis["prevention_measures"])
        
        # Pest prevention
        if pest_analysis and "pest_identifications" in pest_analysis:
            for identification in pest_analysis["pest_identifications"]:
                prevention_measures.extend(identification["prevention_measures"])
        
        # Nutrient prevention
        if nutrient_analysis and "nutrient_deficiencies" in nutrient_analysis:
            for deficiency in nutrient_analysis["nutrient_deficiencies"]:
                prevention_measures.extend(deficiency["prevention_measures"])
        
        # Remove duplicates
        prevention_measures = list(set(prevention_measures))
        
        return prevention_measures
    
    def _estimate_treatment_cost(self, treatment: str) -> float:
        """Estimate treatment cost based on treatment type."""
        cost_estimates = {
            "fongicide_systémique": 45.0,
            "fongicide_contact": 35.0,
            "insecticide_systémique": 40.0,
            "insecticide_contact": 30.0,
            "engrais_azoté": 25.0,
            "engrais_phosphoré": 30.0,
            "engrais_potassique": 35.0,
            "compost": 15.0,
            "chaulage": 20.0
        }
        
        # Find matching treatment
        for treatment_type, cost in cost_estimates.items():
            if treatment_type in treatment.lower():
                return cost
        
        return 25.0  # Default cost
