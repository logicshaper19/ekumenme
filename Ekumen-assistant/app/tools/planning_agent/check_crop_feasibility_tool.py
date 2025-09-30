"""
Check Crop Feasibility Tool - Single Purpose Tool

Job: Check if a crop is feasible in a given location with climate data.
Input: crop, location, include_alternatives
Output: JSON string with feasibility analysis and alternatives

This tool does ONLY:
- Analyze crop climate requirements vs. actual location climate
- Calculate feasibility score
- Identify limiting factors
- Suggest regional alternatives

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional, ClassVar
from langchain.tools import BaseTool
import logging
import json

logger = logging.getLogger(__name__)


class CheckCropFeasibilityTool(BaseTool):
    """
    Tool: Check crop feasibility for a specific location.

    Job: Analyze if a crop can be grown in a location based on climate requirements.
    Input: crop, location, include_alternatives
    Output: JSON string with feasibility analysis
    """

    name: str = "check_crop_feasibility"
    description: str = "Vérifie la faisabilité d'une culture dans une région donnée avec analyse climatique"

    # Comprehensive crop requirements database
    CROP_REQUIREMENTS: ClassVar[Dict[str, Any]] = {
        "café": {
            "temp_min": 15,
            "temp_max": 30,
            "temp_optimal_min": 18,
            "temp_optimal_max": 24,
            "frost_tolerance": False,
            "growing_season_days": 365,
            "climate": "tropical",
            "hardiness_zone": "10-11",
            "rainfall_mm_year": 1500,
            "alternatives_temperate": [
                {"name": "figuier", "hardiness_zone": "7-10", "description": "Arbre fruitier méditerranéen, résistant jusqu'à -12°C"},
                {"name": "amandier", "hardiness_zone": "7-9", "description": "Arbre fruitier rustique, floraison précoce"},
                {"name": "vigne", "hardiness_zone": "6-9", "description": "Nombreux cépages adaptés au climat francilien"},
                {"name": "noisetier", "hardiness_zone": "4-9", "description": "Très rustique, production de noisettes"},
                {"name": "kiwi", "hardiness_zone": "7-9", "description": "Actinidia, résiste au froid, production généreuse"}
            ]
        },
        "blé": {
            "temp_min": -10,
            "temp_max": 30,
            "temp_optimal_min": 15,
            "temp_optimal_max": 25,
            "frost_tolerance": True,
            "growing_season_days": 240,
            "climate": "temperate",
            "hardiness_zone": "3-8",
            "rainfall_mm_year": 600,
            "alternatives_temperate": []
        },
        "maïs": {
            "temp_min": 10,
            "temp_max": 35,
            "temp_optimal_min": 20,
            "temp_optimal_max": 30,
            "frost_tolerance": False,
            "growing_season_days": 120,
            "climate": "temperate_warm",
            "hardiness_zone": "5-10",
            "rainfall_mm_year": 500,
            "alternatives_temperate": []
        },
        "tomate": {
            "temp_min": 10,
            "temp_max": 35,
            "temp_optimal_min": 18,
            "temp_optimal_max": 27,
            "frost_tolerance": False,
            "growing_season_days": 90,
            "climate": "temperate_warm",
            "hardiness_zone": "9-11",
            "rainfall_mm_year": 400,
            "alternatives_temperate": []
        },
        "vigne": {
            "temp_min": -15,
            "temp_max": 35,
            "temp_optimal_min": 15,
            "temp_optimal_max": 30,
            "frost_tolerance": True,
            "growing_season_days": 180,
            "climate": "temperate",
            "hardiness_zone": "6-9",
            "rainfall_mm_year": 500,
            "alternatives_temperate": []
        }
    }

    # French location climate data (simplified)
    LOCATION_CLIMATE: ClassVar[Dict[str, Any]] = {
        "dourdan": {
            "department": "Essonne",
            "region": "Île-de-France",
            "hardiness_zone": "8a",
            "temp_min_annual": -5,
            "temp_max_annual": 35,
            "frost_days": 40,
            "growing_season_days": 200,
            "rainfall_mm_year": 600
        },
        "paris": {
            "department": "Paris",
            "region": "Île-de-France",
            "hardiness_zone": "8b",
            "temp_min_annual": -3,
            "temp_max_annual": 35,
            "frost_days": 30,
            "growing_season_days": 210,
            "rainfall_mm_year": 650
        },
        "normandie": {
            "department": "Calvados",
            "region": "Normandie",
            "hardiness_zone": "8a",
            "temp_min_annual": -5,
            "temp_max_annual": 30,
            "frost_days": 50,
            "growing_season_days": 190,
            "rainfall_mm_year": 800
        },
        "lyon": {
            "department": "Rhône",
            "region": "Auvergne-Rhône-Alpes",
            "hardiness_zone": "8a",
            "temp_min_annual": -7,
            "temp_max_annual": 35,
            "frost_days": 60,
            "growing_season_days": 200,
            "rainfall_mm_year": 800
        },
        "marseille": {
            "department": "Bouches-du-Rhône",
            "region": "Provence-Alpes-Côte d'Azur",
            "hardiness_zone": "9a",
            "temp_min_annual": -2,
            "temp_max_annual": 38,
            "frost_days": 10,
            "growing_season_days": 250,
            "rainfall_mm_year": 500
        }
    }
    
    def _run(
        self, 
        crop: str,
        location: str,
        include_alternatives: bool = True,
        **kwargs
    ) -> str:
        """
        Check crop feasibility for a location.
        
        Args:
            crop: Crop name (e.g., "café", "blé", "maïs")
            location: Location name (e.g., "Dourdan", "Paris")
            include_alternatives: Whether to include alternative crop suggestions
        
        Returns:
            JSON string with feasibility analysis
        """
        try:
            crop_lower = crop.lower()
            location_lower = location.lower()
            
            # Get crop requirements
            requirements = self.CROP_REQUIREMENTS.get(crop_lower)
            if not requirements:
                return json.dumps({
                    "crop": crop,
                    "location": location,
                    "error": f"Crop '{crop}' not found in database",
                    "is_feasible": None,
                    "message": "Culture non reconnue. Cultures disponibles: " + ", ".join(self.CROP_REQUIREMENTS.keys())
                }, ensure_ascii=False)
            
            # Get location climate data
            climate_data = self._get_location_climate(location_lower)
            
            # Analyze feasibility
            feasibility_analysis = self._analyze_feasibility(requirements, climate_data)
            
            # Get alternatives if needed
            alternatives = []
            if include_alternatives and not feasibility_analysis["is_feasible"]:
                alternatives = self._get_regional_alternatives(crop_lower, requirements, climate_data)
            
            result = {
                "crop": crop,
                "location": location,
                "is_feasible": feasibility_analysis["is_feasible"],
                "feasibility_score": feasibility_analysis["score"],
                "limiting_factors": feasibility_analysis["limitations"],
                "climate_data": {
                    "location_details": climate_data,
                    "temp_min_annual": climate_data["temp_min_annual"],
                    "temp_max_annual": climate_data["temp_max_annual"],
                    "frost_days": climate_data["frost_days"],
                    "growing_season_length": climate_data["growing_season_days"],
                    "hardiness_zone": climate_data["hardiness_zone"]
                },
                "crop_requirements": {
                    "temp_min": requirements["temp_min"],
                    "temp_max": requirements["temp_max"],
                    "frost_tolerance": requirements["frost_tolerance"],
                    "climate_type": requirements["climate"],
                    "hardiness_zone": requirements["hardiness_zone"]
                },
                "alternatives": alternatives,
                "indoor_cultivation": feasibility_analysis["indoor_possible"],
                "recommendations": feasibility_analysis["recommendations"],
                "sources": [
                    {
                        "title": f"Base de données climatique - {location.title()}",
                        "url": "#climate-database",
                        "snippet": f"Zone de rusticité: {climate_data.get('hardiness_zone', 'N/A')}, Température: {climate_data.get('temp_min_annual', 'N/A')}-{climate_data.get('temp_max_annual', 'N/A')}°C, Saison de croissance: {climate_data.get('growing_season_days', 'N/A')} jours",
                        "relevance": 1.0,
                        "type": "database"
                    },
                    {
                        "title": f"Exigences culturales - {crop.title()}",
                        "url": "#crop-requirements",
                        "snippet": f"Température optimale: {requirements.get('temp_optimal_min', 'N/A')}-{requirements.get('temp_optimal_max', 'N/A')}°C, Climat: {requirements.get('climate', 'N/A')}, Zone de rusticité: {requirements.get('hardiness_zone', 'N/A')}",
                        "relevance": 1.0,
                        "type": "database"
                    }
                ]
            }

            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error checking crop feasibility: {e}")
            return json.dumps({
                "crop": crop,
                "location": location,
                "error": str(e),
                "is_feasible": None
            }, ensure_ascii=False)
    
    def _get_location_climate(self, location: str) -> Dict[str, Any]:
        """Get climate data for a location"""
        # Try direct match
        if location in self.LOCATION_CLIMATE:
            return self.LOCATION_CLIMATE[location]
        
        # Try partial match
        for loc_key, loc_data in self.LOCATION_CLIMATE.items():
            if loc_key in location or location in loc_key:
                return loc_data
        
        # Default to Paris climate if not found
        logger.warning(f"Location '{location}' not found, using Paris climate as default")
        return self.LOCATION_CLIMATE["paris"]
    
    def _analyze_feasibility(self, requirements: Dict[str, Any], climate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if crop is feasible given climate"""
        limitations = []
        score = 10.0

        # Check minimum temperature
        if climate["temp_min_annual"] < requirements["temp_min"]:
            limitations.append(f"Température minimale trop basse ({climate['temp_min_annual']}°C < {requirements['temp_min']}°C)")
            temp_diff = requirements["temp_min"] - climate["temp_min_annual"]
            if temp_diff > 20:
                score -= 4.0  # Very incompatible
            elif temp_diff > 10:
                score -= 3.0  # Incompatible
            else:
                score -= 1.5  # Slightly incompatible

        # Check frost tolerance
        if not requirements["frost_tolerance"] and climate["frost_days"] > 0:
            limitations.append(f"Gel fréquent ({climate['frost_days']} jours/an) et culture non rustique")
            if climate["frost_days"] > 30:
                score -= 3.0  # Many frost days
            elif climate["frost_days"] > 10:
                score -= 2.0  # Some frost days
            else:
                score -= 1.0  # Few frost days

        # Check growing season
        if climate["growing_season_days"] < requirements["growing_season_days"]:
            limitations.append(f"Saison de croissance trop courte ({climate['growing_season_days']} < {requirements['growing_season_days']} jours)")
            season_diff = requirements["growing_season_days"] - climate["growing_season_days"]
            if season_diff > 100:
                score -= 3.0  # Much too short
            elif season_diff > 50:
                score -= 2.0  # Too short
            else:
                score -= 1.0  # Slightly short

        # Determine if feasible
        is_feasible = score >= 7.0
        indoor_possible = score >= 3.0 and score < 7.0  # Can try indoors/greenhouse if score is moderate

        recommendations = []
        if not is_feasible and indoor_possible:
            recommendations.append("Culture en serre chauffée ou en pot à l'intérieur possible")
            recommendations.append("Nécessite protection contre le gel et températures contrôlées")
        elif not is_feasible:
            recommendations.append("Culture non recommandée même en intérieur pour ce climat")
            recommendations.append("Considérez les alternatives adaptées à votre zone climatique")
        else:
            recommendations.append("Culture possible en pleine terre")
            recommendations.append(f"Zone de rusticité compatible: {climate['hardiness_zone']}")
        
        return {
            "is_feasible": is_feasible,
            "score": round(score, 1),
            "limitations": limitations,
            "indoor_possible": indoor_possible,
            "recommendations": recommendations
        }
    
    def _get_regional_alternatives(self, crop: str, requirements: Dict[str, Any], climate: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get alternative crops suitable for the region"""
        alternatives = []
        
        # Get predefined alternatives for this crop
        if "alternatives_temperate" in requirements and requirements["alternatives_temperate"]:
            alternatives.extend(requirements["alternatives_temperate"])
        
        # Add general alternatives based on climate
        if climate["hardiness_zone"] in ["8a", "8b", "9a"]:
            general_alternatives = [
                {"name": "pommier", "hardiness_zone": "4-8", "description": "Nombreuses variétés adaptées, production fiable"},
                {"name": "poirier", "hardiness_zone": "4-8", "description": "Rustique, bonne adaptation au climat tempéré"},
                {"name": "cerisier", "hardiness_zone": "5-8", "description": "Floraison spectaculaire, fruits appréciés"}
            ]
            # Add only if not already in alternatives
            for alt in general_alternatives:
                if not any(a["name"] == alt["name"] for a in alternatives):
                    alternatives.append(alt)
        
        return alternatives[:5]  # Limit to 5 alternatives
    
    async def _arun(self, *args, **kwargs):
        """Async version - not implemented"""
        raise NotImplementedError("Async version not implemented")

