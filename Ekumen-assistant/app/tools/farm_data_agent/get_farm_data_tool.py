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
        """Get farm data from local database."""
        try:
            async with AsyncSessionLocal() as db:
                # TODO: Replace with actual database queries
                # For now, return enhanced mock data that simulates database structure
                mock_data = [
                    {
                        "id": 1,
                        "farm_id": farm_id or "FR_FARM_123456",
                        "parcel": "Parcelle A",
                        "crop": "blé",
                        "surface_ha": 15.5,
                        "yield_qx_ha": 72.3,
                        "harvest_date": "2024-08-15",
                        "revenue_eur": 450.0,
                        "quality_score": 8.2,
                        "created_at": "2024-08-15T10:30:00",
                        "updated_at": "2024-08-15T10:30:00"
                    },
                    {
                        "id": 2,
                        "farm_id": farm_id or "FR_FARM_123456",
                        "parcel": "Parcelle B",
                        "crop": "maïs",
                        "surface_ha": 12.0,
                        "yield_qx_ha": 95.8,
                        "harvest_date": "2024-09-20",
                        "revenue_eur": 520.0,
                        "quality_score": 8.7,
                        "created_at": "2024-09-20T14:15:00",
                        "updated_at": "2024-09-20T14:15:00"
                    },
                    {
                        "id": 3,
                        "farm_id": farm_id or "FR_FARM_123456",
                        "parcel": "Parcelle C",
                        "crop": "colza",
                        "surface_ha": 8.5,
                        "yield_qx_ha": 35.2,
                        "harvest_date": "2024-07-10",
                        "revenue_eur": 380.0,
                        "quality_score": 7.9,
                        "created_at": "2024-07-10T09:45:00",
                        "updated_at": "2024-07-10T09:45:00"
                    }
                ]

                # Apply filters
                filtered_data = mock_data

                if time_period == "current_year":
                    filtered_data = [d for d in filtered_data if d["harvest_date"].startswith("2024")]
                elif time_period == "previous_year":
                    filtered_data = [d for d in filtered_data if d["harvest_date"].startswith("2023")]

                if crops:
                    filtered_data = [d for d in filtered_data if d["crop"] in crops]

                if parcels:
                    filtered_data = [d for d in filtered_data if d["parcel"] in parcels]

                return filtered_data

        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []

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
        """Get farm data from local database (synchronous version)."""
        try:
            # TODO: Replace with actual database queries
            # For now, return enhanced mock data that simulates database structure
            mock_data = [
                {
                    "id": 1,
                    "farm_id": farm_id or "FR_FARM_123456",
                    "parcel": "Parcelle A",
                    "crop": "blé",
                    "surface_ha": 15.5,
                    "yield_qx_ha": 72.3,
                    "harvest_date": "2024-08-15",
                    "revenue_eur": 450.0,
                    "quality_score": 8.2,
                    "created_at": "2024-08-15T10:30:00",
                    "updated_at": "2024-08-15T10:30:00"
                },
                {
                    "id": 2,
                    "farm_id": farm_id or "FR_FARM_123456",
                    "parcel": "Parcelle B",
                    "crop": "maïs",
                    "surface_ha": 12.0,
                    "yield_qx_ha": 95.8,
                    "harvest_date": "2024-09-20",
                    "revenue_eur": 520.0,
                    "quality_score": 8.7,
                    "created_at": "2024-09-20T14:15:00",
                    "updated_at": "2024-09-20T14:15:00"
                },
                {
                    "id": 3,
                    "farm_id": farm_id or "FR_FARM_123456",
                    "parcel": "Parcelle C",
                    "crop": "colza",
                    "surface_ha": 8.5,
                    "yield_qx_ha": 35.2,
                    "harvest_date": "2024-07-10",
                    "revenue_eur": 380.0,
                    "quality_score": 7.9,
                    "created_at": "2024-07-10T09:45:00",
                    "updated_at": "2024-07-10T09:45:00"
                }
            ]

            # Apply filters
            filtered_data = mock_data

            if time_period == "current_year":
                filtered_data = [d for d in filtered_data if d["harvest_date"].startswith("2024")]
            elif time_period == "previous_year":
                filtered_data = [d for d in filtered_data if d["harvest_date"].startswith("2023")]

            if crops:
                filtered_data = [d for d in filtered_data if d["crop"] in crops]

            if parcels:
                filtered_data = [d for d in filtered_data if d["parcel"] in parcels]

            return filtered_data

        except Exception as e:
            logger.error(f"Database query error: {e}")
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
