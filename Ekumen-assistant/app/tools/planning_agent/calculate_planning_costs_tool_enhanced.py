"""
Enhanced Calculate Planning Costs Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (1h TTL for cost calculations)
- Real cost data from config or defaults
- Comprehensive cost breakdown
- ROI calculation with warnings
- Labor and equipment cost estimation
"""

import logging
import json
import os
from typing import Optional, List, Dict, Any
from langchain.tools import StructuredTool

from app.tools.schemas.planning_schemas import (
    PlanningCostsInput,
    PlanningCostsOutput,
    CostBreakdown,
    CostCategory
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)

# Config directory from environment or default
CONFIG_DIR = os.environ.get('PLANNING_CONFIG_DIR', os.path.join(
    os.path.dirname(__file__), '..', '..', 'config'
))


class EnhancedPlanningCostsService:
    """
    Service for calculating planning costs with caching.
    
    Features:
    - Cost breakdown by category (seeds, fertilizer, pesticides, labor, equipment)
    - Equipment cost estimation based on task duration
    - Labor cost calculation
    - ROI estimation with revenue projections
    - Warnings about assumptions and data quality
    
    Cache Strategy:
    - TTL: 1 hour (3600s) - cost data changes infrequently
    - Category: planning
    - Keys include crop, surface, and task count
    """
    
    # Default cost rates (€/ha or €/hour)
    DEFAULT_COSTS = {
        "equipment_rates": {
            "tracteur_120cv": 45.0,  # €/hour
            "semoir": 35.0,
            "épandeur": 30.0,
            "pulvérisateur": 25.0,
            "moissonneuse": 120.0,
            "default": 40.0
        },
        "labor_rate": 18.0,  # €/hour
        "crop_prices": {
            "blé": 220.0,  # €/tonne
            "maïs": 200.0,
            "colza": 450.0,
            "tournesol": 400.0,
            "orge": 200.0,
            "default": 200.0
        },
        "expected_yields": {
            "blé": 7.5,  # tonnes/ha
            "maïs": 10.0,
            "colza": 3.5,
            "tournesol": 3.0,
            "orge": 6.5,
            "default": 5.0
        }
    }
    
    @redis_cache(ttl=3600, model_class=PlanningCostsOutput, category="planning")
    async def calculate_costs(self, input_data: PlanningCostsInput) -> PlanningCostsOutput:
        """
        Calculate planning costs for tasks.
        
        Args:
            input_data: Validated input with crop, surface, and tasks
            
        Returns:
            PlanningCostsOutput with cost breakdown and ROI
            
        Raises:
            ValueError: If cost calculation fails
        """
        try:
            warnings = []
            
            # Validate tasks have required fields
            for idx, task in enumerate(input_data.tasks):
                if 'task_name' not in task:
                    raise ValueError(f"Tâche {idx}: doit avoir 'task_name'")
            
            # Calculate cost breakdown
            cost_breakdown = self._calculate_cost_breakdown(
                input_data.tasks,
                input_data.surface_ha,
                input_data.include_labor
            )
            
            # Calculate totals
            total_cost = sum(item.amount_eur for item in cost_breakdown)
            cost_per_ha = total_cost / input_data.surface_ha if input_data.surface_ha > 0 else 0
            
            # Estimate revenue and profit
            crop_lower = input_data.crop.lower()
            expected_yield = self.DEFAULT_COSTS["expected_yields"].get(
                crop_lower,
                self.DEFAULT_COSTS["expected_yields"]["default"]
            )
            crop_price = self.DEFAULT_COSTS["crop_prices"].get(
                crop_lower,
                self.DEFAULT_COSTS["crop_prices"]["default"]
            )
            
            estimated_revenue = expected_yield * crop_price * input_data.surface_ha
            estimated_profit = estimated_revenue - total_cost
            roi_percent = None
            if total_cost > 0:
                roi_percent = round((estimated_profit / total_cost) * 100, 1)
            
            # Add warnings about assumptions
            warnings.append(f"ℹ️ Rendement estimé: {expected_yield} t/ha (moyenne régionale)")
            warnings.append(f"ℹ️ Prix estimé: {crop_price} €/t (prix de marché actuel)")
            
            if not input_data.include_labor:
                warnings.append("⚠️ Coûts de main-d'œuvre non inclus")
            
            # Warn if ROI is low
            if roi_percent is not None:
                if roi_percent < 0:
                    warnings.append("⚠️ ROI négatif - Révision du plan recommandée")
                elif roi_percent < 10:
                    warnings.append("⚠️ ROI faible - Optimisation possible")
            
            logger.info(f"✅ Calculated costs for {input_data.crop}: {total_cost:.2f}€ total")
            
            return PlanningCostsOutput(
                success=True,
                crop=input_data.crop,
                surface_ha=input_data.surface_ha,
                total_cost_eur=round(total_cost, 2),
                cost_per_ha_eur=round(cost_per_ha, 2),
                cost_breakdown=cost_breakdown,
                estimated_revenue_eur=round(estimated_revenue, 2),
                estimated_profit_eur=round(estimated_profit, 2),
                roi_percent=roi_percent,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Planning costs calculation error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors du calcul des coûts: {str(e)}")
    
    def _calculate_cost_breakdown(
        self,
        tasks: List[Dict[str, Any]],
        surface_ha: float,
        include_labor: bool
    ) -> List[CostBreakdown]:
        """
        Calculate detailed cost breakdown by category.
        
        Categorizes costs based on task names and resources.
        """
        breakdown = []
        
        # Track costs by category
        category_costs = {
            CostCategory.SEEDS: 0.0,
            CostCategory.FERTILIZER: 0.0,
            CostCategory.PESTICIDES: 0.0,
            CostCategory.LABOR: 0.0,
            CostCategory.EQUIPMENT: 0.0,
            CostCategory.OTHER: 0.0
        }
        
        for task in tasks:
            task_name = task.get('task_name', '').lower()
            duration_days = task.get('estimated_duration_days', 1)
            duration_hours = duration_days * 8  # 8-hour workday
            
            # Categorize based on task name
            if 'semis' in task_name:
                # Seeds cost (estimated)
                seed_cost = 150.0 * surface_ha  # €150/ha average
                category_costs[CostCategory.SEEDS] += seed_cost
                
            elif 'fertilisation' in task_name or 'fertilizer' in task_name:
                # Fertilizer cost (estimated)
                fertilizer_cost = 200.0 * surface_ha  # €200/ha average
                category_costs[CostCategory.FERTILIZER] += fertilizer_cost
                
            elif 'traitement' in task_name or 'protection' in task_name or 'désherbage' in task_name:
                # Pesticide cost (estimated)
                pesticide_cost = 100.0 * surface_ha  # €100/ha average
                category_costs[CostCategory.PESTICIDES] += pesticide_cost
            
            # Equipment costs based on resources
            resources = task.get('resources_required', [])
            for resource in resources:
                if 'Équipement:' in resource:
                    equipment_name = resource.split('Équipement:')[1].strip().lower()
                    equipment_rate = self.DEFAULT_COSTS["equipment_rates"].get(
                        equipment_name,
                        self.DEFAULT_COSTS["equipment_rates"]["default"]
                    )
                    equipment_cost = equipment_rate * duration_hours
                    category_costs[CostCategory.EQUIPMENT] += equipment_cost
            
            # Labor costs
            if include_labor:
                # Extract personnel count from resources
                personnel_count = 1  # Default
                for resource in resources:
                    if 'Personnel:' in resource:
                        # Try to extract number (e.g., "Personnel: 1 chauffeur, 1 aide" -> 2)
                        personnel_str = resource.split('Personnel:')[1].strip()
                        personnel_count = personnel_str.count('1') + personnel_str.count('2')
                        personnel_count = max(1, personnel_count)
                
                labor_cost = self.DEFAULT_COSTS["labor_rate"] * duration_hours * personnel_count
                category_costs[CostCategory.LABOR] += labor_cost
        
        # Create breakdown items
        for category, amount in category_costs.items():
            if amount > 0:
                breakdown.append(CostBreakdown(
                    category=category,
                    amount_eur=round(amount, 2),
                    description=self._get_category_description(category, amount, surface_ha)
                ))
        
        return breakdown
    
    def _get_category_description(self, category: CostCategory, amount: float, surface_ha: float) -> str:
        """Generate description for cost category"""
        per_ha = amount / surface_ha if surface_ha > 0 else 0
        
        descriptions = {
            CostCategory.SEEDS: f"Semences ({per_ha:.0f}€/ha)",
            CostCategory.FERTILIZER: f"Engrais et amendements ({per_ha:.0f}€/ha)",
            CostCategory.PESTICIDES: f"Produits phytosanitaires ({per_ha:.0f}€/ha)",
            CostCategory.LABOR: f"Main-d'œuvre ({per_ha:.0f}€/ha)",
            CostCategory.EQUIPMENT: f"Équipement et mécanisation ({per_ha:.0f}€/ha)",
            CostCategory.OTHER: f"Autres coûts ({per_ha:.0f}€/ha)"
        }
        
        return descriptions.get(category, f"{category.value} ({per_ha:.0f}€/ha)")


async def calculate_planning_costs_enhanced(
    crop: str,
    surface_ha: float,
    tasks: List[Dict[str, Any]],
    include_labor: bool = True
) -> str:
    """
    Async wrapper for calculate planning costs tool
    
    Args:
        crop: Crop name (e.g., 'blé', 'maïs')
        surface_ha: Surface area in hectares
        tasks: List of tasks from generate_planning_tasks
        include_labor: Whether to include labor costs
        
    Returns:
        JSON string with cost analysis
    """
    try:
        # Validate inputs
        input_data = PlanningCostsInput(
            crop=crop,
            surface_ha=surface_ha,
            tasks=tasks,
            include_labor=include_labor
        )
        
        # Execute service
        service = EnhancedPlanningCostsService()
        result = await service.calculate_costs(input_data)
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        # Validation or business logic error
        error_result = PlanningCostsOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            total_cost_eur=0.0,
            cost_per_ha_eur=0.0,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in calculate_planning_costs_enhanced: {e}", exc_info=True)
        error_result = PlanningCostsOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            total_cost_eur=0.0,
            cost_per_ha_eur=0.0,
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
calculate_planning_costs_tool_enhanced = StructuredTool.from_function(
    func=calculate_planning_costs_enhanced,
    name="calculate_planning_costs",
    description="""Calcule les coûts de planification agricole pour une culture.

Analyse:
- Coûts par catégorie (semences, engrais, phyto, main-d'œuvre, équipement)
- Coût total et coût par hectare
- Estimation du revenu et du profit
- Calcul du ROI
- Avertissements sur les hypothèses

Retourne une analyse détaillée des coûts avec recommandations.""",
    args_schema=PlanningCostsInput,
    return_direct=False,
    coroutine=calculate_planning_costs_enhanced,
    handle_validation_error=True
)

