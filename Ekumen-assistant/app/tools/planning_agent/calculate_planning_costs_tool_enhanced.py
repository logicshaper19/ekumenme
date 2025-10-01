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
    
    # Default cost rates with provenance and uncertainty
    # SOURCE: Chambres d'Agriculture France, FranceAgriMer (Sept 2024)
    # WARNING: These are NATIONAL AVERAGES with ±30% regional variation
    DEFAULT_COSTS = {
        "equipment_rates": {
            # €/hour actual use (not task duration)
            # Source: Barème d'entraide 2024
            "tracteur_120cv": {"rate": 45.0, "range": (35.0, 55.0)},
            "semoir": {"rate": 35.0, "range": (25.0, 45.0)},
            "épandeur": {"rate": 30.0, "range": (20.0, 40.0)},
            "pulvérisateur": {"rate": 25.0, "range": (18.0, 35.0)},
            "moissonneuse": {"rate": 120.0, "range": (100.0, 150.0)},
            "default": {"rate": 40.0, "range": (30.0, 50.0)}
        },
        "labor_rate": {
            "rate": 18.0,  # €/hour
            "range": (15.0, 22.0),
            "source": "Convention collective agricole 2024"
        },
        "crop_prices": {
            # €/tonne - FranceAgriMer Sept 2024
            # WARNING: Prices fluctuate ±20% annually
            "blé": {"price": 220.0, "range": (180.0, 260.0), "volatility": "high"},
            "maïs": {"price": 200.0, "range": (170.0, 230.0), "volatility": "high"},
            "colza": {"price": 450.0, "range": (400.0, 520.0), "volatility": "very_high"},
            "tournesol": {"price": 400.0, "range": (350.0, 450.0), "volatility": "high"},
            "orge": {"price": 200.0, "range": (170.0, 230.0), "volatility": "medium"},
            "default": {"price": 200.0, "range": (150.0, 250.0), "volatility": "unknown"}
        },
        "expected_yields": {
            # tonnes/ha - Moyenne nationale 2019-2023
            # WARNING: Variation régionale ±30%, variation annuelle ±20%
            "blé": {"yield": 7.5, "range": (5.0, 9.0), "source": "Agreste 2023"},
            "maïs": {"yield": 10.0, "range": (7.0, 12.0), "source": "Agreste 2023"},
            "colza": {"yield": 3.5, "range": (2.5, 4.5), "source": "Agreste 2023"},
            "tournesol": {"yield": 3.0, "range": (2.0, 4.0), "source": "Agreste 2023"},
            "orge": {"yield": 6.5, "range": (5.0, 8.0), "source": "Agreste 2023"},
            "default": {"yield": 5.0, "range": (3.0, 7.0), "source": "estimation"}
        },
        "data_date": "2024-09",
        "data_source": "Chambres d'Agriculture France, FranceAgriMer, Agreste"
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
            
            # CRITICAL DISCLAIMERS - Must appear first
            warnings.append("🚨 ESTIMATION PRÉLIMINAIRE UNIQUEMENT - Ne pas utiliser pour décisions financières sans consultation professionnelle")
            warnings.append(f"📅 Données basées sur moyennes nationales {self.DEFAULT_COSTS['data_date']} - Variations régionales ±30%")
            warnings.append("⚠️ COÛTS VARIABLES UNIQUEMENT - Coûts fixes non inclus (terre, assurance, stockage, transport, séchage)")

            # Estimate revenue and profit with ranges
            crop_lower = input_data.crop.lower()
            yield_data = self.DEFAULT_COSTS["expected_yields"].get(
                crop_lower,
                self.DEFAULT_COSTS["expected_yields"]["default"]
            )
            price_data = self.DEFAULT_COSTS["crop_prices"].get(
                crop_lower,
                self.DEFAULT_COSTS["crop_prices"]["default"]
            )

            expected_yield = yield_data["yield"]
            crop_price = price_data["price"]

            # Calculate base case
            estimated_revenue = expected_yield * crop_price * input_data.surface_ha
            estimated_profit = estimated_revenue - total_cost

            # Calculate best/worst case scenarios
            best_yield, worst_yield = yield_data["range"]
            best_price, worst_price = price_data["range"]

            best_case_revenue = best_yield * best_price * input_data.surface_ha
            worst_case_revenue = worst_yield * worst_price * input_data.surface_ha

            best_case_profit = best_case_revenue - total_cost
            worst_case_profit = worst_case_revenue - total_cost

            roi_percent = None
            if total_cost > 0:
                roi_percent = round((estimated_profit / total_cost) * 100, 1)

            # Add detailed warnings about assumptions
            warnings.append(
                f"⚠️ Rendement: {expected_yield} t/ha (moyenne nationale - fourchette réelle: {worst_yield}-{best_yield} t/ha selon région/année)"
            )
            warnings.append(
                f"⚠️ Prix: {crop_price}€/t (Sept 2024 - volatilité {price_data['volatility']} - fourchette: {worst_price}-{best_price}€/t)"
            )
            warnings.append(
                f"💰 Scénario optimiste: Profit {best_case_profit:.0f}€ (rendement {best_yield} t/ha, prix {best_price}€/t)"
            )
            warnings.append(
                f"💰 Scénario pessimiste: Profit {worst_case_profit:.0f}€ (rendement {worst_yield} t/ha, prix {worst_price}€/t)"
            )

            if not input_data.include_labor:
                warnings.append("⚠️ Coûts de main-d'œuvre NON INCLUS - Ajouter ~€100-200/ha")

            # Warn about missing fixed costs
            estimated_fixed_costs = input_data.surface_ha * 300  # €300/ha average
            warnings.append(f"⚠️ Coûts fixes estimés non inclus: ~{estimated_fixed_costs:.0f}€ (terre, assurance, amortissement)")

            # Warn if ROI is low (based on variable costs only)
            if roi_percent is not None:
                if roi_percent < 0:
                    warnings.append("🚨 ROI NÉGATIF sur coûts variables - Projet non viable sans révision majeure")
                elif roi_percent < 20:
                    warnings.append("⚠️ ROI faible (<20%) - Après coûts fixes, rentabilité douteuse")
                elif roi_percent < 50:
                    warnings.append("ℹ️ ROI modéré - Vérifier viabilité après ajout coûts fixes")

            # Probability of loss warning
            if worst_case_profit < 0:
                warnings.append("🚨 RISQUE DE PERTE dans scénario pessimiste - Prévoir trésorerie de sécurité")
            
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

        WARNING: Uses rough estimates based on task names.
        Real costs require detailed input quantities and prices.
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

            # Equipment utilization: assume 30% of task duration is actual equipment use
            # (rest is setup, waiting for weather, breaks, etc.)
            equipment_hours = duration_days * 8 * 0.3

            # Labor hours: assume 50% of task duration (more realistic than 100%)
            labor_hours = duration_days * 8 * 0.5

            # Categorize based on task name - ROUGH ESTIMATES ONLY
            if 'semis' in task_name:
                # Seeds cost - VERY ROUGH estimate
                # Real cost depends on variety, density, treatment
                seed_cost = 120.0 * surface_ha  # €80-150/ha range
                category_costs[CostCategory.SEEDS] += seed_cost

            elif 'fertilisation' in task_name or 'fertilizer' in task_name:
                # Fertilizer cost - VERY ROUGH estimate
                # Real cost depends on N-P-K formula, quantities, prices
                fertilizer_cost = 180.0 * surface_ha  # €100-300/ha range
                category_costs[CostCategory.FERTILIZER] += fertilizer_cost

            elif 'traitement' in task_name or 'protection' in task_name or 'désherbage' in task_name:
                # Pesticide cost - VERY ROUGH estimate
                # Real cost depends on products, doses, number of passes
                pesticide_cost = 80.0 * surface_ha  # €50-200/ha range
                category_costs[CostCategory.PESTICIDES] += pesticide_cost

            # Equipment costs based on resources
            resources = task.get('resources_required', [])
            for resource in resources:
                if 'Équipement:' in resource:
                    equipment_name = resource.split('Équipement:')[1].strip().lower()
                    equipment_data = self.DEFAULT_COSTS["equipment_rates"].get(
                        equipment_name,
                        self.DEFAULT_COSTS["equipment_rates"]["default"]
                    )
                    equipment_rate = equipment_data["rate"]
                    # Use actual equipment hours, not task duration
                    equipment_cost = equipment_rate * equipment_hours
                    category_costs[CostCategory.EQUIPMENT] += equipment_cost

            # Labor costs
            if include_labor:
                # Extract personnel count from resources with proper parsing
                personnel_count = self._extract_personnel_count(resources)

                labor_rate = self.DEFAULT_COSTS["labor_rate"]["rate"]
                labor_cost = labor_rate * labor_hours * personnel_count
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

    def _extract_personnel_count(self, resources: List[str]) -> int:
        """
        Extract personnel count from resources with proper parsing.

        Handles:
        - "Personnel: 1 chauffeur" -> 1
        - "Personnel: 1 chauffeur, 1 aide" -> 2
        - "Personnel: 12 workers" -> 12
        - "Personnel: 3 chauffeurs" -> 3
        """
        import re

        for resource in resources:
            if 'Personnel:' in resource:
                personnel_str = resource.split('Personnel:')[1].strip()

                # Find all numbers in the string
                numbers = re.findall(r'\d+', personnel_str)

                if numbers:
                    # If multiple numbers (e.g., "1 chauffeur, 1 aide"), sum them
                    # If single number (e.g., "12 workers"), use it
                    total = sum(int(n) for n in numbers)
                    return max(1, total)

        return 1  # Default
    
    def _get_category_description(self, category: CostCategory, amount: float, surface_ha: float) -> str:
        """Generate description for cost category with uncertainty ranges"""
        per_ha = amount / surface_ha if surface_ha > 0 else 0

        # Include uncertainty ranges in descriptions
        descriptions = {
            CostCategory.SEEDS: f"Semences ({per_ha:.0f}€/ha - estimation ±25%)",
            CostCategory.FERTILIZER: f"Engrais et amendements ({per_ha:.0f}€/ha - estimation ±30%)",
            CostCategory.PESTICIDES: f"Produits phytosanitaires ({per_ha:.0f}€/ha - estimation ±40%)",
            CostCategory.LABOR: f"Main-d'œuvre ({per_ha:.0f}€/ha - 50% utilisation estimée)",
            CostCategory.EQUIPMENT: f"Équipement et mécanisation ({per_ha:.0f}€/ha - 30% utilisation estimée)",
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
    description="""🚨 ESTIMATION PRÉLIMINAIRE - Calcule les coûts de planification agricole.

⚠️ AVERTISSEMENT IMPORTANT:
- Basé sur moyennes nationales (±30% variation régionale)
- COÛTS VARIABLES UNIQUEMENT (terre, assurance, stockage NON inclus)
- Données Sept 2024 - Prix agricoles volatils
- NE PAS utiliser pour décisions financières sans consultation professionnelle

Analyse fournie:
- Coûts par catégorie avec fourchettes d'incertitude
- Scénarios optimiste/pessimiste
- ROI sur coûts variables (incomplet)
- Avertissements détaillés sur limitations

Pour planification préliminaire uniquement. Consulter comptable agricole pour décisions réelles.""",
    args_schema=PlanningCostsInput,
    return_direct=False,
    coroutine=calculate_planning_costs_enhanced,
    handle_validation_error=True
)

