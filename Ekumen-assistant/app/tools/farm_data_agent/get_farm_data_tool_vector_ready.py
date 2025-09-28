"""
Get Farm Data Tool - Vector Database Ready Tool

Job: Retrieve raw farm data records based on filters.
Input: Structured filters (time_period, crops, parcels)
Output: JSON string of FarmDataRecord objects

Enhanced Features:
- External knowledge base (JSON file)
- Configurable analysis parameters
- Asynchronous support
- Comprehensive input validation
- Vector database ready architecture

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

# Import configuration system
from ...config.farm_data_config import get_farm_data_config

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

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class GetFarmDataTool(BaseTool):
    """
    Vector Database Ready Tool: Retrieve raw farm data records based on filters.
    
    Job: Get data records from database/mock data based on filters.
    Input: Structured filters (time_period, crops, parcels)
    Output: JSON string of FarmDataRecord objects
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "get_farm_data_tool"
    description: str = "Récupère les données brutes de l'exploitation avec analyse avancée"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self._config_cache = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "farm_data_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_farm_data_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading farm data knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        time_period: Optional[str] = None,
        crops: Optional[List[str]] = None,
        parcels: Optional[List[str]] = None
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Check if at least one filter is provided
        if config.require_at_least_one_filter:
            if not any([time_period, crops, parcels]):
                errors.append(ValidationError("filters", "At least one filter must be provided", "error"))
        
        # Validate time period
        if time_period and config.validate_time_period:
            knowledge_base = self._load_knowledge_base()
            time_periods = knowledge_base.get("data_filters", {}).get("time_periods", {})
            if time_period not in time_periods:
                errors.append(ValidationError("time_period", f"Unknown time period: {time_period}", "error"))
        
        # Validate crop types
        if crops and config.validate_crop_types:
            knowledge_base = self._load_knowledge_base()
            valid_crops = knowledge_base.get("data_filters", {}).get("crop_types", [])
            invalid_crops = [crop for crop in crops if crop.lower() not in valid_crops]
            if invalid_crops:
                errors.append(ValidationError("crops", f"Unknown crop types: {invalid_crops}", "warning"))
        
        # Validate parcel types
        if parcels and config.validate_parcel_types:
            knowledge_base = self._load_knowledge_base()
            valid_parcels = knowledge_base.get("data_filters", {}).get("parcel_types", [])
            invalid_parcels = [parcel for parcel in parcels if parcel not in valid_parcels]
            if invalid_parcels:
                errors.append(ValidationError("parcels", f"Unknown parcel types: {invalid_parcels}", "warning"))
        
        return errors
    
    def _filter_farm_data(
        self, 
        time_period: Optional[str] = None,
        crops: Optional[List[str]] = None,
        parcels: Optional[List[str]] = None,
        knowledge_base: Dict[str, Any] = None
    ) -> List[FarmDataRecord]:
        """Filter farm data based on provided criteria."""
        if not knowledge_base:
            knowledge_base = self._load_knowledge_base()
        
        mock_data = knowledge_base.get("mock_farm_data", [])
        data_filters = knowledge_base.get("data_filters", {})
        
        # Convert mock data to FarmDataRecord objects
        records = [FarmDataRecord(**record) for record in mock_data]
        
        # Apply time period filter
        if time_period:
            time_periods = data_filters.get("time_periods", {})
            if time_period in time_periods:
                period_value = time_periods[time_period]
                if isinstance(period_value, str):
                    # Single year
                    records = [r for r in records if r.date.startswith(period_value)]
                elif isinstance(period_value, list):
                    # Multiple years
                    records = [r for r in records if any(r.date.startswith(year) for year in period_value)]
        
        # Apply crop filter
        if crops:
            crops_lower = [crop.lower() for crop in crops]
            records = [r for r in records if r.crop.lower() in crops_lower]
        
        # Apply parcel filter
        if parcels:
            records = [r for r in records if r.parcel in parcels]
        
        return records
    
    def _run(
        self,
        time_period: Optional[str] = None,
        crops: Optional[List[str]] = None,
        parcels: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Retrieve raw farm data records based on filters.
        
        Args:
            time_period: Time period filter (current_year, previous_year, last_3_years, last_5_years)
            crops: List of crop types to filter by
            parcels: List of parcel identifiers to filter by
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(time_period, crops, parcels)
            config = self._get_config()
            
            if validation_errors and config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Load knowledge base
            knowledge_base = self._load_knowledge_base()
            
            # Filter farm data
            filtered_records = self._filter_farm_data(time_period, crops, parcels, knowledge_base)
            
            # Limit results if configured
            if len(filtered_records) > config.max_records_returned:
                filtered_records = filtered_records[:config.max_records_returned]
            
            # Calculate summary statistics
            total_surface = sum(record.surface for record in filtered_records)
            total_yield = sum(record.yield_value * record.surface for record in filtered_records)
            total_cost = sum(record.cost_per_hectare * record.surface for record in filtered_records)
            avg_quality = sum(record.quality_score for record in filtered_records) / len(filtered_records) if filtered_records else 0
            
            result = {
                "filters_applied": {
                    "time_period": time_period,
                    "crops": crops,
                    "parcels": parcels
                },
                "records": [asdict(record) for record in filtered_records],
                "summary": {
                    "total_records": len(filtered_records),
                    "total_surface_ha": round(total_surface, 2),
                    "total_yield_production": round(total_yield, 2),
                    "total_cost_eur": round(total_cost, 2),
                    "average_quality_score": round(avg_quality, 2)
                },
                "analysis_metadata": {
                    "config_used": asdict(config),
                    "knowledge_base_version": knowledge_base.get("metadata", {}).get("version", "unknown")
                }
            }
            
            # Add validation warnings if any
            if validation_errors and config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Get farm data error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la récupération des données d'exploitation: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        time_period: Optional[str] = None,
        crops: Optional[List[str]] = None,
        parcels: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of farm data retrieval.
        """
        # For now, just call the sync version
        return self._run(time_period, crops, parcels, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
