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
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

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
        **kwargs
    ) -> str:
        """
        Retrieves farm data records based on filters for time period, crops, or parcels.
        Returns the data as a JSON string.
        """
        try:
            # Get farm data
            farm_data = self._retrieve_farm_data(time_period, crops, parcels)
            
            # Convert to JSON-serializable format
            records_as_dicts = [asdict(record) for record in farm_data]
            
            return json.dumps({
                "records": records_as_dicts,
                "total_records": len(farm_data),
                "filters": {
                    "time_period": time_period,
                    "crops": crops,
                    "parcels": parcels
                }
            }, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Get farm data error: {e}")
            return json.dumps({"error": f"Erreur lors de la récupération des données: {str(e)}"})
    
    def _retrieve_farm_data(self, time_period: str = None, crops: List[str] = None, parcels: List[str] = None) -> List[FarmDataRecord]:
        """Retrieve farm data based on filters."""
        # Mock farm data - in production would query database
        mock_data = [
            FarmDataRecord("Parcelle A", "blé", 15.5, 72.3, "2024-08-15", 450.0, 8.2),
            FarmDataRecord("Parcelle B", "maïs", 12.0, 95.8, "2024-09-20", 520.0, 8.7),
            FarmDataRecord("Parcelle C", "colza", 8.5, 35.2, "2024-07-10", 380.0, 7.9),
            FarmDataRecord("Parcelle A", "blé", 15.5, 68.5, "2023-08-20", 420.0, 7.8),
            FarmDataRecord("Parcelle B", "maïs", 12.0, 88.2, "2023-09-25", 480.0, 8.1),
            FarmDataRecord("Parcelle C", "colza", 8.5, 32.8, "2023-07-15", 350.0, 7.5),
            FarmDataRecord("Parcelle D", "blé", 20.0, 75.1, "2024-08-18", 460.0, 8.4),
            FarmDataRecord("Parcelle E", "maïs", 18.5, 92.3, "2024-09-22", 510.0, 8.6)
        ]
        
        # Apply filters
        filtered_data = mock_data
        
        if time_period:
            if time_period == "current_year":
                filtered_data = [d for d in filtered_data if d.date.startswith("2024")]
            elif time_period == "previous_year":
                filtered_data = [d for d in filtered_data if d.date.startswith("2023")]
        
        if crops:
            filtered_data = [d for d in filtered_data if d.crop in crops]
        
        if parcels:
            filtered_data = [d for d in filtered_data if d.parcel in parcels]
        
        return filtered_data
