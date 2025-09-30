"""
Enhanced Treatment Plan Generation Tool with Pydantic schemas, caching, and error handling

Improvements over original:
- ✅ Pydantic schemas for type safety
- ✅ Redis caching with 30-min TTL
- ✅ Async support
- ✅ Granular error handling
- ✅ Database integration (Crop table + EPPO codes)
- ✅ Follows PoC pattern (Service class + StructuredTool)
- ✅ Input validation (max 10 analyses, budget constraints)
- ✅ Multi-issue prioritization (not just top issue)
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from langchain.tools import StructuredTool
from pydantic import ValidationError, Field

from app.models.crop import Crop
from app.tools.schemas.treatment_schemas import (
    TreatmentPlanInput,
    TreatmentPlanOutput,
    TreatmentStep,
    TreatmentSchedule,
    CostAnalysis,
    MonitoringPlan,
    TreatmentPriority,
    TreatmentType,
    TreatmentTiming
)
from app.tools.schemas.disease_schemas import DiseaseDiagnosisOutput
from app.tools.schemas.pest_schemas import PestIdentificationOutput
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)

# Maximum number of treatment steps (realistic limit)
MAX_TREATMENT_STEPS = 10


# Treatment cost estimates (EUR per hectare)
TREATMENT_COSTS = {
    "fungicide": 45.0,
    "insecticide": 35.0,
    "herbicide": 30.0,
    "fertilizer": 50.0,
    "biological": 60.0,
    "cultural": 15.0,
    "mechanical": 25.0
}


class EnhancedTreatmentService:
    """Service for treatment plan generation with caching and database integration"""

    @redis_cache(ttl=1800, model_class=TreatmentPlanOutput, category="crop_health")
    async def generate_treatment_plan(self, input_data: TreatmentPlanInput) -> TreatmentPlanOutput:
        """
        Generate comprehensive treatment plan.
        
        Args:
            input_data: Validated treatment plan input
            
        Returns:
            TreatmentPlanOutput with comprehensive plan
        """
        try:
            # Step 1: Get crop from database
            crop = await self._get_crop_from_database(input_data.crop_type, input_data.eppo_code)

            if not crop:
                raise ValueError(f"Culture inconnue: {input_data.crop_type}")
            
            # Step 2: Generate executive summary
            executive_summary = self._generate_executive_summary(
                input_data.disease_analysis,
                input_data.pest_analysis,
                input_data.nutrient_analysis
            )
            
            # Step 3: Generate treatment steps
            treatment_steps = self._generate_treatment_steps(
                crop=crop,
                disease_analysis=input_data.disease_analysis,
                pest_analysis=input_data.pest_analysis,
                nutrient_analysis=input_data.nutrient_analysis,
                bbch_stage=input_data.bbch_stage,
                organic_farming=input_data.organic_farming
            )
            
            # Step 4: Generate treatment schedule
            treatment_schedule = self._generate_treatment_schedule(
                treatment_steps,
                input_data.bbch_stage
            )
            
            # Step 5: Generate cost analysis
            cost_analysis = self._generate_cost_analysis(
                treatment_steps,
                input_data.field_size_ha,
                input_data.budget_constraint
            )
            
            # Step 6: Generate monitoring plan
            monitoring_plan = self._generate_monitoring_plan(
                treatment_steps,
                crop
            )
            
            # Step 7: Generate prevention measures
            prevention_measures = self._generate_prevention_measures(
                crop,
                input_data.disease_analysis,
                input_data.pest_analysis,
                input_data.nutrient_analysis
            )
            
            # Step 8: Build output
            output = TreatmentPlanOutput(
                success=True,
                crop_type=crop.name_fr,
                crop_eppo_code=crop.eppo_code,
                plan_metadata={
                    "generated_at": datetime.now().isoformat(),
                    "plan_version": "2.0",
                    "crop_category": crop.category,
                    "bbch_stage": input_data.bbch_stage,
                    "organic_farming": input_data.organic_farming
                },
                executive_summary=executive_summary,
                treatment_steps=treatment_steps,
                treatment_schedule=treatment_schedule,
                cost_analysis=cost_analysis,
                monitoring_plan=monitoring_plan,
                prevention_measures=prevention_measures,
                total_steps=len(treatment_steps),
                estimated_duration_days=self._estimate_duration(treatment_steps),
                timestamp=datetime.now()
            )
            
            logger.info(
                f"Treatment plan generated for {crop.name_fr} (EPPO: {crop.eppo_code}): "
                f"{len(treatment_steps)} steps, {cost_analysis.total_estimated_cost_eur:.2f} EUR"
            )
            
            return output
            
        except ValueError as e:
            logger.error(f"Treatment plan generation error: {e}")
            return TreatmentPlanOutput(
                success=False,
                crop_type=input_data.crop_type,
                plan_metadata={"error": str(e)},
                executive_summary={},
                treatment_steps=[],
                treatment_schedule=[],
                cost_analysis=CostAnalysis(
                    total_estimated_cost_eur=0.0,
                    cost_breakdown={}
                ),
                monitoring_plan=MonitoringPlan(
                    monitoring_frequency="unknown",
                    monitoring_methods=[],
                    success_indicators=[],
                    warning_signs=[]
                ),
                prevention_measures=[],
                total_steps=0,
                error=str(e),
                error_type=getattr(e, 'error_type', 'unknown_error')
            )
        except Exception as e:
            logger.exception(f"Unexpected error in treatment plan generation: {e}")
            return TreatmentPlanOutput(
                success=False,
                crop_type=input_data.crop_type,
                plan_metadata={},
                executive_summary={},
                treatment_steps=[],
                treatment_schedule=[],
                cost_analysis=CostAnalysis(
                    total_estimated_cost_eur=0.0,
                    cost_breakdown={}
                ),
                monitoring_plan=MonitoringPlan(
                    monitoring_frequency="unknown",
                    monitoring_methods=[],
                    success_indicators=[],
                    warning_signs=[]
                ),
                prevention_measures=[],
                total_steps=0,
                error=f"Erreur inattendue: {str(e)}",
                error_type="unexpected_error"
            )
    
    async def _get_crop_from_database(self, crop_name: str, eppo_code: Optional[str] = None) -> Optional[Crop]:
        """Get crop from database using Crop model"""
        try:
            if eppo_code:
                crop = await Crop.from_eppo_code(eppo_code)
                if crop:
                    return crop
            
            crop = await Crop.from_french_name(crop_name)
            return crop
            
        except Exception as e:
            logger.warning(f"Error getting crop from database: {e}")
            return None
    
    def _generate_executive_summary(
        self,
        disease_analysis: Optional[Any],
        pest_analysis: Optional[Any],
        nutrient_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate executive summary"""
        total_issues = 0
        priority_level = TreatmentPriority.LOW
        
        # Count issues from disease analysis
        if disease_analysis:
            if isinstance(disease_analysis, DiseaseDiagnosisOutput):
                total_issues += disease_analysis.total_diagnoses
            elif isinstance(disease_analysis, dict):
                total_issues += len(disease_analysis.get("diagnoses", []))
        
        # Count issues from pest analysis
        if pest_analysis:
            if isinstance(pest_analysis, PestIdentificationOutput):
                total_issues += pest_analysis.total_identifications
            elif isinstance(pest_analysis, dict):
                total_issues += len(pest_analysis.get("pest_identifications", []))
        
        # Count issues from nutrient analysis
        if nutrient_analysis:
            total_issues += len(nutrient_analysis.get("nutrient_deficiencies", []))
        
        # Determine priority
        if total_issues > 5:
            priority_level = TreatmentPriority.CRITICAL
            duration = "3-4 semaines"
        elif total_issues > 2:
            priority_level = TreatmentPriority.HIGH
            duration = "2-3 semaines"
        elif total_issues > 0:
            priority_level = TreatmentPriority.MODERATE
            duration = "1-2 semaines"
        else:
            duration = "Aucun traitement nécessaire"
        
        return {
            "total_issues_identified": total_issues,
            "priority_level": priority_level.value,
            "estimated_treatment_duration": duration,
            "has_disease_issues": disease_analysis is not None,
            "has_pest_issues": pest_analysis is not None,
            "has_nutrient_issues": nutrient_analysis is not None
        }
    
    def _generate_treatment_steps(
        self,
        crop: Crop,
        disease_analysis: Optional[Any],
        pest_analysis: Optional[Any],
        nutrient_analysis: Optional[Dict[str, Any]],
        bbch_stage: Optional[int],
        organic_farming: bool
    ) -> List[TreatmentStep]:
        """Generate treatment steps"""
        steps = []
        step_number = 1
        
        # Disease treatment steps
        if disease_analysis:
            disease_steps = self._generate_disease_steps(
                disease_analysis,
                crop,
                step_number,
                organic_farming
            )
            steps.extend(disease_steps)
            step_number += len(disease_steps)
        
        # Pest treatment steps
        if pest_analysis:
            pest_steps = self._generate_pest_steps(
                pest_analysis,
                crop,
                step_number,
                organic_farming
            )
            steps.extend(pest_steps)
            step_number += len(pest_steps)
        
        # Nutrient treatment steps
        if nutrient_analysis:
            nutrient_steps = self._generate_nutrient_steps(
                nutrient_analysis,
                crop,
                step_number
            )
            steps.extend(nutrient_steps)

        # Limit to MAX_TREATMENT_STEPS (realistic constraint)
        if len(steps) > MAX_TREATMENT_STEPS:
            logger.warning(f"Treatment plan has {len(steps)} steps - limiting to {MAX_TREATMENT_STEPS}")
            steps = steps[:MAX_TREATMENT_STEPS]

        return steps
    
    def _generate_disease_steps(
        self,
        disease_analysis: Any,
        crop: Crop,
        start_number: int,
        organic_farming: bool
    ) -> List[TreatmentStep]:
        """Generate disease treatment steps"""
        steps = []
        
        # Extract diagnoses
        diagnoses = []
        if isinstance(disease_analysis, DiseaseDiagnosisOutput):
            diagnoses = disease_analysis.diagnoses
        elif isinstance(disease_analysis, dict):
            diagnoses = disease_analysis.get("diagnoses", [])
        
        for i, diagnosis in enumerate(diagnoses):
            if isinstance(diagnosis, dict):
                disease_name = diagnosis.get("disease_name", "Unknown")
                confidence = diagnosis.get("confidence", 0.5)
                severity = diagnosis.get("severity", "moderate")
                treatments = diagnosis.get("treatment_recommendations", [])
            else:
                disease_name = diagnosis.disease_name
                confidence = diagnosis.confidence
                severity = diagnosis.severity.value if hasattr(diagnosis.severity, 'value') else diagnosis.severity
                treatments = diagnosis.treatment_recommendations
            
            if confidence > 0.5:
                # Determine priority
                if severity == "critical" or severity == "high":
                    priority = TreatmentPriority.CRITICAL
                    timing = TreatmentTiming.IMMEDIATE
                elif severity == "moderate":
                    priority = TreatmentPriority.HIGH
                    timing = TreatmentTiming.WITHIN_24H
                else:
                    priority = TreatmentPriority.MODERATE
                    timing = TreatmentTiming.WITHIN_WEEK
                
                # Select treatment type
                treatment_type = TreatmentType.BIOLOGICAL if organic_farming else TreatmentType.CHEMICAL
                
                step = TreatmentStep(
                    step_number=start_number + i,
                    step_name=f"Traitement maladie: {disease_name}",
                    description=f"Traitement contre {disease_name} sur {crop.name_fr}",
                    treatment_type=treatment_type,
                    priority=priority,
                    timing=timing,
                    target_issue=disease_name,
                    products=treatments[:2] if treatments else ["Consulter expert"],
                    dosage="Selon étiquette produit",
                    application_method="Pulvérisation foliaire",
                    cost_estimate_eur=TREATMENT_COSTS.get("biological" if organic_farming else "fungicide", 45.0),
                    effectiveness_rating="high" if confidence > 0.7 else "moderate",
                    safety_precautions=[
                        "Port EPI obligatoire",
                        "Respecter ZNT",
                        "Conditions météo favorables"
                    ],
                    weather_requirements="Température < 25°C, vent < 15 km/h, pas de pluie 6h"
                )
                steps.append(step)
        
        return steps
    
    def _generate_pest_steps(
        self,
        pest_analysis: Any,
        crop: Crop,
        start_number: int,
        organic_farming: bool
    ) -> List[TreatmentStep]:
        """Generate pest treatment steps"""
        steps = []
        
        # Extract pest identifications
        pests = []
        if isinstance(pest_analysis, PestIdentificationOutput):
            pests = pest_analysis.pest_identifications
        elif isinstance(pest_analysis, dict):
            pests = pest_analysis.get("pest_identifications", [])
        
        for i, pest in enumerate(pests):
            if isinstance(pest, dict):
                pest_name = pest.get("pest_name", "Unknown")
                confidence = pest.get("confidence", 0.5)
                severity = pest.get("severity", "moderate")
                treatments = pest.get("treatment_recommendations", [])
            else:
                pest_name = pest.pest_name
                confidence = pest.confidence
                severity = pest.severity.value if hasattr(pest.severity, 'value') else pest.severity
                treatments = pest.treatment_recommendations
            
            if confidence > 0.5:
                # Determine priority
                if severity == "critical" or severity == "high":
                    priority = TreatmentPriority.CRITICAL
                    timing = TreatmentTiming.IMMEDIATE
                elif severity == "moderate":
                    priority = TreatmentPriority.HIGH
                    timing = TreatmentTiming.WITHIN_24H
                else:
                    priority = TreatmentPriority.MODERATE
                    timing = TreatmentTiming.WITHIN_WEEK
                
                # Select treatment type
                treatment_type = TreatmentType.BIOLOGICAL if organic_farming else TreatmentType.INTEGRATED
                
                step = TreatmentStep(
                    step_number=start_number + i,
                    step_name=f"Traitement ravageur: {pest_name}",
                    description=f"Lutte contre {pest_name} sur {crop.name_fr}",
                    treatment_type=treatment_type,
                    priority=priority,
                    timing=timing,
                    target_issue=pest_name,
                    products=treatments[:2] if treatments else ["Consulter expert"],
                    dosage="Selon étiquette produit",
                    application_method="Pulvérisation ou piégeage",
                    cost_estimate_eur=TREATMENT_COSTS.get("biological" if organic_farming else "insecticide", 35.0),
                    effectiveness_rating="high" if confidence > 0.7 else "moderate",
                    safety_precautions=[
                        "Port EPI obligatoire",
                        "Respecter ZNT",
                        "Protéger auxiliaires"
                    ],
                    weather_requirements="Température < 25°C, vent < 15 km/h"
                )
                steps.append(step)
        
        return steps
    
    def _generate_nutrient_steps(
        self,
        nutrient_analysis: Dict[str, Any],
        crop: Crop,
        start_number: int
    ) -> List[TreatmentStep]:
        """Generate nutrient treatment steps"""
        steps = []
        
        deficiencies = nutrient_analysis.get("nutrient_deficiencies", [])
        
        for i, deficiency in enumerate(deficiencies):
            nutrient = deficiency.get("nutrient", "Unknown")
            severity = deficiency.get("severity", "moderate")
            recommendations = deficiency.get("recommendations", [])
            
            # Determine priority
            if severity == "severe":
                priority = TreatmentPriority.HIGH
                timing = TreatmentTiming.WITHIN_WEEK
            else:
                priority = TreatmentPriority.MODERATE
                timing = TreatmentTiming.SCHEDULED
            
            step = TreatmentStep(
                step_number=start_number + i,
                step_name=f"Correction carence: {nutrient}",
                description=f"Apport de {nutrient} pour {crop.name_fr}",
                treatment_type=TreatmentType.CULTURAL,
                priority=priority,
                timing=timing,
                target_issue=f"Carence en {nutrient}",
                products=recommendations[:2] if recommendations else [f"Engrais {nutrient}"],
                dosage="Selon analyse de sol",
                application_method="Épandage ou foliaire",
                cost_estimate_eur=TREATMENT_COSTS.get("fertilizer", 50.0),
                effectiveness_rating="high",
                safety_precautions=[
                    "Respecter doses",
                    "Éviter lessivage",
                    "Fractionnement si nécessaire"
                ],
                weather_requirements="Pas de pluie forte prévue"
            )
            steps.append(step)
        
        return steps
    
    def _generate_treatment_schedule(
        self,
        treatment_steps: List[TreatmentStep],
        bbch_stage: Optional[int]
    ) -> List[TreatmentSchedule]:
        """Generate treatment schedule"""
        schedule = []
        
        # Group by timing
        immediate_steps = [s.step_number for s in treatment_steps if s.timing == TreatmentTiming.IMMEDIATE]
        within_24h_steps = [s.step_number for s in treatment_steps if s.timing == TreatmentTiming.WITHIN_24H]
        within_week_steps = [s.step_number for s in treatment_steps if s.timing == TreatmentTiming.WITHIN_WEEK]
        scheduled_steps = [s.step_number for s in treatment_steps if s.timing == TreatmentTiming.SCHEDULED]
        
        if immediate_steps:
            schedule.append(TreatmentSchedule(
                scheduled_date="immediate",
                treatment_steps=immediate_steps,
                weather_dependent=True,
                bbch_stage_dependent=False,
                notes="Traitement urgent - intervenir dès que possible"
            ))
        
        if within_24h_steps:
            schedule.append(TreatmentSchedule(
                scheduled_date="within_24h",
                treatment_steps=within_24h_steps,
                weather_dependent=True,
                bbch_stage_dependent=False,
                notes="Traitement prioritaire - dans les 24 heures"
            ))
        
        if within_week_steps:
            schedule.append(TreatmentSchedule(
                scheduled_date="within_week",
                treatment_steps=within_week_steps,
                weather_dependent=True,
                bbch_stage_dependent=False,
                notes="Traitement à planifier cette semaine"
            ))
        
        if scheduled_steps:
            schedule.append(TreatmentSchedule(
                scheduled_date="scheduled",
                treatment_steps=scheduled_steps,
                weather_dependent=False,
                bbch_stage_dependent=True,
                notes="Traitement à planifier selon stade cultural"
            ))
        
        return schedule
    
    def _generate_cost_analysis(
        self,
        treatment_steps: List[TreatmentStep],
        field_size_ha: Optional[float],
        budget_constraint: Optional[float]
    ) -> CostAnalysis:
        """Generate cost analysis"""
        # Calculate total cost
        total_cost = sum(step.cost_estimate_eur or 0.0 for step in treatment_steps)
        
        # Calculate cost per hectare if field size provided
        cost_per_ha = total_cost / field_size_ha if field_size_ha and field_size_ha > 0 else None
        
        # Cost breakdown by treatment type
        cost_breakdown = {}
        for step in treatment_steps:
            treatment_type = step.treatment_type.value
            cost_breakdown[treatment_type] = cost_breakdown.get(treatment_type, 0.0) + (step.cost_estimate_eur or 0.0)
        
        # Budget status
        budget_status = "no_budget_set"
        if budget_constraint:
            if total_cost <= budget_constraint:
                budget_status = "within_budget"
            else:
                budget_status = "over_budget"
        
        # Cost optimization suggestions
        optimization_suggestions = []
        if budget_status == "over_budget":
            optimization_suggestions.append("Prioriser les traitements critiques")
            optimization_suggestions.append("Considérer alternatives biologiques moins coûteuses")
            optimization_suggestions.append("Fractionner les interventions")
        
        return CostAnalysis(
            total_estimated_cost_eur=total_cost,
            cost_per_hectare_eur=cost_per_ha,
            cost_breakdown=cost_breakdown,
            budget_status=budget_status,
            cost_optimization_suggestions=optimization_suggestions if optimization_suggestions else None
        )
    
    def _generate_monitoring_plan(
        self,
        treatment_steps: List[TreatmentStep],
        crop: Crop
    ) -> MonitoringPlan:
        """Generate monitoring plan"""
        # Determine monitoring frequency based on priority
        has_critical = any(s.priority == TreatmentPriority.CRITICAL for s in treatment_steps)
        has_high = any(s.priority == TreatmentPriority.HIGH for s in treatment_steps)
        
        if has_critical:
            frequency = "quotidien (3-5 jours)"
        elif has_high:
            frequency = "tous les 2-3 jours"
        else:
            frequency = "hebdomadaire"
        
        # Monitoring methods
        methods = [
            "Observation visuelle des symptômes",
            "Comptage des ravageurs/maladies",
            "Évaluation de l'efficacité des traitements"
        ]
        
        # Success indicators
        success_indicators = [
            "Réduction des symptômes",
            "Diminution de la pression parasitaire",
            "Amélioration de la vigueur des plantes",
            "Absence de nouveaux foyers"
        ]
        
        # Warning signs
        warning_signs = [
            "Aggravation des symptômes",
            "Extension des zones touchées",
            "Apparition de nouveaux problèmes",
            "Inefficacité des traitements"
        ]
        
        # Reassessment date
        reassessment = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        return MonitoringPlan(
            monitoring_frequency=frequency,
            monitoring_methods=methods,
            success_indicators=success_indicators,
            warning_signs=warning_signs,
            reassessment_date=reassessment
        )
    
    def _generate_prevention_measures(
        self,
        crop: Crop,
        disease_analysis: Optional[Any],
        pest_analysis: Optional[Any],
        nutrient_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate long-term prevention measures"""
        measures = []
        
        # Crop-specific measures
        if crop.category == "cereal":
            measures.extend([
                "Rotation des cultures (3-4 ans)",
                "Choix de variétés résistantes",
                "Gestion des résidus de culture"
            ])
        elif crop.category == "oilseed":
            measures.extend([
                "Rotation avec céréales",
                "Semis précoce pour éviter ravageurs",
                "Gestion des adventices hôtes"
            ])
        
        # General prevention
        measures.extend([
            "Surveillance régulière des parcelles",
            "Respect des bonnes pratiques culturales",
            "Gestion équilibrée de la fertilisation",
            "Favoriser la biodiversité fonctionnelle"
        ])
        
        return measures
    
    def _estimate_duration(self, treatment_steps: List[TreatmentStep]) -> int:
        """Estimate treatment duration in days"""
        if not treatment_steps:
            return 0
        
        # Count by timing
        has_immediate = any(s.timing == TreatmentTiming.IMMEDIATE for s in treatment_steps)
        has_within_24h = any(s.timing == TreatmentTiming.WITHIN_24H for s in treatment_steps)
        has_within_week = any(s.timing == TreatmentTiming.WITHIN_WEEK for s in treatment_steps)
        has_scheduled = any(s.timing == TreatmentTiming.SCHEDULED for s in treatment_steps)
        
        if has_scheduled:
            return 21  # 3 weeks
        elif has_within_week:
            return 14  # 2 weeks
        elif has_within_24h:
            return 7   # 1 week
        elif has_immediate:
            return 3   # 3 days
        else:
            return 7   # Default 1 week



# Create service instance
_service = EnhancedTreatmentService()


# Async wrapper function
async def generate_treatment_plan_enhanced(
    crop_type: str,
    eppo_code: Optional[str] = None,
    disease_analysis: Optional[Dict[str, Any]] = None,
    pest_analysis: Optional[Dict[str, Any]] = None,
    nutrient_analysis: Optional[Dict[str, Any]] = None,
    bbch_stage: Optional[int] = None,
    organic_farming: Optional[bool] = False,
    field_size_ha: Optional[float] = None,
    budget_constraint: Optional[float] = None
) -> str:
    """
    Generate comprehensive treatment plan integrating disease, pest, and nutrient analyses

    Args:
        crop_type: Type of crop (e.g., 'blé', 'maïs', 'colza')
        eppo_code: Optional EPPO code for crop identification
        disease_analysis: Optional disease diagnosis results
        pest_analysis: Optional pest identification results
        nutrient_analysis: Optional nutrient deficiency analysis results
        bbch_stage: Optional BBCH growth stage (0-99)
        organic_farming: Whether organic farming practices are required
        field_size_ha: Optional field size in hectares
        budget_constraint: Optional budget constraint in EUR

    Returns:
        JSON string with comprehensive treatment plan
    """
    try:
        # Create input
        input_data = TreatmentPlanInput(
            crop_type=crop_type,
            eppo_code=eppo_code,
            disease_analysis=disease_analysis,
            pest_analysis=pest_analysis,
            nutrient_analysis=nutrient_analysis,
            bbch_stage=bbch_stage,
            organic_farming=organic_farming,
            field_size_ha=field_size_ha,
            budget_constraint=budget_constraint
        )

        # Execute treatment plan generation
        result = await _service.generate_treatment_plan(input_data)

        # Return JSON
        return result.model_dump_json(indent=2)

    except ValidationError as e:
        logger.error(f"Treatment plan validation error: {e}")
        error_result = TreatmentPlanOutput(
            success=False,
            crop_type=crop_type,
            plan_metadata={},
            executive_summary={},
            treatment_steps=[],
            treatment_schedule=[],
            cost_analysis=CostAnalysis(
                total_estimated_cost_eur=0.0,
                cost_breakdown={}
            ),
            monitoring_plan=MonitoringPlan(
                monitoring_frequency="unknown",
                monitoring_methods=[],
                success_indicators=[],
                warning_signs=[]
            ),
            prevention_measures=[],
            total_steps=0,
            timestamp=datetime.now(),
            error="Erreur de validation des paramètres. Vérifiez les analyses fournies.",
            error_type="validation_error"
        )
        return error_result.model_dump_json(indent=2)

    except Exception as e:
        logger.error(f"Unexpected treatment plan error: {e}", exc_info=True)
        error_result = TreatmentPlanOutput(
            success=False,
            crop_type=crop_type,
            plan_metadata={},
            executive_summary={},
            treatment_steps=[],
            treatment_schedule=[],
            cost_analysis=CostAnalysis(
                total_estimated_cost_eur=0.0,
                cost_breakdown={}
            ),
            monitoring_plan=MonitoringPlan(
                monitoring_frequency="unknown",
                monitoring_methods=[],
                success_indicators=[],
                warning_signs=[]
            ),
            prevention_measures=[],
            total_steps=0,
            timestamp=datetime.now(),
            error="Erreur inattendue lors de la génération du plan de traitement. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create structured tool
generate_treatment_plan_tool_enhanced = StructuredTool.from_function(
    func=generate_treatment_plan_enhanced,
    name="generate_treatment_plan",
    description="""Génère un plan de traitement complet intégrant maladies, ravageurs et carences nutritionnelles.

Retourne un plan détaillé avec:
- Résumé exécutif des problèmes identifiés
- Étapes de traitement prioritisées
- Calendrier de traitement
- Analyse des coûts
- Plan de surveillance
- Mesures préventives

Utilisez cet outil pour créer un plan d'action complet après avoir identifié des problèmes de santé des cultures.""",
    args_schema=TreatmentPlanInput,
    return_direct=False,
    coroutine=generate_treatment_plan_enhanced,
    handle_validation_error=True
)

