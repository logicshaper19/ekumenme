"""
Analyze Trends Tool - Single Purpose Tool

Job: Calculate year-over-year trends from farm data.
Input: JSON string of records from GetFarmDataTool
Output: JSON string with trend analysis

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

class AnalyzeTrendsTool(BaseTool):
    """
    Tool: Calculate year-over-year trends from farm data.
    
    Job: Take farm data records and calculate trends over time.
    Input: JSON string of records from GetFarmDataTool
    Output: JSON string with trend analysis
    """
    
    name: str = "analyze_trends_tool"
    description: str = "Analyse les tendances année par année des données d'exploitation"
    
    def _run(
        self,
        records_json: str,
        **kwargs
    ) -> str:
        """
        Analyzes year-over-year trends from farm data records.
        """
        try:
            data = json.loads(records_json)
            
            if "error" in data:
                return records_json  # Pass through errors
            
            records_data = data.get("records", [])
            if not records_data:
                return json.dumps({"error": "Aucune donnée fournie pour l'analyse des tendances"})
            
            # Convert back to FarmDataRecord objects for processing
            records = [FarmDataRecord(**record_dict) for record_dict in records_data]
            
            # Analyze trends
            trend_analysis = self._analyze_trends(records)
            
            # Calculate trend insights
            trend_insights = self._generate_trend_insights(trend_analysis)
            
            result = {
                "trend_analysis": trend_analysis,
                "trend_insights": trend_insights,
                "total_records": len(records)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Analyze trends error: {e}")
            return json.dumps({"error": f"Erreur lors de l'analyse des tendances: {str(e)}"})
    
    def _analyze_trends(self, records: List[FarmDataRecord]) -> Dict[str, Any]:
        """Analyze trends from farm data records."""
        # Group records by year
        yearly_data = {}
        for record in records:
            year = record.date[:4]
            if year not in yearly_data:
                yearly_data[year] = []
            yearly_data[year].append(record)
        
        if len(yearly_data) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        # Calculate yearly metrics
        yearly_metrics = {}
        for year, year_records in yearly_data.items():
            total_surface = sum(r.surface for r in year_records)
            total_yield = sum(r.yield_value * r.surface for r in year_records)
            total_cost = sum(r.cost_per_hectare * r.surface for r in year_records)
            total_quality = sum(r.quality_score for r in year_records)
            
            yearly_metrics[year] = {
                "average_yield": round(total_yield / total_surface, 2) if total_surface > 0 else 0,
                "average_cost": round(total_cost / total_surface, 2) if total_surface > 0 else 0,
                "average_quality": round(total_quality / len(year_records), 2),
                "total_surface": round(total_surface, 2),
                "record_count": len(year_records)
            }
        
        # Calculate trends
        trends = self._calculate_trends(yearly_metrics)
        
        # Calculate crop-specific trends
        crop_trends = self._calculate_crop_trends(records)
        
        return {
            "yearly_metrics": yearly_metrics,
            "overall_trends": trends,
            "crop_trends": crop_trends
        }
    
    def _calculate_trends(self, yearly_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall trends from yearly metrics."""
        years = sorted(yearly_metrics.keys())
        if len(years) < 2:
            return {"error": "Insufficient years for trend calculation"}
        
        first_year = years[0]
        last_year = years[-1]
        
        first_metrics = yearly_metrics[first_year]
        last_metrics = yearly_metrics[last_year]
        
        # Calculate percentage changes
        yield_change = self._calculate_percentage_change(first_metrics["average_yield"], last_metrics["average_yield"])
        cost_change = self._calculate_percentage_change(first_metrics["average_cost"], last_metrics["average_cost"])
        quality_change = self._calculate_percentage_change(first_metrics["average_quality"], last_metrics["average_quality"])
        
        return {
            "yield_trend": {
                "change_percent": yield_change,
                "trend_direction": "increasing" if yield_change > 5 else "decreasing" if yield_change < -5 else "stable",
                "first_year_value": first_metrics["average_yield"],
                "last_year_value": last_metrics["average_yield"]
            },
            "cost_trend": {
                "change_percent": cost_change,
                "trend_direction": "increasing" if cost_change > 5 else "decreasing" if cost_change < -5 else "stable",
                "first_year_value": first_metrics["average_cost"],
                "last_year_value": last_metrics["average_cost"]
            },
            "quality_trend": {
                "change_percent": quality_change,
                "trend_direction": "increasing" if quality_change > 5 else "decreasing" if quality_change < -5 else "stable",
                "first_year_value": first_metrics["average_quality"],
                "last_year_value": last_metrics["average_quality"]
            }
        }
    
    def _calculate_crop_trends(self, records: List[FarmDataRecord]) -> Dict[str, Any]:
        """Calculate trends by crop."""
        crop_trends = {}
        
        # Group by crop and year
        crop_yearly_data = {}
        for record in records:
            crop = record.crop
            year = record.date[:4]
            
            if crop not in crop_yearly_data:
                crop_yearly_data[crop] = {}
            if year not in crop_yearly_data[crop]:
                crop_yearly_data[crop][year] = []
            
            crop_yearly_data[crop][year].append(record)
        
        # Calculate trends for each crop
        for crop, yearly_data in crop_yearly_data.items():
            if len(yearly_data) < 2:
                continue
            
            years = sorted(yearly_data.keys())
            first_year = years[0]
            last_year = years[-1]
            
            first_records = yearly_data[first_year]
            last_records = yearly_data[last_year]
            
            first_avg_yield = sum(r.yield_value for r in first_records) / len(first_records)
            last_avg_yield = sum(r.yield_value for r in last_records) / len(last_records)
            
            yield_change = self._calculate_percentage_change(first_avg_yield, last_avg_yield)
            
            crop_trends[crop] = {
                "yield_trend": {
                    "change_percent": yield_change,
                    "trend_direction": "increasing" if yield_change > 5 else "decreasing" if yield_change < -5 else "stable",
                    "first_year_value": round(first_avg_yield, 2),
                    "last_year_value": round(last_avg_yield, 2)
                }
            }
        
        return crop_trends
    
    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change between two values."""
        if old_value == 0:
            return 0
        return round(((new_value - old_value) / old_value) * 100, 1)
    
    def _generate_trend_insights(self, trend_analysis: Dict[str, Any]) -> List[str]:
        """Generate trend insights."""
        insights = []
        
        if "error" in trend_analysis:
            insights.append("❌ Données insuffisantes pour l'analyse des tendances")
            return insights
        
        overall_trends = trend_analysis.get("overall_trends", {})
        
        # Yield trend insights
        yield_trend = overall_trends.get("yield_trend", {})
        if yield_trend.get("trend_direction") == "increasing":
            insights.append(f"📈 Rendement en hausse: +{yield_trend.get('change_percent', 0)}%")
        elif yield_trend.get("trend_direction") == "decreasing":
            insights.append(f"📉 Rendement en baisse: {yield_trend.get('change_percent', 0)}%")
        else:
            insights.append("📊 Rendement stable")
        
        # Cost trend insights
        cost_trend = overall_trends.get("cost_trend", {})
        if cost_trend.get("trend_direction") == "increasing":
            insights.append(f"💰 Coûts en hausse: +{cost_trend.get('change_percent', 0)}%")
        elif cost_trend.get("trend_direction") == "decreasing":
            insights.append(f"💰 Coûts en baisse: {cost_trend.get('change_percent', 0)}%")
        else:
            insights.append("💰 Coûts stables")
        
        # Quality trend insights
        quality_trend = overall_trends.get("quality_trend", {})
        if quality_trend.get("trend_direction") == "increasing":
            insights.append(f"⭐ Qualité en amélioration: +{quality_trend.get('change_percent', 0)}%")
        elif quality_trend.get("trend_direction") == "decreasing":
            insights.append(f"⭐ Qualité en baisse: {quality_trend.get('change_percent', 0)}%")
        else:
            insights.append("⭐ Qualité stable")
        
        # Crop-specific insights
        crop_trends = trend_analysis.get("crop_trends", {})
        for crop, trends in crop_trends.items():
            yield_trend = trends.get("yield_trend", {})
            if yield_trend.get("trend_direction") == "increasing":
                insights.append(f"🌾 {crop}: Rendement en hausse (+{yield_trend.get('change_percent', 0)}%)")
            elif yield_trend.get("trend_direction") == "decreasing":
                insights.append(f"🌾 {crop}: Rendement en baisse ({yield_trend.get('change_percent', 0)}%)")
        
        return insights
