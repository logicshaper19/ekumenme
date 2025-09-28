"""
Calculate Carbon Footprint Tool - Single Purpose Tool

Job: Calculate carbon footprint for agricultural practices and operations.
Input: practice_type, inputs_used, area_ha, duration
Output: JSON string with carbon footprint analysis

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
class CarbonFootprintComponent:
    """Structured carbon footprint component."""
    component_type: str
    emission_source: str
    co2_equivalent: float
    percentage: float
    reduction_potential: float

class CalculateCarbonFootprintTool(BaseTool):
    """
    Tool: Calculate carbon footprint for agricultural practices and operations.
    
    Job: Take agricultural practice data and calculate carbon footprint.
    Input: practice_type, inputs_used, area_ha, duration
    Output: JSON string with carbon footprint analysis
    """
    
    name: str = "calculate_carbon_footprint_tool"
    description: str = "Calcule l'empreinte carbone des pratiques agricoles"
    
    def _run(
        self,
        practice_type: str,
        inputs_used: List[str] = None,
        area_ha: float = 1.0,
        duration_days: int = 1,
        **kwargs
    ) -> str:
        """
        Calculate carbon footprint for agricultural practices and operations.
        
        Args:
            practice_type: Type of agricultural practice (spraying, fertilization, etc.)
            inputs_used: List of inputs used (fertilizers, pesticides, fuel, etc.)
            area_ha: Area in hectares
            duration_days: Duration in days
        """
        try:
            # Get carbon footprint database
            carbon_database = self._get_carbon_database()
            
            # Calculate carbon footprint components
            carbon_components = self._calculate_carbon_components(practice_type, inputs_used or [], area_ha, duration_days, carbon_database)
            
            # Calculate total carbon footprint
            total_carbon_footprint = self._calculate_total_carbon_footprint(carbon_components)
            
            # Calculate carbon intensity
            carbon_intensity = self._calculate_carbon_intensity(total_carbon_footprint, area_ha)
            
            # Generate carbon reduction recommendations
            reduction_recommendations = self._generate_reduction_recommendations(carbon_components)
            
            result = {
                "practice_type": practice_type,
                "inputs_used": inputs_used or [],
                "area_ha": area_ha,
                "duration_days": duration_days,
                "carbon_components": [asdict(component) for component in carbon_components],
                "total_carbon_footprint": total_carbon_footprint,
                "carbon_intensity": carbon_intensity,
                "reduction_recommendations": reduction_recommendations
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Calculate carbon footprint error: {e}")
            return json.dumps({"error": f"Erreur lors du calcul de l'empreinte carbone: {str(e)}"})
    
    def _get_carbon_database(self) -> Dict[str, Any]:
        """Get carbon footprint database with emission factors."""
        carbon_database = {
            "fertilizers": {
                "azote": {"co2_per_kg": 4.2, "reduction_potential": 0.3},
                "phosphore": {"co2_per_kg": 1.2, "reduction_potential": 0.2},
                "potassium": {"co2_per_kg": 0.8, "reduction_potential": 0.1},
                "compost": {"co2_per_kg": 0.3, "reduction_potential": 0.5}
            },
            "pesticides": {
                "herbicide": {"co2_per_kg": 8.5, "reduction_potential": 0.4},
                "insecticide": {"co2_per_kg": 12.3, "reduction_potential": 0.5},
                "fongicide": {"co2_per_kg": 6.7, "reduction_potential": 0.3}
            },
            "fuel": {
                "diesel": {"co2_per_liter": 2.68, "reduction_potential": 0.2},
                "essence": {"co2_per_liter": 2.31, "reduction_potential": 0.2}
            },
            "machinery": {
                "tracteur": {"co2_per_hour": 15.2, "reduction_potential": 0.3},
                "moissonneuse": {"co2_per_hour": 25.8, "reduction_potential": 0.4},
                "pulvérisateur": {"co2_per_hour": 8.5, "reduction_potential": 0.2}
            },
            "practices": {
                "spraying": {"co2_per_ha": 12.5, "reduction_potential": 0.3},
                "fertilization": {"co2_per_ha": 18.7, "reduction_potential": 0.4},
                "irrigation": {"co2_per_ha": 8.3, "reduction_potential": 0.2},
                "harvesting": {"co2_per_ha": 22.1, "reduction_potential": 0.3}
            }
        }
        
        return carbon_database
    
    def _calculate_carbon_components(self, practice_type: str, inputs_used: List[str], area_ha: float, duration_days: int, carbon_database: Dict[str, Any]) -> List[CarbonFootprintComponent]:
        """Calculate carbon footprint components."""
        components = []
        
        # Calculate practice-specific emissions
        if practice_type in carbon_database["practices"]:
            practice_data = carbon_database["practices"][practice_type]
            co2_equivalent = practice_data["co2_per_ha"] * area_ha
            component = CarbonFootprintComponent(
                component_type="practice",
                emission_source=practice_type,
                co2_equivalent=co2_equivalent,
                percentage=0.0,  # Will be calculated later
                reduction_potential=practice_data["reduction_potential"]
            )
            components.append(component)
        
        # Calculate input-specific emissions
        for input_type in inputs_used:
            input_lower = input_type.lower()
            
            # Check fertilizers
            if input_lower in carbon_database["fertilizers"]:
                fertilizer_data = carbon_database["fertilizers"][input_lower]
                co2_equivalent = fertilizer_data["co2_per_kg"] * area_ha * 0.1  # Assuming 0.1 kg/ha
                component = CarbonFootprintComponent(
                    component_type="fertilizer",
                    emission_source=input_type,
                    co2_equivalent=co2_equivalent,
                    percentage=0.0,  # Will be calculated later
                    reduction_potential=fertilizer_data["reduction_potential"]
                )
                components.append(component)
            
            # Check pesticides
            elif input_lower in carbon_database["pesticides"]:
                pesticide_data = carbon_database["pesticides"][input_lower]
                co2_equivalent = pesticide_data["co2_per_kg"] * area_ha * 0.05  # Assuming 0.05 kg/ha
                component = CarbonFootprintComponent(
                    component_type="pesticide",
                    emission_source=input_type,
                    co2_equivalent=co2_equivalent,
                    percentage=0.0,  # Will be calculated later
                    reduction_potential=pesticide_data["reduction_potential"]
                )
                components.append(component)
            
            # Check fuel
            elif input_lower in carbon_database["fuel"]:
                fuel_data = carbon_database["fuel"][input_lower]
                co2_equivalent = fuel_data["co2_per_liter"] * area_ha * 2.0  # Assuming 2L/ha
                component = CarbonFootprintComponent(
                    component_type="fuel",
                    emission_source=input_type,
                    co2_equivalent=co2_equivalent,
                    percentage=0.0,  # Will be calculated later
                    reduction_potential=fuel_data["reduction_potential"]
                )
                components.append(component)
        
        # Calculate percentages
        total_emissions = sum(component.co2_equivalent for component in components)
        for component in components:
            component.percentage = (component.co2_equivalent / total_emissions * 100) if total_emissions > 0 else 0
        
        return components
    
    def _calculate_total_carbon_footprint(self, carbon_components: List[CarbonFootprintComponent]) -> float:
        """Calculate total carbon footprint."""
        return sum(component.co2_equivalent for component in carbon_components)
    
    def _calculate_carbon_intensity(self, total_carbon_footprint: float, area_ha: float) -> float:
        """Calculate carbon intensity per hectare."""
        return total_carbon_footprint / area_ha if area_ha > 0 else 0
    
    def _generate_reduction_recommendations(self, carbon_components: List[CarbonFootprintComponent]) -> List[str]:
        """Generate carbon reduction recommendations."""
        recommendations = []
        
        # Sort components by emission level
        sorted_components = sorted(carbon_components, key=lambda x: x.co2_equivalent, reverse=True)
        
        for component in sorted_components:
            if component.co2_equivalent > 10:  # High emission component
                if component.component_type == "fertilizer":
                    recommendations.append(f"🌱 Optimiser l'usage des engrais {component.emission_source} (réduction potentielle: {component.reduction_potential:.0%})")
                elif component.component_type == "pesticide":
                    recommendations.append(f"🐛 Réduire l'usage des pesticides {component.emission_source} (réduction potentielle: {component.reduction_potential:.0%})")
                elif component.component_type == "fuel":
                    recommendations.append(f"⛽ Optimiser la consommation de carburant {component.emission_source} (réduction potentielle: {component.reduction_potential:.0%})")
                elif component.component_type == "practice":
                    recommendations.append(f"🔧 Améliorer les pratiques {component.emission_source} (réduction potentielle: {component.reduction_potential:.0%})")
        
        # General recommendations
        recommendations.append("🌿 Considérer l'agriculture biologique pour réduire l'empreinte carbone")
        recommendations.append("♻️ Implémenter des pratiques de circularité (compost, rotation)")
        recommendations.append("🌱 Utiliser des variétés résistantes pour réduire les intrants")
        
        return recommendations
