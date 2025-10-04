"""
Atomic Tools for Journal Processing
Simple, focused tools that do ONE thing each
"""

from typing import Dict, List, Optional, Any
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
import time
from datetime import date, datetime

from app.services.infrastructure.ephy_service import EphyService
from app.services.infrastructure.weather_service import WeatherService
from app.core.database import get_async_db
from app.models.intervention import VoiceJournalEntry
from app.models.mesparcelles import Parcelle
from app.services.monitoring.voice_monitoring import voice_monitor

logger = logging.getLogger(__name__)

# Initialize services
ephy_service = EphyService()
weather_service = WeatherService()


# ============================================================================
# EPHY DATABASE TOOLS (Atomic operations)
# ============================================================================

@tool
async def get_product_by_amm(amm_code: str) -> Dict[str, Any]:
    """Get basic product information by AMM code from EPHY database"""
    start_time = time.time()
    try:
        async for db in get_async_db():
            product_info = await ephy_service.get_product_by_amm(amm_code, db)
            
            # Record successful EPHY lookup
            duration_ms = (time.time() - start_time) * 1000
            voice_monitor.record_ephy_lookup(amm_code, duration_ms, success=True)
            
            return {
                "success": True,
                "amm_code": amm_code,
                "product": product_info
            }
    except Exception as e:
        logger.error(f"Error getting product {amm_code}: {e}")
        
        # Record failed EPHY lookup
        duration_ms = (time.time() - start_time) * 1000
        voice_monitor.record_ephy_lookup(amm_code, duration_ms, success=False, error_message=str(e))
        
        return {
            "success": False,
            "amm_code": amm_code,
            "error": str(e)
        }


@tool
async def check_product_authorized(amm_code: str) -> Dict[str, Any]:
    """Check if product is currently authorized (not withdrawn)"""
    try:
        async for db in get_async_db():
            product_info = await ephy_service.get_product_by_amm(amm_code, db)
            if not product_info:
                return {
                    "success": False,
                    "amm_code": amm_code,
                    "authorized": False,
                    "reason": "Product not found"
                }
            
            is_authorized = product_info.get("etat_autorisation") == "AUTORISE"
            return {
                "success": True,
                "amm_code": amm_code,
                "authorized": is_authorized,
                "status": product_info.get("etat_autorisation"),
                "product_name": product_info.get("nom_produit")
            }
    except Exception as e:
        return {
            "success": False,
            "amm_code": amm_code,
            "error": str(e)
        }


@tool
async def get_max_dose_for_crop(amm_code: str, crop_type: str) -> Dict[str, Any]:
    """Get maximum authorized dose for product on specific crop"""
    try:
        async for db in get_async_db():
            product_info = await ephy_service.get_product_by_amm(amm_code, db)
            if not product_info:
                return {
                    "success": False,
                    "amm_code": amm_code,
                    "crop_type": crop_type,
                    "error": "Product not found"
                }
            
            # Find usage for this crop
            max_dose = None
            unit = None
            for usage in product_info.get("usages", []):
                if crop_type.lower() in usage.get("type_culture_libelle", "").lower():
                    max_dose = usage.get("dose_max_par_apport")
                    unit = usage.get("dose_max_par_apport_unite")
                    break
            
            return {
                "success": True,
                "amm_code": amm_code,
                "crop_type": crop_type,
                "max_dose": float(max_dose) if max_dose else None,
                "unit": unit,
                "found": max_dose is not None
            }
    except Exception as e:
        return {
            "success": False,
            "amm_code": amm_code,
            "crop_type": crop_type,
            "error": str(e)
        }


@tool
async def check_crop_authorization(amm_code: str, crop_type: str) -> Dict[str, Any]:
    """Check if product is authorized for specific crop"""
    try:
        async for db in get_async_db():
            product_info = await ephy_service.get_product_by_amm(amm_code, db)
            if not product_info:
                return {
                    "success": False,
                    "amm_code": amm_code,
                    "crop_type": crop_type,
                    "authorized": False,
                    "reason": "Product not found"
                }
            
            # Check if crop is in authorized usages
            authorized_crops = []
            for usage in product_info.get("usages", []):
                crop_name = usage.get("type_culture_libelle", "")
                if crop_name:
                    authorized_crops.append(crop_name)
            
            is_authorized = any(crop_type.lower() in crop.lower() for crop in authorized_crops)
            
            return {
                "success": True,
                "amm_code": amm_code,
                "crop_type": crop_type,
                "authorized": is_authorized,
                "authorized_crops": authorized_crops
            }
    except Exception as e:
        return {
            "success": False,
            "amm_code": amm_code,
            "crop_type": crop_type,
            "error": str(e)
        }


@tool
async def get_pre_harvest_interval(amm_code: str, crop_type: str) -> Dict[str, Any]:
    """Get days required before harvest (DAR) for product on crop"""
    try:
        async for db in get_async_db():
            product_info = await ephy_service.get_product_by_amm(amm_code, db)
            if not product_info:
                return {
                    "success": False,
                    "amm_code": amm_code,
                    "crop_type": crop_type,
                    "error": "Product not found"
                }
            
            # Find DAR for this crop
            dar_days = None
            for usage in product_info.get("usages", []):
                if crop_type.lower() in usage.get("type_culture_libelle", "").lower():
                    dar_days = usage.get("delai_avant_recolte_jour")
                    break
            
            return {
                "success": True,
                "amm_code": amm_code,
                "crop_type": crop_type,
                "dar_days": dar_days,
                "found": dar_days is not None
            }
    except Exception as e:
        return {
            "success": False,
            "amm_code": amm_code,
            "crop_type": crop_type,
            "error": str(e)
        }


@tool
async def search_products_by_name(product_name: str, limit: int = 10) -> Dict[str, Any]:
    """Search products by name in EPHY database"""
    try:
        async for db in get_async_db():
            products = await ephy_service.search_products(
                product_name=product_name,
                limit=limit,
                db=db
            )
            
            return {
                "success": True,
                "product_name": product_name,
                "products": products,
                "count": len(products)
            }
    except Exception as e:
        return {
            "success": False,
            "product_name": product_name,
            "error": str(e)
        }


# ============================================================================
# WEATHER TOOLS (Atomic operations)
# ============================================================================

@tool
async def get_wind_speed(date_str: str, location: str) -> Dict[str, Any]:
    """Get wind speed in km/h for specific date and location"""
    try:
        target_date = datetime.fromisoformat(date_str).date()
        weather_data = await weather_service.get_weather_for_date(
            date=target_date,
            location=location
        )
        
        wind_speed = weather_data.get("wind_speed_kmh", 0) if weather_data else 0
        
        return {
            "success": True,
            "date": date_str,
            "location": location,
            "wind_speed_kmh": wind_speed,
            "data_available": weather_data is not None
        }
    except Exception as e:
        return {
            "success": False,
            "date": date_str,
            "location": location,
            "error": str(e)
        }


@tool
async def get_temperature(date_str: str, location: str) -> Dict[str, Any]:
    """Get temperature in Celsius for specific date and location"""
    try:
        target_date = datetime.fromisoformat(date_str).date()
        weather_data = await weather_service.get_weather_for_date(
            date=target_date,
            location=location
        )
        
        temperature = weather_data.get("temperature_celsius", 0) if weather_data else 0
        
        return {
            "success": True,
            "date": date_str,
            "location": location,
            "temperature_celsius": temperature,
            "data_available": weather_data is not None
        }
    except Exception as e:
        return {
            "success": False,
            "date": date_str,
            "location": location,
            "error": str(e)
        }


@tool
async def check_rain_forecast(date_str: str, location: str) -> Dict[str, Any]:
    """Check if rain is forecast for specific date and location"""
    try:
        target_date = datetime.fromisoformat(date_str).date()
        weather_data = await weather_service.get_weather_for_date(
            date=target_date,
            location=location
        )
        
        precipitation = weather_data.get("precipitation_mm", 0) if weather_data else 0
        rain_expected = precipitation > 0
        
        return {
            "success": True,
            "date": date_str,
            "location": location,
            "rain_expected": rain_expected,
            "precipitation_mm": precipitation,
            "data_available": weather_data is not None
        }
    except Exception as e:
        return {
            "success": False,
            "date": date_str,
            "location": location,
            "error": str(e)
        }


@tool
async def is_weather_safe_for_treatment(date_str: str, location: str) -> Dict[str, Any]:
    """Check if weather conditions are safe for phytosanitary treatment"""
    try:
        target_date = datetime.fromisoformat(date_str).date()
        weather_data = await weather_service.get_weather_for_date(
            date=target_date,
            location=location
        )
        
        if not weather_data:
            return {
                "success": False,
                "date": date_str,
                "location": location,
                "error": "Weather data not available"
            }
        
        wind_speed = weather_data.get("wind_speed_kmh", 0)
        temperature = weather_data.get("temperature_celsius", 0)
        precipitation = weather_data.get("precipitation_mm", 0)
        
        issues = []
        if wind_speed > 19:
            issues.append(f"Wind too strong: {wind_speed} km/h (max: 19 km/h)")
        if temperature < 5:
            issues.append(f"Temperature too low: {temperature}°C (min: 5°C)")
        if precipitation > 0:
            issues.append(f"Rain expected: {precipitation} mm")
        
        is_safe = len(issues) == 0
        
        return {
            "success": True,
            "date": date_str,
            "location": location,
            "is_safe": is_safe,
            "issues": issues,
            "wind_speed_kmh": wind_speed,
            "temperature_celsius": temperature,
            "precipitation_mm": precipitation
        }
    except Exception as e:
        return {
            "success": False,
            "date": date_str,
            "location": location,
            "error": str(e)
        }


# ============================================================================
# DATABASE TOOLS (Atomic operations)
# ============================================================================

@tool
async def save_journal_entry(entry_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Save journal entry to database and return entry ID"""
    try:
        async for db in get_async_db():
            # Create journal entry
            journal_entry = VoiceJournalEntry(
                user_id=user_id,
                intervention_type=entry_data.get("type_intervention"),
                parcelle=entry_data.get("parcelle"),
                date_intervention=datetime.fromisoformat(entry_data.get("date_intervention")) if entry_data.get("date_intervention") else datetime.now(),
                surface_ha=entry_data.get("surface_travaillee_ha"),
                culture=entry_data.get("culture"),
                description=entry_data.get("notes", ""),
                products_used=entry_data.get("intrants", []),
                equipment_used=entry_data.get("materiels", []),
                weather_conditions=entry_data.get("conditions_meteo"),
                temperature_celsius=entry_data.get("temperature_celsius"),
                humidity_percent=entry_data.get("humidity_percent"),
                wind_speed_kmh=entry_data.get("wind_speed_kmh"),
                duration_minutes=entry_data.get("duration_minutes"),
                prestataire=entry_data.get("prestataire"),
                cout_euros=entry_data.get("cout_euros"),
                raw_transcript=entry_data.get("raw_transcript", ""),
                structured_data=entry_data
            )
            
            db.add(journal_entry)
            await db.commit()
            await db.refresh(journal_entry)
            
            return {
                "success": True,
                "entry_id": str(journal_entry.id),
                "saved_at": journal_entry.created_at.isoformat()
            }
    except Exception as e:
        logger.error(f"Error saving journal entry: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def get_farm_parcels(org_id: str) -> Dict[str, Any]:
    """Get list of farm parcels for organization"""
    try:
        async for db in get_async_db():
            parcels = await db.execute(
                select(Parcelle).where(Parcelle.siret == org_id)
            )
            parcel_list = parcels.scalars().all()
            
            return {
                "success": True,
                "org_id": org_id,
                "parcels": [
                    {
                        "id": str(parcel.id),
                        "name": parcel.nom_parcelle,
                        "surface_ha": float(parcel.surface_ha) if parcel.surface_ha else None,
                        "culture": parcel.culture_actuelle
                    }
                    for parcel in parcel_list
                ],
                "count": len(parcel_list)
            }
    except Exception as e:
        return {
            "success": False,
            "org_id": org_id,
            "error": str(e)
        }


@tool
async def get_journal_entry(entry_id: str) -> Dict[str, Any]:
    """Get journal entry by ID"""
    try:
        async for db in get_async_db():
            entry = await db.get(VoiceJournalEntry, entry_id)
            if not entry:
                return {
                    "success": False,
                    "entry_id": entry_id,
                    "error": "Entry not found"
                }
            
            return {
                "success": True,
                "entry_id": entry_id,
                "entry": {
                    "id": str(entry.id),
                    "intervention_type": entry.intervention_type,
                    "parcelle": entry.parcelle,
                    "date_intervention": entry.date_intervention.isoformat() if entry.date_intervention else None,
                    "surface_ha": float(entry.surface_ha) if entry.surface_ha else None,
                    "culture": entry.culture,
                    "description": entry.description,
                    "products_used": entry.products_used,
                    "weather_conditions": entry.weather_conditions,
                    "created_at": entry.created_at.isoformat()
                }
            }
    except Exception as e:
        return {
            "success": False,
            "entry_id": entry_id,
            "error": str(e)
        }


# ============================================================================
# VALIDATION TOOLS (Atomic operations)
# ============================================================================

@tool
async def validate_dose(dose: float, max_dose: float, unit: str) -> Dict[str, Any]:
    """Validate if dose is within authorized limits"""
    try:
        if dose > max_dose:
            return {
                "success": True,
                "valid": False,
                "dose": dose,
                "max_dose": max_dose,
                "unit": unit,
                "issue": f"Dose too high: {dose} {unit} > {max_dose} {unit}"
            }
        elif dose < max_dose * 0.5:  # Warning if less than 50% of max
            return {
                "success": True,
                "valid": True,
                "dose": dose,
                "max_dose": max_dose,
                "unit": unit,
                "warning": f"Dose quite low: {dose} {unit} (max: {max_dose} {unit})"
            }
        else:
            return {
                "success": True,
                "valid": True,
                "dose": dose,
                "max_dose": max_dose,
                "unit": unit,
                "message": "Dose within acceptable range"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def check_date_validity(date_str: str, intervention_type: str) -> Dict[str, Any]:
    """Check if date is valid for intervention type (basic validation)"""
    try:
        target_date = datetime.fromisoformat(date_str).date()
        today = date.today()
        
        # Basic date validation
        if target_date > today:
            return {
                "success": True,
                "date": date_str,
                "intervention_type": intervention_type,
                "valid": False,
                "issue": "Date is in the future"
            }
        
        # Check if date is too old (more than 1 year)
        if (today - target_date).days > 365:
            return {
                "success": True,
                "date": date_str,
                "intervention_type": intervention_type,
                "valid": False,
                "issue": "Date is more than 1 year old"
            }
        
        return {
            "success": True,
            "date": date_str,
            "intervention_type": intervention_type,
            "valid": True,
            "message": "Date is valid"
        }
    except Exception as e:
        return {
            "success": False,
            "date": date_str,
            "error": str(e)
        }


@tool
async def validate_surface(surface_ha: float, max_surface: float = 1000.0) -> Dict[str, Any]:
    """Validate if surface area is reasonable"""
    try:
        if surface_ha <= 0:
            return {
                "success": True,
                "valid": False,
                "surface_ha": surface_ha,
                "issue": "Surface must be positive"
            }
        
        if surface_ha > max_surface:
            return {
                "success": True,
                "valid": False,
                "surface_ha": surface_ha,
                "max_surface": max_surface,
                "issue": f"Surface too large: {surface_ha} ha > {max_surface} ha"
            }
        
        return {
            "success": True,
            "valid": True,
            "surface_ha": surface_ha,
            "message": "Surface is valid"
        }
    except Exception as e:
        return {
            "success": False,
            "surface_ha": surface_ha,
            "error": str(e)
        }


# ============================================================================
# UTILITY TOOLS (Atomic operations)
# ============================================================================

@tool
async def extract_date_from_text(text: str) -> Dict[str, Any]:
    """Extract date from text using simple patterns"""
    try:
        import re
        from datetime import datetime, date
        
        # Simple date patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # DD/MM/YYYY
            r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    if '-' in date_str and len(date_str.split('-')[0]) == 4:
                        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        parsed_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                    
                    return {
                        "success": True,
                        "text": text,
                        "date_found": date_str,
                        "parsed_date": parsed_date.isoformat()
                    }
                except ValueError:
                    continue
        
        return {
            "success": True,
            "text": text,
            "date_found": None,
            "message": "No valid date pattern found"
        }
    except Exception as e:
        return {
            "success": False,
            "text": text,
            "error": str(e)
        }


@tool
async def extract_number_from_text(text: str, unit: str = None) -> Dict[str, Any]:
    """Extract number from text (for doses, surfaces, etc.)"""
    try:
        import re
        
        # Pattern for numbers with optional decimal
        pattern = r'(\d+(?:\.\d+)?)'
        matches = re.findall(pattern, text)
        
        if matches:
            numbers = [float(match) for match in matches]
            return {
                "success": True,
                "text": text,
                "numbers_found": numbers,
                "unit": unit,
                "primary_number": numbers[0] if numbers else None
            }
        
        return {
            "success": True,
            "text": text,
            "numbers_found": [],
            "unit": unit,
            "message": "No numbers found"
        }
    except Exception as e:
        return {
            "success": False,
            "text": text,
            "error": str(e)
        }


# Export all atomic tools
ATOMIC_TOOLS = [
    # EPHY tools
    get_product_by_amm,
    check_product_authorized,
    get_max_dose_for_crop,
    check_crop_authorization,
    get_pre_harvest_interval,
    search_products_by_name,
    
    # Weather tools
    get_wind_speed,
    get_temperature,
    check_rain_forecast,
    is_weather_safe_for_treatment,
    
    # Database tools
    save_journal_entry,
    get_farm_parcels,
    get_journal_entry,
    
    # Validation tools
    validate_dose,
    check_date_validity,
    validate_surface,
    
    # Utility tools
    extract_date_from_text,
    extract_number_from_text,
]
