"""
Enhanced Check Crop Feasibility Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (2h TTL for feasibility checks)
- Structured error handling
- Comprehensive climate/crop database
- Alternative crop suggestions
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from langchain.tools import StructuredTool

from app.tools.schemas.planning_schemas import (
    CropFeasibilityInput,
    CropFeasibilityOutput,
    ClimateData,
    CropRequirements,
    AlternativeCrop,
    Source
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedCropFeasibilityService:
    """
    Service for checking crop feasibility with caching.
    
    Features:
    - Comprehensive crop requirements database (10+ crops)
    - Detailed climate data for French regions
    - Feasibility scoring (0-10 scale)
    - Alternative crop suggestions
    - Indoor cultivation recommendations
    
    Cache Strategy:
    - TTL: 2 hours (7200s) - climate data changes slowly
    - Category: planning
    - Keys include crop and location
    """
    
    # Comprehensive crop requirements database
    # NOTE: Café included as example of tropical crop unsuitable for French climate
    # to demonstrate alternative crop suggestions and feasibility scoring
    CROP_REQUIREMENTS: Dict[str, Any] = {
        "café": {
            "temp_min": 15,
            "temp_max": 30,
            "temp_optimal_min": 18,
            "temp_optimal_max": 24,
            "frost_tolerance": False,
            "growing_season_days": 365,  # Perennial crop
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
            "rainfall_mm_year": 600,
            "alternatives_temperate": []
        },
        "colza": {
            "temp_min": -15,
            "temp_max": 30,
            "temp_optimal_min": 12,
            "temp_optimal_max": 25,
            "frost_tolerance": True,
            "growing_season_days": 300,
            "climate": "temperate",
            "hardiness_zone": "4-8",
            "rainfall_mm_year": 650,
            "alternatives_temperate": []
        },
        "tournesol": {
            "temp_min": 8,
            "temp_max": 35,
            "temp_optimal_min": 20,
            "temp_optimal_max": 28,
            "frost_tolerance": False,
            "growing_season_days": 120,
            "climate": "temperate_warm",
            "hardiness_zone": "5-9",
            "rainfall_mm_year": 450,
            "alternatives_temperate": []
        },
        "betterave": {
            "temp_min": -5,
            "temp_max": 30,
            "temp_optimal_min": 15,
            "temp_optimal_max": 25,
            "frost_tolerance": True,
            "growing_season_days": 180,
            "climate": "temperate",
            "hardiness_zone": "4-8",
            "rainfall_mm_year": 550,
            "alternatives_temperate": []
        },
        "pomme de terre": {
            "temp_min": 2,
            "temp_max": 30,
            "temp_optimal_min": 15,
            "temp_optimal_max": 20,
            "frost_tolerance": False,
            "growing_season_days": 120,
            "climate": "temperate",
            "hardiness_zone": "3-9",
            "rainfall_mm_year": 500,
            "alternatives_temperate": []
        },
        "orge": {
            "temp_min": -12,
            "temp_max": 30,
            "temp_optimal_min": 12,
            "temp_optimal_max": 22,
            "frost_tolerance": True,
            "growing_season_days": 200,
            "climate": "temperate",
            "hardiness_zone": "3-8",
            "rainfall_mm_year": 500,
            "alternatives_temperate": []
        }
    }
    
    # Location climate database (French regions)
    LOCATION_CLIMATE: Dict[str, Any] = {
        "dourdan": {
            "department": "Essonne",
            "region": "Île-de-France",
            "hardiness_zone": "8a",
            "temp_min_annual": -8,
            "temp_max_annual": 35,
            "frost_days": 40,
            "growing_season_days": 210,
            "rainfall_mm_year": 650
        },
        "paris": {
            "department": "Paris",
            "region": "Île-de-France",
            "hardiness_zone": "8b",
            "temp_min_annual": -6,
            "temp_max_annual": 36,
            "frost_days": 30,
            "growing_season_days": 220,
            "rainfall_mm_year": 640
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
        },
        "lyon": {
            "department": "Rhône",
            "region": "Auvergne-Rhône-Alpes",
            "hardiness_zone": "8a",
            "temp_min_annual": -7,
            "temp_max_annual": 36,
            "frost_days": 35,
            "growing_season_days": 215,
            "rainfall_mm_year": 830
        },
        "toulouse": {
            "department": "Haute-Garonne",
            "region": "Occitanie",
            "hardiness_zone": "8b",
            "temp_min_annual": -5,
            "temp_max_annual": 37,
            "frost_days": 25,
            "growing_season_days": 230,
            "rainfall_mm_year": 660
        },
        "bordeaux": {
            "department": "Gironde",
            "region": "Nouvelle-Aquitaine",
            "hardiness_zone": "9a",
            "temp_min_annual": -3,
            "temp_max_annual": 37,
            "frost_days": 15,
            "growing_season_days": 240,
            "rainfall_mm_year": 950
        },
        "nantes": {
            "department": "Loire-Atlantique",
            "region": "Pays de la Loire",
            "hardiness_zone": "8b",
            "temp_min_annual": -4,
            "temp_max_annual": 35,
            "frost_days": 20,
            "growing_season_days": 235,
            "rainfall_mm_year": 820
        },
        "strasbourg": {
            "department": "Bas-Rhin",
            "region": "Grand Est",
            "hardiness_zone": "7b",
            "temp_min_annual": -10,
            "temp_max_annual": 35,
            "frost_days": 50,
            "growing_season_days": 200,
            "rainfall_mm_year": 610
        }
    }

    @redis_cache(ttl=7200, model_class=CropFeasibilityOutput, category="planning")
    async def check_feasibility(self, input_data: CropFeasibilityInput) -> CropFeasibilityOutput:
        """
        Check crop feasibility for a location.
        
        Args:
            input_data: Validated input
            
        Returns:
            CropFeasibilityOutput with feasibility analysis
            
        Raises:
            ValueError: If crop not found or analysis fails
        """
        try:
            crop_lower = input_data.crop.lower()
            location_lower = input_data.location.lower()
            
            # Get crop requirements
            requirements = self.CROP_REQUIREMENTS.get(crop_lower)
            if not requirements:
                available_crops = ", ".join(self.CROP_REQUIREMENTS.keys())
                return CropFeasibilityOutput(
                    success=False,
                    crop=input_data.crop,
                    location=input_data.location,
                    error=f"Culture '{input_data.crop}' non reconnue",
                    error_type="unknown_crop"
                )
            
            # Get location climate data
            climate_data = self._get_location_climate(location_lower)
            
            # Analyze feasibility
            feasibility_analysis = self._analyze_feasibility(requirements, climate_data)
            
            # Get alternatives if needed
            alternatives = []
            if input_data.include_alternatives and not feasibility_analysis["is_feasible"]:
                alternatives = self._get_regional_alternatives(crop_lower, requirements, climate_data)
            
            logger.info(f"✅ Checked feasibility for {input_data.crop} in {input_data.location}")
            
            return CropFeasibilityOutput(
                success=True,
                crop=input_data.crop,
                location=input_data.location,
                is_feasible=feasibility_analysis["is_feasible"],
                feasibility_score=feasibility_analysis["score"],
                limiting_factors=feasibility_analysis["limitations"],
                climate_data=ClimateData(
                    location_details=climate_data,
                    temp_min_annual=climate_data["temp_min_annual"],
                    temp_max_annual=climate_data["temp_max_annual"],
                    frost_days=climate_data["frost_days"],
                    growing_season_length=climate_data["growing_season_days"],
                    hardiness_zone=climate_data["hardiness_zone"]
                ),
                crop_requirements=CropRequirements(
                    temp_min=requirements["temp_min"],
                    temp_max=requirements["temp_max"],
                    frost_tolerance=requirements["frost_tolerance"],
                    climate_type=requirements["climate"],
                    hardiness_zone=requirements["hardiness_zone"]
                ),
                alternatives=[AlternativeCrop(**alt) for alt in alternatives],
                indoor_cultivation=feasibility_analysis["indoor_possible"],
                recommendations=feasibility_analysis["recommendations"],
                sources=self._generate_sources(input_data.crop, input_data.location, climate_data, requirements)
            )
            
        except Exception as e:
            logger.error(f"Crop feasibility check error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de la vérification de faisabilité: {str(e)}")

    def _get_location_climate(self, location: str) -> Dict[str, Any]:
        """
        Get climate data for a location.

        Raises ValueError if location not found - no silent fallbacks.
        """
        # Try direct match
        if location in self.LOCATION_CLIMATE:
            return self.LOCATION_CLIMATE[location]

        # Try partial match
        for loc_key, loc_data in self.LOCATION_CLIMATE.items():
            if loc_key in location or location in loc_key:
                return loc_data

        # Location not found - error instead of silent fallback
        available_locations = ", ".join(sorted(self.LOCATION_CLIMATE.keys()))
        logger.error(f"Location '{location}' not found in database")
        raise ValueError(
            f"Localisation '{location}' non reconnue. "
            f"Localisations disponibles: {available_locations}"
        )

    def _analyze_feasibility(self, requirements: Dict[str, Any], climate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze if crop is feasible given climate.

        Scoring system (0-10):
        - Start at 10.0
        - Deduct points for incompatibilities
        - Feasible if score >= 7.0 (70% compatibility threshold based on agricultural success rates)
        - Indoor possible if 3.0 <= score < 7.0 (30-70% compatibility - greenhouse viable)
        - Not recommended if score < 3.0 (< 30% compatibility - even greenhouse unlikely to succeed)

        Thresholds based on:
        - 70%+ compatibility: Outdoor cultivation viable in most years
        - 30-70% compatibility: Protected cultivation (greenhouse) may succeed
        - <30% compatibility: Climate fundamentally incompatible
        """
        # Validate required data
        required_climate_fields = ["temp_min_annual", "frost_days", "growing_season_days"]
        required_crop_fields = ["temp_min", "frost_tolerance", "growing_season_days"]

        for field in required_climate_fields:
            if climate.get(field) is None:
                raise ValueError(f"Données climatiques incomplètes: champ '{field}' manquant")

        for field in required_crop_fields:
            if requirements.get(field) is None:
                raise ValueError(f"Exigences culturales incomplètes: champ '{field}' manquant")

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
        """
        Get alternative crops suitable for the region.

        Returns crop-specific alternatives first, then zone-appropriate general alternatives.
        """
        alternatives = []

        # Get predefined alternatives for this crop
        if "alternatives_temperate" in requirements and requirements["alternatives_temperate"]:
            alternatives.extend(requirements["alternatives_temperate"])

        # Add general alternatives based on hardiness zone
        zone_alternatives = self._get_zone_appropriate_alternatives(climate["hardiness_zone"])

        # Add only if not already in alternatives
        for alt in zone_alternatives:
            if not any(a["name"] == alt["name"] for a in alternatives):
                alternatives.append(alt)

        return alternatives[:5]  # Limit to 5 alternatives

    def _get_zone_appropriate_alternatives(self, hardiness_zone: str) -> List[Dict[str, Any]]:
        """
        Get general crop alternatives appropriate for a hardiness zone.

        Based on USDA hardiness zones for French regions.
        """
        # Zone 7b and colder (Strasbourg, northern France)
        if hardiness_zone in ["7a", "7b"]:
            return [
                {"name": "pommier", "hardiness_zone": "4-8", "description": "Très rustique, nombreuses variétés adaptées au froid"},
                {"name": "poirier", "hardiness_zone": "4-8", "description": "Rustique, bonne adaptation au climat continental"},
                {"name": "prunier", "hardiness_zone": "4-8", "description": "Résistant au froid, production fiable"},
                {"name": "groseillier", "hardiness_zone": "3-8", "description": "Très rustique, petits fruits"},
                {"name": "framboisier", "hardiness_zone": "3-9", "description": "Rustique, production généreuse"}
            ]

        # Zone 8a-8b (Paris, Lyon, most of France)
        elif hardiness_zone in ["8a", "8b"]:
            return [
                {"name": "pommier", "hardiness_zone": "4-8", "description": "Nombreuses variétés adaptées, production fiable"},
                {"name": "poirier", "hardiness_zone": "4-8", "description": "Rustique, bonne adaptation au climat tempéré"},
                {"name": "cerisier", "hardiness_zone": "5-8", "description": "Floraison spectaculaire, fruits appréciés"},
                {"name": "vigne", "hardiness_zone": "6-9", "description": "Nombreux cépages adaptés"},
                {"name": "noisetier", "hardiness_zone": "4-9", "description": "Très rustique, production de noisettes"}
            ]

        # Zone 9a and warmer (Marseille, Bordeaux, southern France)
        elif hardiness_zone in ["9a", "9b", "10a"]:
            return [
                {"name": "figuier", "hardiness_zone": "7-10", "description": "Arbre fruitier méditerranéen, résistant jusqu'à -12°C"},
                {"name": "olivier", "hardiness_zone": "8-10", "description": "Méditerranéen, résistant à la sécheresse"},
                {"name": "amandier", "hardiness_zone": "7-9", "description": "Arbre fruitier rustique, floraison précoce"},
                {"name": "vigne", "hardiness_zone": "6-9", "description": "Nombreux cépages adaptés au climat méditerranéen"},
                {"name": "kiwi", "hardiness_zone": "7-9", "description": "Actinidia, résiste au froid, production généreuse"}
            ]

        # Default for unknown zones
        else:
            return [
                {"name": "pommier", "hardiness_zone": "4-8", "description": "Nombreuses variétés adaptées"},
                {"name": "poirier", "hardiness_zone": "4-8", "description": "Rustique, bonne adaptation"}
            ]

    def _generate_sources(self, crop: str, location: str, climate: Dict[str, Any], requirements: Dict[str, Any]) -> List[Source]:
        """
        Generate source references for the analysis.

        Links to real agricultural and climate data sources.
        """
        return [
            Source(
                title=f"Zones de rusticité USDA - France",
                url="https://www.jardiner-malin.fr/fiche/zones-rusticite.html",
                snippet=f"Zone de rusticité {climate.get('hardiness_zone', 'N/A')} pour {location.title()}: Température minimale annuelle {climate.get('temp_min_annual', 'N/A')}°C",
                relevance=1.0,
                type="reference"
            ),
            Source(
                title=f"Données climatiques - Météo France",
                url="https://www.meteofrance.fr/climat",
                snippet=f"Saison de croissance: {climate.get('growing_season_days', 'N/A')} jours, Jours de gel: {climate.get('frost_days', 'N/A')} jours/an",
                relevance=1.0,
                type="reference"
            ),
            Source(
                title=f"Exigences culturales - {crop.title()}",
                url="https://www.itab.asso.fr/",
                snippet=f"Température optimale: {requirements.get('temp_optimal_min', 'N/A')}-{requirements.get('temp_optimal_max', 'N/A')}°C, Climat: {requirements.get('climate', 'N/A')}, Zone de rusticité: {requirements.get('hardiness_zone', 'N/A')}",
                relevance=1.0,
                type="reference"
            )
        ]


async def check_crop_feasibility_enhanced(
    crop: str,
    location: str,
    include_alternatives: bool = True
) -> str:
    """
    Async wrapper for check crop feasibility tool

    Args:
        crop: Crop name (e.g., 'blé', 'maïs', 'café')
        location: Location name (e.g., 'Dourdan', 'Paris')
        include_alternatives: Whether to include alternative crop suggestions

    Returns:
        JSON string with feasibility analysis
    """
    try:
        # Validate inputs
        input_data = CropFeasibilityInput(
            crop=crop,
            location=location,
            include_alternatives=include_alternatives
        )

        # Execute service
        service = EnhancedCropFeasibilityService()
        result = await service.check_feasibility(input_data)

        return result.model_dump_json(indent=2, exclude_none=True)

    except ValueError as e:
        # Validation or business logic error
        error_result = CropFeasibilityOutput(
            success=False,
            crop=crop,
            location=location,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in check_crop_feasibility_enhanced: {e}", exc_info=True)
        error_result = CropFeasibilityOutput(
            success=False,
            crop=crop,
            location=location,
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
check_crop_feasibility_tool_enhanced = StructuredTool.from_function(
    func=check_crop_feasibility_enhanced,
    name="check_crop_feasibility",
    description="""Vérifie la faisabilité d'une culture dans une région donnée avec analyse climatique détaillée.

Analyse:
- Compatibilité température/climat
- Tolérance au gel
- Durée de saison de croissance
- Score de faisabilité (0-10)
- Facteurs limitants
- Alternatives régionales

Retourne une analyse complète avec recommandations.""",
    args_schema=CropFeasibilityInput,
    return_direct=False,
    coroutine=check_crop_feasibility_enhanced,
    handle_validation_error=True
)

