"""
Enhanced Calculate Evapotranspiration Tool - With Caching and Type Safety

Enhancements:
- Pydantic schemas for type safety
- Redis + memory caching
- Structured error handling
- Async support
- Category-specific cache
- Penman-Monteith FAO-56 method
- Simple 4-stage Kc lookup (FAO-56 standard)

Architecture:
- Uses simple 4-stage crop coefficients (semis, croissance, floraison, maturation)
- NO database queries, NO BBCH service calls
- BBCH → simple stage conversion happens in input validation only
"""

from typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
import logging
import json
import math
from datetime import datetime
from pydantic import ValidationError

from app.tools.schemas.evapotranspiration_schemas import (
    EvapotranspirationInput,
    EvapotranspirationOutput,
    DailyEvapotranspiration,
    WaterBalance,
    IrrigationRecommendation,
    CROP_COEFFICIENTS,
)
from app.tools.exceptions import (
    WeatherValidationError,
    WeatherDataError
)
from app.core.cache import redis_cache
from app.services.weather import (
    SolarRadiationEstimator,
    PenmanMonteithET0
)

logger = logging.getLogger(__name__)


class EvapotranspirationService:
    """Service for calculating evapotranspiration with caching"""
    
    @redis_cache(
        ttl=3600,  # 1 hour cache (derived data from weather)
        model_class=EvapotranspirationOutput,
        category="weather"
    )
    async def calculate_evapotranspiration(
        self,
        weather_data_json: str,
        crop_type: Optional[str] = None,
        crop_stage: Optional[str] = None
    ) -> EvapotranspirationOutput:
        """
        Calculate evapotranspiration from weather data
        
        Uses 1-hour cache since ET is derived from weather data
        and doesn't change as frequently as raw weather data.
        
        Args:
            weather_data_json: JSON string from weather tool
            crop_type: Optional crop type for crop-specific calculations
            crop_stage: Optional crop development stage
            
        Returns:
            EvapotranspirationOutput with ET calculations and irrigation recommendations
            
        Raises:
            WeatherValidationError: If weather data is invalid
            WeatherDataError: If required weather data is missing
        """
        try:
            # Parse weather data
            data = json.loads(weather_data_json)
            
            # Check for errors in weather data
            if not data.get("success", True):
                raise WeatherDataError(
                    f"Données météo invalides: {data.get('error', 'Erreur inconnue')}"
                )
            
            # Extract weather conditions
            weather_conditions = data.get("weather_conditions", [])
            if not weather_conditions:
                raise WeatherDataError("Aucune donnée météo fournie pour le calcul de l'ETP")
            
            location = data.get("location", "")
            forecast_period_days = len(weather_conditions)
            
            # Calculate daily ET
            daily_et_list = []
            warnings = []
            
            for condition in weather_conditions:
                try:
                    daily_et = self._calculate_daily_et(
                        condition,
                        crop_type,
                        crop_stage,
                        warnings
                    )
                    daily_et_list.append(daily_et)
                except Exception as e:
                    logger.warning(f"Error calculating ET for {condition.get('date')}: {e}")
                    warnings.append(f"Calcul ETP incomplet pour {condition.get('date')}: {str(e)}")
            
            if not daily_et_list:
                raise WeatherDataError("Impossible de calculer l'évapotranspiration")
            
            # Calculate water balance
            water_balance = self._calculate_water_balance(
                daily_et_list,
                weather_conditions,
                crop_type
            )
            
            # Generate irrigation recommendations
            irrigation_recommendations = self._generate_irrigation_recommendations(
                daily_et_list,
                water_balance,
                crop_type,
                crop_stage
            )
            
            # Calculate summary statistics
            avg_et0 = sum(d.et0 for d in daily_et_list) / len(daily_et_list)
            avg_etc = None
            if all(d.etc is not None for d in daily_et_list):
                avg_etc = sum(d.etc for d in daily_et_list) / len(daily_et_list)
            
            # Find peak ET
            peak_et_day = max(daily_et_list, key=lambda d: d.etc if d.etc else d.et0)
            peak_et_date = peak_et_day.date
            peak_et_value = peak_et_day.etc if peak_et_day.etc else peak_et_day.et0
            
            # Build output
            result = EvapotranspirationOutput(
                location=location,
                forecast_period_days=forecast_period_days,
                crop_type=crop_type,
                crop_stage=crop_stage,
                daily_et=daily_et_list,
                water_balance=water_balance,
                irrigation_recommendations=irrigation_recommendations,
                avg_et0=round(avg_et0, 2),
                avg_etc=round(avg_etc, 2) if avg_etc else None,
                peak_et_date=peak_et_date,
                peak_et_value=round(peak_et_value, 2),
                calculation_method="Penman-Monteith FAO-56",
                data_source="weather_analysis",
                calculated_at=datetime.utcnow().isoformat() + "Z",
                success=True,
                warnings=warnings
            )
            
            return result
            
        except (WeatherValidationError, WeatherDataError):
            raise
        except json.JSONDecodeError as e:
            raise WeatherValidationError(f"Format JSON invalide: {str(e)}")
        except Exception as e:
            logger.error(f"Evapotranspiration calculation error: {e}", exc_info=True)
            raise WeatherDataError(f"Erreur lors du calcul de l'ETP: {str(e)}")
    
    def _calculate_daily_et(
        self,
        condition: Dict[str, Any],
        crop_type: Optional[str],
        crop_stage: Optional[str],
        warnings: List[str]
    ) -> DailyEvapotranspiration:
        """
        Calculate daily evapotranspiration using Penman-Monteith FAO-56

        Args:
            condition: Weather condition dict
            crop_type: Crop type
            crop_stage: Crop development stage (semis, croissance, floraison, maturation)
            warnings: List to append warnings to

        Returns:
            DailyEvapotranspiration object
        """
        date_str = condition.get("date", "")
        temp_min = condition.get("temperature_min", 15.0)
        temp_max = condition.get("temperature_max", 25.0)
        humidity = condition.get("humidity", 70.0)
        wind_speed_kmh = condition.get("wind_speed", 10.0)
        cloud_cover = condition.get("cloud_cover", 50.0)

        # Parse date
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            date = datetime.now()

        # Calculate average temperature
        temp_avg = (temp_min + temp_max) / 2

        # Estimate solar radiation from cloud cover and temperature
        # Default latitude for France (approximate center)
        latitude_deg = 46.0  # TODO: Extract from location if available
        elevation_m = 200.0  # TODO: Extract from location if available

        Rs, method = SolarRadiationEstimator.estimate_best_available(
            temp_min=temp_min,
            temp_max=temp_max,
            latitude_deg=latitude_deg,
            date=date,
            cloud_cover_percent=cloud_cover,
            elevation_m=elevation_m
        )

        # Calculate ET0 using Penman-Monteith FAO-56
        try:
            et0 = PenmanMonteithET0.calculate(
                temp_min=temp_min,
                temp_max=temp_max,
                humidity_mean=humidity,
                wind_speed_kmh=wind_speed_kmh,
                Rs=Rs,
                latitude_deg=latitude_deg,
                date=date,
                elevation_m=elevation_m
            )
        except Exception as e:
            logger.warning(f"Penman-Monteith calculation failed, using fallback: {e}")
            # Fallback to simplified Hargreaves
            temp_range = temp_max - temp_min
            et0 = 0.0023 * (temp_avg + 17.8) * math.sqrt(max(temp_range, 0.1)) * 15.0
            et0 = max(0.0, et0)

        # Calculate crop coefficient (simple 4-stage lookup)
        kc = None
        etc = None
        if crop_type:
            kc = self._get_crop_coefficient(crop_type, crop_stage)
            etc = et0 * kc

        return DailyEvapotranspiration(
            date=date_str,
            et0=round(et0, 2),
            etc=round(etc, 2) if etc is not None else None,
            kc=round(kc, 2) if kc is not None else None,
            temperature_avg=round(temp_avg, 1),
            humidity_avg=round(humidity, 1),
            wind_speed_avg=round(wind_speed_kmh, 1),
            solar_radiation=round(Rs, 2) if Rs else None
        )
    
    def _get_crop_coefficient(
        self,
        crop_type: Optional[str],
        crop_stage: Optional[str]
    ) -> float:
        """
        Get crop coefficient (Kc) for crop type and stage
        
        Args:
            crop_type: Crop type
            crop_stage: Crop development stage
            
        Returns:
            Crop coefficient (Kc)
        """
        if not crop_type:
            return 0.8  # Default Kc
        
        crop_lower = crop_type.lower()
        crop_coeffs = CROP_COEFFICIENTS.get(crop_lower, CROP_COEFFICIENTS["general"])
        
        if crop_stage:
            stage_lower = crop_stage.lower()
            return crop_coeffs.get(stage_lower, crop_coeffs.get("default", 0.8))
        
        return crop_coeffs.get("default", 0.8)
    
    def _calculate_water_balance(
        self,
        daily_et_list: List[DailyEvapotranspiration],
        weather_conditions: List[Dict[str, Any]],
        crop_type: Optional[str]
    ) -> WaterBalance:
        """Calculate water balance for the period"""
        # Sum ET
        total_et0 = sum(d.et0 for d in daily_et_list)
        total_etc = None
        if all(d.etc is not None for d in daily_et_list):
            total_etc = sum(d.etc for d in daily_et_list)
        
        # Sum precipitation
        total_precipitation = sum(c.get("precipitation", 0.0) for c in weather_conditions)
        
        # Calculate deficit/surplus
        et_for_balance = total_etc if total_etc is not None else total_et0
        water_deficit = max(0.0, et_for_balance - total_precipitation)
        water_surplus = max(0.0, total_precipitation - et_for_balance)
        
        # Determine if irrigation is needed (deficit > 10mm)
        irrigation_needed = water_deficit > 10.0
        irrigation_amount = round(water_deficit * 1.1, 1) if irrigation_needed else None  # Add 10% buffer
        
        return WaterBalance(
            total_et0=round(total_et0, 1),
            total_etc=round(total_etc, 1) if total_etc is not None else None,
            total_precipitation=round(total_precipitation, 1),
            water_deficit=round(water_deficit, 1),
            water_surplus=round(water_surplus, 1),
            irrigation_needed=irrigation_needed,
            irrigation_amount=irrigation_amount
        )

    def _generate_irrigation_recommendations(
        self,
        daily_et_list: List[DailyEvapotranspiration],
        water_balance: WaterBalance,
        crop_type: Optional[str],
        crop_stage: Optional[str]
    ) -> List[IrrigationRecommendation]:
        """Generate irrigation recommendations based on ET and water balance"""
        recommendations = []

        if not water_balance.irrigation_needed:
            return recommendations

        # Find days with highest ET deficit
        cumulative_deficit = 0.0
        for i, daily_et in enumerate(daily_et_list):
            # Assume no precipitation for simplification (already in water balance)
            daily_deficit = daily_et.etc if daily_et.etc else daily_et.et0
            cumulative_deficit += daily_deficit

            # Recommend irrigation when cumulative deficit > 15mm
            if cumulative_deficit > 15.0:
                amount_mm = round(cumulative_deficit, 1)
                amount_m3_ha = round(amount_mm * 10, 1)  # 1mm = 10 m³/ha

                # Determine priority based on crop stage and deficit
                priority = "moyenne"
                if crop_stage in ["floraison", "maturation"] or cumulative_deficit > 30:
                    priority = "haute"
                elif cumulative_deficit < 20:
                    priority = "basse"

                # Generate reason
                reason = f"Déficit hydrique de {amount_mm}mm"
                if crop_type and crop_stage:
                    reason += f" pendant {crop_stage} de {crop_type}"

                # Optimal time (morning for most crops)
                optimal_time = "matin"
                if daily_et.temperature_avg > 25:
                    optimal_time = "soir"  # Evening if hot

                # Method recommendation
                method = "aspersion"
                if crop_type in ["vigne", "maïs"]:
                    method = "goutte à goutte"

                recommendations.append(IrrigationRecommendation(
                    date=daily_et.date,
                    amount_mm=amount_mm,
                    amount_m3_ha=amount_m3_ha,
                    priority=priority,
                    reason=reason,
                    optimal_time=optimal_time,
                    method_recommendation=method
                ))

                # Reset cumulative deficit after recommendation
                cumulative_deficit = 0.0

        return recommendations


# Create service instance
evapotranspiration_service = EvapotranspirationService()


async def calculate_evapotranspiration_enhanced(
    weather_data_json: str,
    crop_type: Optional[str] = None,
    crop_stage: Optional[str] = None
) -> str:
    """
    Calculate evapotranspiration and water needs from weather data

    Args:
        weather_data_json: JSON string from weather tool containing forecast data
        crop_type: Optional crop type for crop-specific calculations (blé, maïs, colza, etc.)
        crop_stage: Optional crop development stage (semis, croissance, floraison, maturation)

    Returns:
        JSON string with ET calculations, water balance, and irrigation recommendations
    """
    try:
        # Validate input
        input_data = EvapotranspirationInput(
            weather_data_json=weather_data_json,
            crop_type=crop_type,
            crop_stage=crop_stage
        )

        # Calculate evapotranspiration
        result = await evapotranspiration_service.calculate_evapotranspiration(
            weather_data_json=input_data.weather_data_json,
            crop_type=input_data.crop_type,
            crop_stage=input_data.crop_stage
        )

        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)

    except ValidationError as e:
        logger.error(f"Evapotranspiration validation error: {e}")
        error_result = EvapotranspirationOutput(
            location="",
            forecast_period_days=1,  # Minimum valid value
            daily_et=[],
            water_balance=WaterBalance(
                total_et0=0.0,
                total_precipitation=0.0,
                water_deficit=0.0,
                water_surplus=0.0,
                irrigation_needed=False
            ),
            avg_et0=0.0,
            calculated_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=f"Paramètres invalides: {str(e)}",
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)

    except WeatherValidationError as e:
        logger.error(f"Weather validation error: {e}")
        error_result = EvapotranspirationOutput(
            location="",
            forecast_period_days=1,  # Minimum valid value
            daily_et=[],
            water_balance=WaterBalance(
                total_et0=0.0,
                total_precipitation=0.0,
                water_deficit=0.0,
                water_surplus=0.0,
                irrigation_needed=False
            ),
            avg_et0=0.0,
            calculated_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=f"Données météo invalides: {str(e)}",
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)

    except WeatherDataError as e:
        logger.error(f"Weather data error: {e}")
        error_result = EvapotranspirationOutput(
            location="",
            forecast_period_days=1,  # Minimum valid value
            daily_et=[],
            water_balance=WaterBalance(
                total_et0=0.0,
                total_precipitation=0.0,
                water_deficit=0.0,
                water_surplus=0.0,
                irrigation_needed=False
            ),
            avg_et0=0.0,
            calculated_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=f"Données manquantes: {str(e)}",
            error_type="data_missing"
        )
        return error_result.model_dump_json(indent=2)

    except Exception as e:
        logger.error(f"Evapotranspiration calculation error: {e}", exc_info=True)
        error_result = EvapotranspirationOutput(
            location="",
            forecast_period_days=1,  # Minimum valid value
            daily_et=[],
            water_balance=WaterBalance(
                total_et0=0.0,
                total_precipitation=0.0,
                water_deficit=0.0,
                water_surplus=0.0,
                irrigation_needed=False
            ),
            avg_et0=0.0,
            calculated_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error="Erreur inattendue lors du calcul de l'ETP. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the enhanced tool
calculate_evapotranspiration_tool = StructuredTool.from_function(
    func=calculate_evapotranspiration_enhanced,
    name="calculate_evapotranspiration",
    description="""Calcule l'évapotranspiration (ETP) et les besoins en eau à partir des données météo.

    Utilise la méthode Penman-Monteith FAO-56 pour calculer:
    - ETP de référence (ET0) quotidienne
    - ETP de la culture (ETc) avec coefficients culturaux
    - Bilan hydrique (précipitations vs besoins)
    - Recommandations d'irrigation personnalisées

    Supporte les cultures: blé, maïs, colza, orge, tournesol, betterave, pomme de terre, vigne, prairie
    Stades de développement: semis, croissance, floraison, maturation

    Entrée: JSON de données météo + type de culture (optionnel) + stade (optionnel)
    Sortie: Calculs ETP, bilan hydrique, recommandations d'irrigation""",
    args_schema=EvapotranspirationInput,
    return_direct=False,
    coroutine=calculate_evapotranspiration_enhanced,
    handle_validation_error=False  # We handle errors ourselves
)

