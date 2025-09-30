"""
Get Farm Data Tool - Single Purpose Tool

Job: Retrieve raw farm data records based on filters.
Input: Structured filters (time_period, crops, parcels)
Output: JSON string of FarmDataRecord objects

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
import asyncio
import aiohttp
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

@dataclass
class FarmDataRecord:
    """Structured farm data record."""
    parcel: str
    crop: str
    surface: float
    yield_value: float
    date: str
    cost_per_hectare: float
    quality_score: float

class GetFarmDataTool(BaseTool):
    """
    Tool: Retrieve raw farm data records based on filters.
    
    Job: Get data records from database/mock data based on filters.
    Input: Structured filters (time_period, crops, parcels)
    Output: JSON string of FarmDataRecord objects
    """
    
    name: str = "get_farm_data_tool"
    description: str = "Récupère les données brutes de l'exploitation basées sur des filtres"
    
    def _run(
        self,
        time_period: Optional[str] = None,
        crops: Optional[List[str]] = None,
        parcels: Optional[List[str]] = None,
        farm_id: Optional[str] = None,
        use_mesparcelles: bool = True,
        **kwargs
    ) -> str:
        """
        Retrieves farm data records from database and MesParcelles API.

        Args:
            time_period: Time period filter (e.g., "current_year", "last_season")
            crops: List of crop types to filter by
            parcels: List of parcel IDs to filter by
            farm_id: Specific farm ID for targeted data retrieval
            use_mesparcelles: Whether to include MesParcelles API data
        """
        try:
            # Get farm data from database and MesParcelles (synchronous for now)
            farm_data = self._retrieve_farm_data_sync(
                time_period, crops, parcels, farm_id, use_mesparcelles
            )

            return json.dumps(farm_data, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Get farm data error: {e}")
            return json.dumps({"error": f"Erreur lors de la récupération des données: {str(e)}"})

    def _retrieve_farm_data_sync(
        self,
        time_period: str = None,
        crops: List[str] = None,
        parcels: List[str] = None,
        farm_id: str = None,
        use_mesparcelles: bool = True
    ) -> Dict[str, Any]:
        """Retrieve farm data from database and MesParcelles API (synchronous version)."""

        # Get data from local database
        database_data = self._get_database_farm_data_sync(time_period, crops, parcels, farm_id)

        result = {
            "database_records": database_data,
            "total_records": len(database_data),
            "filters": {
                "time_period": time_period,
                "crops": crops,
                "parcels": parcels,
                "farm_id": farm_id
            },
            "data_sources": ["local_database"]
        }

        # Add MesParcelles data if requested
        if use_mesparcelles:
            try:
                mesparcelles_data = self._get_mesparcelles_data_sync(farm_id, parcels)
                result["mesparcelles_data"] = mesparcelles_data
                result["data_sources"].append("mesparcelles_api")
            except Exception as e:
                logger.warning(f"MesParcelles integration failed: {e}")
                result["mesparcelles_error"] = str(e)

        return result

    async def _retrieve_farm_data_async(
        self,
        time_period: str = None,
        crops: List[str] = None,
        parcels: List[str] = None,
        farm_id: str = None,
        use_mesparcelles: bool = True
    ) -> Dict[str, Any]:
        """Retrieve farm data from database and MesParcelles API."""

        # Get data from local database
        database_data = await self._get_database_farm_data(time_period, crops, parcels, farm_id)

        result = {
            "database_records": database_data,
            "total_records": len(database_data),
            "filters": {
                "time_period": time_period,
                "crops": crops,
                "parcels": parcels,
                "farm_id": farm_id
            },
            "data_sources": ["local_database"]
        }

        # Add MesParcelles data if requested
        if use_mesparcelles:
            try:
                mesparcelles_data = await self._get_mesparcelles_data(farm_id, parcels)
                result["mesparcelles_data"] = mesparcelles_data
                result["data_sources"].append("mesparcelles_api")
            except Exception as e:
                logger.warning(f"MesParcelles integration failed: {e}")
                result["mesparcelles_error"] = str(e)

        return result

    async def _get_database_farm_data(
        self,
        time_period: str = None,
        crops: List[str] = None,
        parcels: List[str] = None,
        farm_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get farm data from MesParcelles database (async version)."""
        # For now, call the sync version
        # TODO: Implement true async version if needed for performance
        return self._get_database_farm_data_sync(time_period, crops, parcels, farm_id)

    async def _get_mesparcelles_data(self, farm_id: str = None, parcels: List[str] = None) -> Dict[str, Any]:
        """Get data from MesParcelles API."""
        try:
            # TODO: Replace with actual MesParcelles API calls
            # For now, return mock MesParcelles-style data structure

            return {
                "api_status": "connected",
                "farm_profile": {
                    "farm_id": farm_id or "FR_FARM_123456",
                    "siret": "12345678901234",
                    "total_surface_ha": 156.5,
                    "main_crops": ["blé", "maïs", "colza", "orge"],
                    "certification": "HVE_niveau_2",
                    "region": "Normandie",
                    "department": "Calvados"
                },
                "parcel_details": [
                    {
                        "parcel_id": "MP_001",
                        "name": "Parcelle A",
                        "surface_ha": 15.5,
                        "crop_rotation": ["blé", "colza", "orge"],
                        "soil_analysis": {
                            "ph": 6.8,
                            "organic_matter_percent": 2.4,
                            "phosphore_ppm": 45,
                            "potasse_ppm": 180,
                            "azote_ppm": 25
                        },
                        "irrigation_system": "aspersion",
                        "drainage": "bon",
                        "coordinates": {
                            "lat": 49.1829,
                            "lon": 0.3707
                        }
                    },
                    {
                        "parcel_id": "MP_002",
                        "name": "Parcelle B",
                        "surface_ha": 12.0,
                        "crop_rotation": ["maïs", "blé", "colza"],
                        "soil_analysis": {
                            "ph": 7.1,
                            "organic_matter_percent": 2.8,
                            "phosphore_ppm": 52,
                            "potasse_ppm": 195,
                            "azote_ppm": 28
                        },
                        "irrigation_system": "goutte_a_goutte",
                        "drainage": "excellent",
                        "coordinates": {
                            "lat": 49.1845,
                            "lon": 0.3723
                        }
                    }
                ],
                "weather_station": {
                    "station_id": "METEO_NORMANDIE_01",
                    "distance_km": 2.3,
                    "last_update": datetime.now().isoformat()
                },
                "last_sync": datetime.now().isoformat(),
                "sync_status": "success"
            }

        except Exception as e:
            logger.error(f"MesParcelles API error: {e}")
            return {
                "api_status": "error",
                "error": str(e),
                "last_sync": datetime.now().isoformat()
            }

    def _get_database_farm_data_sync(
        self,
        time_period: str = None,
        crops: List[str] = None,
        parcels: List[str] = None,
        farm_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get farm data from MesParcelles database (synchronous version)."""
        try:
            # Import MesParcelles models from Ekumenbackend
            import sys
            import os
            backend_path = os.path.join(os.path.dirname(__file__), '../../../../Ekumenbackend')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)

            from app.models.mesparcelles import Parcelle, SuccessionCulture, Culture, Intervention
            from app.core.database import SessionLocal
            from sqlalchemy import select
            from datetime import datetime

            # Use synchronous session
            with SessionLocal() as db:
                # Query parcelles for the farm (SIRET)
                query = select(Parcelle)

                # Filter by farm_id (SIRET)
                if farm_id:
                    query = query.where(Parcelle.siret_exploitation == farm_id)

                # Filter by millesime (year) if time_period specified
                current_year = datetime.now().year
                if time_period == "current_year":
                    query = query.where(Parcelle.millesime == current_year)
                elif time_period == "previous_year":
                    query = query.where(Parcelle.millesime == current_year - 1)

                # Filter by parcel names if specified
                if parcels:
                    query = query.where(Parcelle.nom.in_(parcels))

                # Execute query
                result = db.execute(query)
                parcel_records = result.scalars().all()

                # Convert to dict format
                farm_data = []
                for parcelle in parcel_records:
                    # Get succession cultures (crops) for this parcel
                    cultures_query = select(SuccessionCulture).join(Culture).where(
                        SuccessionCulture.uuid_parcelle == parcelle.uuid_parcelle
                    )
                    cultures_result = db.execute(cultures_query)
                    succession_cultures = cultures_result.scalars().all()

                    # Get culture names
                    culture_names = []
                    for sc in succession_cultures:
                        if sc.culture:
                            culture_names.append(sc.culture.libelle)

                    # Filter by crops if specified
                    if crops and not any(crop in culture_names for crop in crops):
                        continue

                    # Get interventions for this parcel
                    interventions_query = select(Intervention).where(
                        Intervention.uuid_parcelle == parcelle.uuid_parcelle
                    ).limit(10)  # Limit to recent interventions
                    interventions_result = db.execute(interventions_query)
                    interventions = interventions_result.scalars().all()

                    farm_data.append({
                        "id": str(parcelle.uuid_parcelle),
                        "farm_id": parcelle.siret_exploitation,
                        "parcel": parcelle.nom or f"Parcelle {parcelle.uuid_parcelle}",
                        "millesime": parcelle.millesime,
                        "surface_ha": float(parcelle.surface_mesuree_ha) if parcelle.surface_mesuree_ha else 0.0,
                        "commune": parcelle.insee_commune,
                        "cultures": culture_names,
                        "nb_interventions": len(interventions),
                        "created_at": parcelle.created_at.isoformat() if parcelle.created_at else None,
                        "updated_at": parcelle.updated_at.isoformat() if parcelle.updated_at else None
                    })

                logger.info(f"✅ Retrieved {len(farm_data)} parcels from MesParcelles database for farm {farm_id}")
                return farm_data

        except Exception as e:
            logger.error(f"❌ MesParcelles database query error: {e}", exc_info=True)
            logger.warning("Returning empty result")
            return []

    def _get_mesparcelles_data_sync(self, farm_id: str = None, parcels: List[str] = None) -> Dict[str, Any]:
        """Get data from MesParcelles API (synchronous version)."""
        try:
            # TODO: Replace with actual MesParcelles API calls
            # For now, return mock MesParcelles-style data structure

            return {
                "api_status": "connected",
                "farm_profile": {
                    "farm_id": farm_id or "FR_FARM_123456",
                    "siret": "12345678901234",
                    "total_surface_ha": 156.5,
                    "main_crops": ["blé", "maïs", "colza", "orge"],
                    "certification": "HVE_niveau_2",
                    "region": "Normandie",
                    "department": "Calvados"
                },
                "parcel_details": [
                    {
                        "parcel_id": "MP_001",
                        "name": "Parcelle A",
                        "surface_ha": 15.5,
                        "crop_rotation": ["blé", "colza", "orge"],
                        "soil_analysis": {
                            "ph": 6.8,
                            "organic_matter_percent": 2.4,
                            "phosphore_ppm": 45,
                            "potasse_ppm": 180,
                            "azote_ppm": 25
                        },
                        "irrigation_system": "aspersion",
                        "drainage": "bon",
                        "coordinates": {
                            "lat": 49.1829,
                            "lon": 0.3707
                        }
                    }
                ],
                "weather_station": {
                    "station_id": "METEO_NORMANDIE_01",
                    "distance_km": 2.3,
                    "last_update": datetime.now().isoformat()
                },
                "last_sync": datetime.now().isoformat(),
                "sync_status": "success"
            }

        except Exception as e:
            logger.error(f"MesParcelles API error: {e}")
            return {
                "api_status": "error",
                "error": str(e),
                "last_sync": datetime.now().isoformat()
            }
