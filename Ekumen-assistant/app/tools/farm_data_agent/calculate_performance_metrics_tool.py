"""
Calculate Performance Metrics Tool - Single Purpose Tool

Job: Calculate performance metrics from farm data records.
Input: JSON string of records from GetFarmDataTool
Output: JSON string with calculated metrics

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
from dataclasses import dataclass

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

class CalculatePerformanceMetricsTool(BaseTool):
    """
    Tool: Calculate performance metrics from farm data records.
    
    Job: Take farm data records and calculate key performance metrics.
    Input: JSON string of records from GetFarmDataTool
    Output: JSON string with calculated metrics
    """
    
    name: str = "calculate_performance_metrics_tool"
    description: str = "Calcule les métriques de performance à partir des données d'exploitation"
    
    def _run(
        self,
        records_json: str,
        **kwargs
    ) -> str:
        """
        Calculates performance metrics from a list of farm records.
        Input should be a JSON string of records from the get_farm_records tool.
        """
        try:
            data = json.loads(records_json)
            
            if "error" in data:
                return records_json  # Pass through errors
            
            records_data = data.get("records", [])
            if not records_data:
                return json.dumps({"error": "Aucune donnée fournie pour le calcul des métriques"})
            
            # Convert back to FarmDataRecord objects for processing
            records = [FarmDataRecord(**record_dict) for record_dict in records_data]
            
            # Calculate metrics
            metrics = self._calculate_metrics(records)
            
            # Calculate crop-specific metrics
            crop_metrics = self._calculate_crop_metrics(records)
            
            # Calculate parcel metrics
            parcel_metrics = self._calculate_parcel_metrics(records)
            
            result = {
                "overall_metrics": metrics,
                "crop_metrics": crop_metrics,
                "parcel_metrics": parcel_metrics,
                "total_records": len(records)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Calculate performance metrics error: {e}")
            return json.dumps({"error": f"Erreur lors du calcul des métriques: {str(e)}"})
    
    def _calculate_metrics(self, records: List[FarmDataRecord]) -> Dict[str, Any]:
        """Calculate overall performance metrics."""
        if not records:
            return {"error": "No records provided"}
        
        total_surface = sum(r.surface for r in records)
        if total_surface == 0:
            return {"error": "Total surface is zero"}
        
        total_yield_production = sum(r.yield_value * r.surface for r in records)
        average_yield = total_yield_production / total_surface
        
        total_cost = sum(r.cost_per_hectare * r.surface for r in records)
        average_cost = total_cost / total_surface
        
        average_quality = sum(r.quality_score for r in records) / len(records)
        
        # Calculate yield trend
        yield_trend = self._calculate_yield_trend(records)
        
        return {
            "total_surface_ha": round(total_surface, 2),
            "average_yield_q_ha": round(average_yield, 2),
            "total_cost_eur": round(total_cost, 2),
            "average_cost_eur_ha": round(average_cost, 2),
            "average_quality_score": round(average_quality, 2),
            "yield_trend": yield_trend,
            "record_count": len(records)
        }
    
    def _calculate_crop_metrics(self, records: List[FarmDataRecord]) -> Dict[str, Any]:
        """Calculate metrics by crop."""
        crop_metrics = {}
        
        for record in records:
            if record.crop not in crop_metrics:
                crop_metrics[record.crop] = {
                    "total_surface": 0,
                    "total_yield": 0,
                    "total_cost": 0,
                    "quality_scores": [],
                    "records": []
                }
            
            crop_metrics[record.crop]["total_surface"] += record.surface
            crop_metrics[record.crop]["total_yield"] += record.yield_value * record.surface
            crop_metrics[record.crop]["total_cost"] += record.cost_per_hectare * record.surface
            crop_metrics[record.crop]["quality_scores"].append(record.quality_score)
            crop_metrics[record.crop]["records"].append(record)
        
        # Calculate averages
        for crop, metrics in crop_metrics.items():
            if metrics["total_surface"] > 0:
                metrics["average_yield"] = round(metrics["total_yield"] / metrics["total_surface"], 2)
                metrics["average_cost"] = round(metrics["total_cost"] / metrics["total_surface"], 2)
            metrics["average_quality"] = round(sum(metrics["quality_scores"]) / len(metrics["quality_scores"]), 2)
            metrics["record_count"] = len(metrics["records"])
        
        return crop_metrics
    
    def _calculate_parcel_metrics(self, records: List[FarmDataRecord]) -> Dict[str, Any]:
        """Calculate metrics by parcel."""
        parcel_metrics = {}
        
        for record in records:
            if record.parcel not in parcel_metrics:
                parcel_metrics[record.parcel] = {
                    "total_surface": 0,
                    "total_yield": 0,
                    "total_cost": 0,
                    "quality_scores": [],
                    "records": []
                }
            
            parcel_metrics[record.parcel]["total_surface"] += record.surface
            parcel_metrics[record.parcel]["total_yield"] += record.yield_value * record.surface
            parcel_metrics[record.parcel]["total_cost"] += record.cost_per_hectare * record.surface
            parcel_metrics[record.parcel]["quality_scores"].append(record.quality_score)
            parcel_metrics[record.parcel]["records"].append(record)
        
        # Calculate averages
        for parcel, metrics in parcel_metrics.items():
            if metrics["total_surface"] > 0:
                metrics["average_yield"] = round(metrics["total_yield"] / metrics["total_surface"], 2)
                metrics["average_cost"] = round(metrics["total_cost"] / metrics["total_surface"], 2)
            metrics["average_quality"] = round(sum(metrics["quality_scores"]) / len(metrics["quality_scores"]), 2)
            metrics["record_count"] = len(metrics["records"])
        
        return parcel_metrics
    
    def _calculate_yield_trend(self, records: List[FarmDataRecord]) -> str:
        """Calculate yield trend over time."""
        if len(records) < 2:
            return "insufficient_data"
        
        # Sort by date
        sorted_records = sorted(records, key=lambda r: r.date)
        
        # Calculate average yield for each year
        yearly_yields = {}
        for record in sorted_records:
            year = record.date[:4]
            if year not in yearly_yields:
                yearly_yields[year] = []
            yearly_yields[year].append(record.yield_value)
        
        if len(yearly_yields) < 2:
            return "insufficient_data"
        
        # Calculate trend
        years = sorted(yearly_yields.keys())
        first_year_avg = sum(yearly_yields[years[0]]) / len(yearly_yields[years[0]])
        last_year_avg = sum(yearly_yields[years[-1]]) / len(yearly_yields[years[-1]])
        
        if last_year_avg > first_year_avg * 1.05:
            return "increasing"
        elif last_year_avg < first_year_avg * 0.95:
            return "decreasing"
        else:
            return "stable"
