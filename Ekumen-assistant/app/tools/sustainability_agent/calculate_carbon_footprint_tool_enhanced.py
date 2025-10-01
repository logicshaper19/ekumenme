"""
Enhanced Calculate Carbon Footprint Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (2h TTL for carbon calculations)
- Realistic emission factors from ADEME/IPCC
- Actual quantity inputs (no assumptions)
- Sequestration potential calculation
- Benchmark comparisons
- Strong data quality disclaimers
"""

import logging
from typing import Optional, List
from langchain.tools import StructuredTool

from app.tools.schemas.sustainability_schemas import (
    CarbonFootprintInput,
    CarbonFootprintOutput,
    CarbonEmission,
    CarbonSource
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedCarbonFootprintService:
    """
    Service for calculating agricultural carbon footprint with caching.
    
    Features:
    - Realistic emission factors from ADEME (French Environment Agency)
    - Actual quantity-based calculations (no assumptions)
    - Carbon sequestration potential from practices
    - Benchmark comparisons by crop
    - Strong data quality disclaimers
    
    Cache Strategy:
    - TTL: 2 hours (7200s) - calculations are deterministic
    - Category: sustainability
    - Keys include all inputs
    
    Emission Factors (ADEME 2023):
    - Diesel: 2.68 kg CO2eq/L
    - Nitrogen fertilizer: 5.5 kg CO2eq/kg N (production + N2O emissions)
    - Phosphorus: 1.2 kg CO2eq/kg P2O5
    - Potassium: 0.6 kg CO2eq/kg K2O
    - Pesticides: 10-20 kg CO2eq/kg active ingredient
    
    Sequestration Potential:
    - Cover crops: 1.5 t CO2eq/ha/year
    - Reduced tillage: 0.5 t CO2eq/ha/year
    - Organic amendments: 0.3 t CO2eq/ha/year
    """
    
    # Emission factors (kg CO2eq per unit) - ADEME 2023
    EMISSION_FACTORS = {
        "diesel": 2.68,  # kg CO2eq/L
        "gasoline": 2.31,  # kg CO2eq/L
        "nitrogen": 5.5,  # kg CO2eq/kg N (range: 5-11 depending on type and N2O emissions)
        "phosphorus": 1.2,  # kg CO2eq/kg P2O5
        "potassium": 0.6,  # kg CO2eq/kg K2O
        "organic_fertilizer": 0.3,  # kg CO2eq/kg (much lower)
        "pesticide": 15.0,  # kg CO2eq/kg active ingredient (average)
    }
    
    # Sequestration potential (kg CO2eq/ha/year)
    SEQUESTRATION_FACTORS = {
        "cover_crops": 1500,  # 1.5 t CO2eq/ha/year
        "reduced_tillage": 500,  # 0.5 t CO2eq/ha/year
        "organic_amendments": 300,  # 0.3 t CO2eq/ha/year
    }
    
    # Benchmark emissions by crop (kg CO2eq/ha) - French averages
    CROP_BENCHMARKS = {
        "blé": 2800,  # Wheat
        "maïs": 3200,  # Corn
        "colza": 3000,  # Rapeseed
        "tournesol": 2500,  # Sunflower
        "orge": 2600,  # Barley
        "soja": 2200,  # Soybean (N-fixing)
        "pomme de terre": 3500,  # Potato (high inputs)
    }
    
    @redis_cache(ttl=7200, model_class=CarbonFootprintOutput, category="sustainability")
    async def calculate_carbon_footprint(self, input_data: CarbonFootprintInput) -> CarbonFootprintOutput:
        """
        Calculate carbon footprint from agricultural inputs.
        
        Args:
            input_data: Validated input with crop, surface, and actual quantities
            
        Returns:
            CarbonFootprintOutput with emissions breakdown and recommendations
            
        Raises:
            ValueError: If calculation fails
        """
        try:
            total_emissions = 0.0
            data_completeness_notes = []

            # Track emissions by source (calculate totals first, then create Pydantic objects)
            fuel_emissions_total = 0.0
            fertilizer_emissions_total = 0.0
            pesticide_emissions_total = 0.0

            # Calculate fuel emissions (diesel + gasoline combined)
            if input_data.diesel_liters is not None and input_data.diesel_liters > 0:
                fuel_emissions_total += input_data.diesel_liters * self.EMISSION_FACTORS["diesel"]
            if input_data.gasoline_liters is not None and input_data.gasoline_liters > 0:
                fuel_emissions_total += input_data.gasoline_liters * self.EMISSION_FACTORS["gasoline"]

            if fuel_emissions_total == 0:
                data_completeness_notes.append("Consommation carburant non fournie - émissions carburant non calculées")
            else:
                total_emissions += fuel_emissions_total

            # Calculate fertilizer emissions (all types combined)
            if input_data.nitrogen_kg is not None and input_data.nitrogen_kg > 0:
                fertilizer_emissions_total += input_data.nitrogen_kg * self.EMISSION_FACTORS["nitrogen"]
            if input_data.phosphorus_kg is not None and input_data.phosphorus_kg > 0:
                fertilizer_emissions_total += input_data.phosphorus_kg * self.EMISSION_FACTORS["phosphorus"]
            if input_data.potassium_kg is not None and input_data.potassium_kg > 0:
                fertilizer_emissions_total += input_data.potassium_kg * self.EMISSION_FACTORS["potassium"]
            if input_data.organic_fertilizer_kg is not None and input_data.organic_fertilizer_kg > 0:
                fertilizer_emissions_total += input_data.organic_fertilizer_kg * self.EMISSION_FACTORS["organic_fertilizer"]

            if fertilizer_emissions_total == 0:
                data_completeness_notes.append("Quantités engrais non fournies - émissions fertilisation non calculées")
            else:
                total_emissions += fertilizer_emissions_total

            # Calculate pesticide emissions
            if input_data.pesticide_kg is not None and input_data.pesticide_kg > 0:
                pesticide_emissions_total = input_data.pesticide_kg * self.EMISSION_FACTORS["pesticide"]
                total_emissions += pesticide_emissions_total
            else:
                data_completeness_notes.append("Quantités pesticides non fournies - émissions phyto non calculées")
            
            # Calculate sequestration potential
            sequestration = 0.0
            if input_data.cover_crops:
                sequestration += self.SEQUESTRATION_FACTORS["cover_crops"] * input_data.surface_ha
            if input_data.reduced_tillage:
                sequestration += self.SEQUESTRATION_FACTORS["reduced_tillage"] * input_data.surface_ha
            if input_data.organic_amendments:
                sequestration += self.SEQUESTRATION_FACTORS["organic_amendments"] * input_data.surface_ha

            # Now create Pydantic emission objects with percentages calculated
            emissions_by_source = []

            if fuel_emissions_total > 0:
                fuel_pct = (fuel_emissions_total / total_emissions) * 100 if total_emissions > 0 else 0
                emissions_by_source.append(CarbonEmission(
                    source=CarbonSource.FUEL,
                    emissions_kg_co2eq=round(fuel_emissions_total, 1),
                    percentage_of_total=round(fuel_pct, 1),
                    reduction_potential_percent=20.0  # Precision agriculture, route optimization
                ))

            if fertilizer_emissions_total > 0:
                fertilizer_pct = (fertilizer_emissions_total / total_emissions) * 100 if total_emissions > 0 else 0
                emissions_by_source.append(CarbonEmission(
                    source=CarbonSource.FERTILIZER,
                    emissions_kg_co2eq=round(fertilizer_emissions_total, 1),
                    percentage_of_total=round(fertilizer_pct, 1),
                    reduction_potential_percent=30.0  # Precision fertilization, organic alternatives
                ))

            if pesticide_emissions_total > 0:
                pesticide_pct = (pesticide_emissions_total / total_emissions) * 100 if total_emissions > 0 else 0
                emissions_by_source.append(CarbonEmission(
                    source=CarbonSource.PESTICIDES,
                    emissions_kg_co2eq=round(pesticide_emissions_total, 1),
                    percentage_of_total=round(pesticide_pct, 1),
                    reduction_potential_percent=40.0  # IPM, biological control
                ))

            if sequestration > 0:
                emissions_by_source.append(CarbonEmission(
                    source=CarbonSource.SEQUESTRATION,
                    emissions_kg_co2eq=-round(sequestration, 1),  # Negative = removal
                    percentage_of_total=0.0,  # Not a percentage of emissions
                    reduction_potential_percent=None
                ))
            
            # Net emissions
            net_emissions = total_emissions - sequestration
            emissions_per_ha = net_emissions / input_data.surface_ha if input_data.surface_ha > 0 else 0
            
            # Benchmark comparison
            benchmark_comparison = self._get_benchmark_comparison(
                input_data.crop,
                emissions_per_ha
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                emissions_by_source,
                input_data,
                emissions_per_ha
            )
            
            # Data quality note
            data_quality_note = self._generate_data_quality_note(
                data_completeness_notes
            )
            
            logger.info(
                f"✅ Carbon footprint calculated for {input_data.crop}: "
                f"{net_emissions:.0f} kg CO2eq total, {emissions_per_ha:.0f} kg CO2eq/ha"
            )
            
            return CarbonFootprintOutput(
                success=True,
                crop=input_data.crop,
                surface_ha=input_data.surface_ha,
                total_emissions_kg_co2eq=round(total_emissions, 1),
                emissions_per_ha=round(emissions_per_ha, 1),
                emissions_by_source=emissions_by_source,
                sequestration_potential_kg_co2eq=round(sequestration, 1),
                net_emissions_kg_co2eq=round(net_emissions, 1),
                benchmark_comparison=benchmark_comparison,
                reduction_recommendations=recommendations,
                data_quality_note=data_quality_note
            )
            
        except Exception as e:
            logger.error(f"Carbon footprint calculation error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors du calcul de l'empreinte carbone: {str(e)}")
    
    def _get_benchmark_comparison(self, crop: str, emissions_per_ha: float) -> str:
        """Compare to crop benchmark"""
        crop_lower = crop.lower()
        if crop_lower in self.CROP_BENCHMARKS:
            benchmark = self.CROP_BENCHMARKS[crop_lower]
            diff_percent = ((emissions_per_ha - benchmark) / benchmark) * 100
            
            if diff_percent < -20:
                return f"✅ Excellent: {abs(diff_percent):.0f}% sous moyenne {crop} ({benchmark} kg CO2eq/ha)"
            elif diff_percent < 0:
                return f"✅ Bon: {abs(diff_percent):.0f}% sous moyenne {crop} ({benchmark} kg CO2eq/ha)"
            elif diff_percent < 20:
                return f"⚠️ Proche moyenne {crop} ({benchmark} kg CO2eq/ha)"
            else:
                return f"🚨 {diff_percent:.0f}% au-dessus moyenne {crop} ({benchmark} kg CO2eq/ha) - Optimisation urgente"
        else:
            return f"ℹ️ Pas de référence disponible pour {crop}"
    
    def _generate_recommendations(
        self,
        emissions: List[CarbonEmission],
        input_data: CarbonFootprintInput,
        emissions_per_ha: float
    ) -> List[str]:
        """Generate reduction recommendations"""
        recommendations = []
        
        # Sort by emissions (highest first, excluding sequestration)
        sorted_emissions = sorted(
            [e for e in emissions if e.source != CarbonSource.SEQUESTRATION],
            key=lambda x: x.emissions_kg_co2eq,
            reverse=True
        )
        
        # Top emission sources
        for emission in sorted_emissions[:2]:  # Top 2 sources
            if emission.source == CarbonSource.FERTILIZER:
                recommendations.append(
                    f"🌱 Fertilisation = {emission.percentage_of_total:.0f}% émissions - "
                    f"Réduction potentielle {emission.reduction_potential_percent:.0f}% via analyse sol et fractionnement"
                )
            elif emission.source == CarbonSource.FUEL:
                recommendations.append(
                    f"⛽ Carburant = {emission.percentage_of_total:.0f}% émissions - "
                    f"Réduction potentielle {emission.reduction_potential_percent:.0f}% via optimisation trajets et entretien"
                )
            elif emission.source == CarbonSource.PESTICIDES:
                recommendations.append(
                    f"🐛 Pesticides = {emission.percentage_of_total:.0f}% émissions - "
                    f"Réduction potentielle {emission.reduction_potential_percent:.0f}% via lutte intégrée (IPM)"
                )
        
        # Sequestration recommendations
        if not input_data.cover_crops:
            recommendations.append("🌿 Implanter couverts végétaux (+1.5 t CO2eq/ha/an séquestration)")
        if not input_data.reduced_tillage:
            recommendations.append("🚜 Réduire travail du sol (+0.5 t CO2eq/ha/an séquestration)")
        if not input_data.organic_amendments:
            recommendations.append("♻️ Apports organiques réguliers (+0.3 t CO2eq/ha/an séquestration)")
        
        # Benchmark-based
        crop_lower = input_data.crop.lower()
        if crop_lower in self.CROP_BENCHMARKS:
            if emissions_per_ha > self.CROP_BENCHMARKS[crop_lower] * 1.2:
                recommendations.append("🚨 Émissions 20%+ au-dessus moyenne - Audit complet recommandé")
        
        return recommendations[:8]  # Limit to top 8
    
    def _generate_data_quality_note(
        self,
        notes: List[str]
    ) -> str:
        """Generate data quality disclaimer"""
        base_note = (
            "⚠️ LIMITATION: Calcul basé sur facteurs d'émission ADEME 2023. "
            "Émissions réelles varient selon pratiques, équipement, conditions. "
        )

        if notes:
            base_note += "Données manquantes: " + "; ".join(notes) + ". "

        base_note += (
            "PÉRIMÈTRE: Inclut uniquement émissions opérationnelles directes (carburant véhicules ferme, intrants appliqués). "
            "NON INCLUS: transport intrants vers ferme, transport récolte vers marché, "
            "fabrication/amortissement équipement, émissions indirectes (scope 3). "
            "Pour bilan carbone complet certifié, consulter expert agréé."
        )

        return base_note


async def calculate_carbon_footprint_enhanced(
    surface_ha: float,
    crop: str,
    diesel_liters: Optional[float] = None,
    gasoline_liters: Optional[float] = None,
    nitrogen_kg: Optional[float] = None,
    phosphorus_kg: Optional[float] = None,
    potassium_kg: Optional[float] = None,
    organic_fertilizer_kg: Optional[float] = None,
    pesticide_kg: Optional[float] = None,
    cover_crops: bool = False,
    reduced_tillage: bool = False,
    organic_amendments: bool = False
) -> str:
    """
    Async wrapper for calculate carbon footprint tool
    
    Args:
        surface_ha: Surface area in hectares
        crop: Crop type
        diesel_liters: Diesel consumption in liters (optional)
        gasoline_liters: Gasoline consumption in liters (optional)
        nitrogen_kg: Nitrogen fertilizer in kg (optional)
        phosphorus_kg: Phosphorus fertilizer in kg (optional)
        potassium_kg: Potassium fertilizer in kg (optional)
        organic_fertilizer_kg: Organic fertilizer in kg (optional)
        pesticide_kg: Total pesticides in kg active ingredient (optional)
        cover_crops: Whether cover crops are used
        reduced_tillage: Whether reduced/no-till is practiced
        organic_amendments: Whether organic amendments are applied
        
    Returns:
        JSON string with carbon footprint analysis
    """
    try:
        # Validate inputs
        input_data = CarbonFootprintInput(
            surface_ha=surface_ha,
            crop=crop,
            diesel_liters=diesel_liters,
            gasoline_liters=gasoline_liters,
            nitrogen_kg=nitrogen_kg,
            phosphorus_kg=phosphorus_kg,
            potassium_kg=potassium_kg,
            organic_fertilizer_kg=organic_fertilizer_kg,
            pesticide_kg=pesticide_kg,
            cover_crops=cover_crops,
            reduced_tillage=reduced_tillage,
            organic_amendments=organic_amendments
        )
        
        # Execute service
        service = EnhancedCarbonFootprintService()
        result = await service.calculate_carbon_footprint(input_data)
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        # Validation or business logic error
        error_result = CarbonFootprintOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            total_emissions_kg_co2eq=0.0,
            emissions_per_ha=0.0,
            net_emissions_kg_co2eq=0.0,
            data_quality_note="Erreur de validation",
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in calculate_carbon_footprint_enhanced: {e}", exc_info=True)
        error_result = CarbonFootprintOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            total_emissions_kg_co2eq=0.0,
            emissions_per_ha=0.0,
            net_emissions_kg_co2eq=0.0,
            data_quality_note="Erreur système",
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
calculate_carbon_footprint_tool_enhanced = StructuredTool.from_function(
    func=calculate_carbon_footprint_enhanced,
    name="calculate_carbon_footprint",
    description="""Calcule l'empreinte carbone des pratiques agricoles.

⚠️ IMPORTANT: Fournir quantités réelles pour calcul précis.

Entrées (toutes optionnelles mais plus = mieux):
- Carburant: diesel (L), essence (L)
- Engrais: azote (kg N), phosphore (kg P2O5), potassium (kg K2O), organique (kg)
- Pesticides: total matière active (kg)
- Pratiques: couverts végétaux, travail réduit, amendements organiques

Facteurs d'émission ADEME 2023:
- Diesel: 2.68 kg CO2eq/L
- Azote: 5.5 kg CO2eq/kg (production + N2O)
- Pesticides: 15 kg CO2eq/kg matière active

Séquestration potentielle:
- Couverts: 1.5 t CO2eq/ha/an
- Travail réduit: 0.5 t CO2eq/ha/an
- Amendements: 0.3 t CO2eq/ha/an

Retourne:
- Émissions totales et par hectare
- Répartition par source (%)
- Potentiel séquestration
- Comparaison moyenne culture
- Recommandations réduction priorisées
- Note qualité données et limitations

NE REMPLACE PAS bilan carbone certifié.""",
    args_schema=CarbonFootprintInput,
    return_direct=False,
    coroutine=calculate_carbon_footprint_enhanced,
    handle_validation_error=True
)

