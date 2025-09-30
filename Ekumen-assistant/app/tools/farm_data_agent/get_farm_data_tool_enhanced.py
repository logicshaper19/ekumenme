"""
Enhanced Get Farm Data Tool with DATABASE INTEGRATION.

REAL DATABASE INTEGRATION:
- MesParcelles database for farm data
- SIRET-based multi-tenancy
- Millesime (vintage year) tracking
- Real parcel and intervention data
- Extracts yield, cost, and quality data from interventions

Improvements:
- Type-safe Pydantic schemas
- Redis caching (1h TTL for farm data)
- Structured error handling
- Real database queries with eager loading (prevents N+1)
- Async-safe database access
- MesParcelles API integration (mock for now)
"""

import logging
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from langchain.tools import StructuredTool

from app.tools.schemas.farm_data_schemas import (
    FarmDataInput,
    FarmDataOutput,
    ParcelRecord,
    InterventionSummary,
    TimePeriod
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


# Intervention type constants (from MesParcelles database)
class InterventionType:
    """Intervention type IDs from types_intervention table"""
    SEMIS = 1
    FERTILISATION = 2
    TRAITEMENT_PHYTO = 3
    RECOLTE = 4
    IRRIGATION = 5
    TRAVAIL_SOL = 6


class EnhancedFarmDataService:
    """Service for fetching farm data with caching"""

    @redis_cache(ttl=3600, model_class=FarmDataOutput, category="farm_data")
    async def get_farm_data(self, input_data: FarmDataInput) -> FarmDataOutput:
        """
        Get farm data from database and MesParcelles API
        
        Args:
            input_data: Validated input
            
        Returns:
            FarmDataOutput with farm records
            
        Raises:
            ValueError: If database query fails
        """
        try:
            # Get data from MesParcelles database
            database_records = await self._get_database_farm_data(
                time_period=input_data.time_period,
                crops=input_data.crops,
                parcels=input_data.parcels,
                farm_id=input_data.farm_id
            )
            
            result = FarmDataOutput(
                success=True,
                database_records=database_records,
                total_records=len(database_records),
                filters={
                    "time_period": input_data.time_period.value if input_data.time_period else None,
                    "crops": input_data.crops,
                    "parcels": input_data.parcels,
                    "farm_id": input_data.farm_id
                },
                data_sources=["local_database"]
            )
            
            # Add MesParcelles API data if requested
            if input_data.use_mesparcelles:
                try:
                    mesparcelles_data = await self._get_mesparcelles_data(
                        farm_id=input_data.farm_id,
                        parcels=input_data.parcels
                    )
                    result.mesparcelles_data = mesparcelles_data
                    result.data_sources.append("mesparcelles_api")
                except Exception as e:
                    logger.warning(f"MesParcelles integration failed: {e}")
                    result.mesparcelles_error = str(e)
            
            logger.info(f"✅ Retrieved {len(database_records)} parcels for farm {input_data.farm_id}")
            return result
            
        except Exception as e:
            logger.error(f"Farm data retrieval error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de la récupération des données: {str(e)}")

    async def _get_database_farm_data(
        self,
        time_period: Optional[TimePeriod] = None,
        crops: Optional[List[str]] = None,
        parcels: Optional[List[str]] = None,
        farm_id: Optional[str] = None,
        max_results: int = 100
    ) -> List[ParcelRecord]:
        """
        Async wrapper for database farm data retrieval.

        Runs synchronous database query in thread pool to avoid blocking event loop.
        """
        return await asyncio.to_thread(
            self._get_database_farm_data_sync,
            time_period,
            crops,
            parcels,
            farm_id,
            max_results
        )

    def _get_database_farm_data_sync(
        self,
        time_period: Optional[TimePeriod] = None,
        crops: Optional[List[str]] = None,
        parcels: Optional[List[str]] = None,
        farm_id: Optional[str] = None,
        max_results: int = 100
    ) -> List[ParcelRecord]:
        """
        Get farm data from MesParcelles database (synchronous).

        Uses eager loading to prevent N+1 query problem.
        Limited to max_results to prevent memory issues.
        """
        try:
            # TODO: Remove sys.path manipulation - fix PYTHONPATH in deployment
            # This is a temporary workaround for development environment
            import sys
            import os
            backend_path = os.path.join(os.path.dirname(__file__), '../../../../Ekumenbackend')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)

            # Import with validation
            try:
                from app.models.mesparcelles import Parcelle, SuccessionCulture, Culture, Intervention
                from app.core.database import SessionLocal
                from sqlalchemy import select, func
                from sqlalchemy.orm import joinedload
                from sqlalchemy.exc import SQLAlchemyError
            except ImportError as e:
                logger.error(f"Failed to import MesParcelles models: {e}")
                logger.error("Check PYTHONPATH configuration and database setup")
                return []

            # Use synchronous session
            with SessionLocal() as db:
                # Query parcelles with eager loading to prevent N+1 queries
                query = select(Parcelle).options(
                    joinedload(Parcelle.succession_cultures).joinedload(SuccessionCulture.culture),
                    joinedload(Parcelle.interventions).joinedload(Intervention.extrants),
                    joinedload(Parcelle.interventions).joinedload(Intervention.intrants)
                )

                # Filter by farm_id (SIRET)
                if farm_id:
                    query = query.where(Parcelle.siret_exploitation == farm_id)

                # Filter by millesime (year) if time_period specified
                current_year = datetime.now().year
                if time_period == TimePeriod.CURRENT_YEAR:
                    query = query.where(Parcelle.millesime == current_year)
                elif time_period == TimePeriod.PREVIOUS_YEAR:
                    query = query.where(Parcelle.millesime == current_year - 1)
                elif time_period == TimePeriod.LAST_3_YEARS:
                    query = query.where(Parcelle.millesime >= current_year - 3)

                # Filter by parcel names if specified
                if parcels:
                    query = query.where(Parcelle.nom.in_(parcels))

                # Check total count before pagination
                count_query = select(func.count()).select_from(Parcelle)
                if farm_id:
                    count_query = count_query.where(Parcelle.siret_exploitation == farm_id)
                total_count = db.execute(count_query).scalar()

                # Add pagination to prevent memory issues
                query = query.limit(max_results)

                # Warn if results are truncated
                if total_count > max_results:
                    logger.warning(
                        f"Results limited to {max_results} of {total_count} parcels. "
                        f"Increase max_results or add more specific filters."
                    )

                # Execute query with unique() to handle joinedload duplicates
                result = db.execute(query)
                parcel_records = result.scalars().unique().all()

                # Convert to Pydantic models
                farm_data = []
                for parcelle in parcel_records:
                    # Get culture names from eager-loaded succession_cultures
                    culture_names = []
                    if hasattr(parcelle, 'succession_cultures'):
                        for sc in parcelle.succession_cultures:
                            if sc.culture:
                                culture_names.append(sc.culture.libelle)

                    # Filter by crops if specified
                    if crops and not any(crop in culture_names for crop in crops):
                        continue

                    # Get interventions from eager-loaded data (no extra query!)
                    interventions = parcelle.interventions if hasattr(parcelle, 'interventions') else []

                    # Extract intervention summary with real data
                    intervention_summary = self._extract_intervention_summary(
                        interventions,
                        parcelle.surface_mesuree_ha
                    )

                    farm_data.append(ParcelRecord(
                        id=str(parcelle.uuid_parcelle),
                        farm_id=parcelle.siret_exploitation,
                        parcel=parcelle.nom or f"Parcelle {parcelle.uuid_parcelle}",
                        millesime=parcelle.millesime,
                        surface_ha=float(parcelle.surface_mesuree_ha) if parcelle.surface_mesuree_ha else 0.0,
                        commune=parcelle.insee_commune,
                        cultures=culture_names,
                        nb_interventions=len(interventions),
                        intervention_summary=intervention_summary,
                        created_at=parcelle.created_at.isoformat() if parcelle.created_at else None,
                        updated_at=parcelle.updated_at.isoformat() if parcelle.updated_at else None
                    ))

                logger.info(f"✅ Retrieved {len(farm_data)} parcels from MesParcelles database")
                return farm_data

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error: {e}", exc_info=True)
            logger.warning("Returning empty result due to database error")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error in farm data retrieval: {e}", exc_info=True)
            logger.warning("Returning empty result")
            return []

    def _extract_intervention_summary(
        self,
        interventions: List[Any],
        surface_ha: Optional[float]
    ) -> InterventionSummary:
        """
        Extract intervention summary with real data from MesParcelles interventions.

        Extracts:
        - Harvest data from extrants (outputs)
        - Cost data from intrants (inputs) - NOT IMPLEMENTED (requires price database)
        - Intervention type counts
        """
        if not interventions:
            return InterventionSummary(
                total_interventions=0,
                harvest_interventions=0,
                fertilization_interventions=0,
                pest_control_interventions=0,
                has_real_data=False
            )

        # Count intervention types
        harvest_count = 0
        fertilization_count = 0
        pest_control_count = 0

        # Track harvest and cost data
        total_harvest_kg = 0.0
        has_harvest_data = False

        for intervention in interventions:
            # Count by type using constants
            type_id = intervention.id_type_intervention
            if type_id == InterventionType.RECOLTE:
                harvest_count += 1

                # Extract harvest quantity from extrants with proper JSON validation
                if hasattr(intervention, 'extrants') and intervention.extrants:
                    for extrant in intervention.extrants:
                        if not extrant.extrant_details:
                            continue

                        try:
                            # Handle both JSON string and dict
                            if isinstance(extrant.extrant_details, str):
                                details = json.loads(extrant.extrant_details)
                            elif isinstance(extrant.extrant_details, dict):
                                details = extrant.extrant_details
                            else:
                                logger.warning(f"Unexpected extrant_details type: {type(extrant.extrant_details)}")
                                continue

                            # Try multiple field names for quantity
                            quantity = details.get('quantite_kg') or details.get('quantite') or details.get('quantity_kg')
                            if quantity is not None:
                                total_harvest_kg += float(quantity)
                                has_harvest_data = True
                        except (json.JSONDecodeError, ValueError, TypeError) as e:
                            logger.warning(f"Failed to parse extrant details: {e}")
                            continue

            elif type_id == InterventionType.FERTILISATION:
                fertilization_count += 1
            elif type_id == InterventionType.TRAITEMENT_PHYTO:
                pest_control_count += 1

        # Calculate yield if we have harvest data and surface
        average_yield_q_ha = None
        if has_harvest_data and surface_ha and surface_ha > 0:
            # Convert kg to quintals (1 quintal = 100 kg)
            total_harvest_q = total_harvest_kg / 100.0
            average_yield_q_ha = round(total_harvest_q / float(surface_ha), 2)

        # Cost data not implemented (requires price database)
        # Setting to None to be honest about missing data

        return InterventionSummary(
            total_interventions=len(interventions),
            harvest_interventions=harvest_count,
            fertilization_interventions=fertilization_count,
            pest_control_interventions=pest_control_count,
            total_harvest_quantity=round(total_harvest_kg, 2) if has_harvest_data else None,
            average_yield_q_ha=average_yield_q_ha,
            total_cost_eur=None,  # Not implemented - requires price database
            average_cost_eur_ha=None,  # Not implemented - requires price database
            has_real_data=has_harvest_data  # Only harvest data available for now
        )

    async def _get_mesparcelles_data(
        self,
        farm_id: Optional[str] = None,
        parcels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get data from MesParcelles API (mock for now)"""
        try:
            # TODO: Replace with actual MesParcelles API calls
            return {
                "api_status": "connected",
                "farm_profile": {
                    "farm_id": farm_id or "FR_FARM_123456",
                    "siret": farm_id or "12345678901234",
                    "total_surface_ha": 156.5,
                    "main_crops": ["blé", "maïs", "colza", "orge"],
                    "certification": "HVE_niveau_2",
                    "region": "Normandie",
                    "department": "Calvados"
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


async def get_farm_data_enhanced(
    time_period: Optional[str] = None,
    crops: Optional[List[str]] = None,
    parcels: Optional[List[str]] = None,
    farm_id: Optional[str] = None,
    use_mesparcelles: bool = True
) -> str:
    """
    Async wrapper for get farm data tool
    
    Args:
        time_period: Time period filter (e.g., 'current_year', 'last_season')
        crops: List of crop types to filter by
        parcels: List of parcel IDs to filter by
        farm_id: Specific farm ID (SIRET) for targeted data retrieval
        use_mesparcelles: Whether to include MesParcelles API data
        
    Returns:
        JSON string with farm data
    """
    try:
        # Validate inputs
        input_data = FarmDataInput(
            time_period=TimePeriod(time_period) if time_period else None,
            crops=crops,
            parcels=parcels,
            farm_id=farm_id,
            use_mesparcelles=use_mesparcelles
        )
        
        # Execute service
        service = EnhancedFarmDataService()
        result = await service.get_farm_data(input_data)
        
        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        logger.error(f"Farm data validation error: {e}")
        error_result = FarmDataOutput(
            success=False,
            database_records=[],
            total_records=0,
            filters={},
            data_sources=[],
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
        
    except Exception as e:
        logger.error(f"Unexpected farm data error: {e}", exc_info=True)
        error_result = FarmDataOutput(
            success=False,
            database_records=[],
            total_records=0,
            filters={},
            data_sources=[],
            error="Erreur inattendue lors de la récupération des données. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
get_farm_data_tool_enhanced = StructuredTool.from_function(
    func=get_farm_data_enhanced,
    name="get_farm_data",
    description="""Récupère les données brutes de l'exploitation depuis la base MesParcelles.

Retourne des données détaillées avec:
- Parcelles et surfaces
- Cultures et rotations
- Interventions agricoles
- Données MesParcelles API (optionnel)

Utilisez cet outil quand les agriculteurs demandent leurs données d'exploitation, parcelles, ou historique cultural.""",
    args_schema=FarmDataInput,
    return_direct=False,
    coroutine=get_farm_data_enhanced,
    handle_validation_error=True
)

