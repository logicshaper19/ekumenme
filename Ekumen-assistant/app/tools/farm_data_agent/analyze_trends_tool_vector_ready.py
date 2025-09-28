"""
Analyze Trends Tool - Vector Database Ready Tool

Job: Calculate year-over-year trends from farm data.
Input: JSON string of records from GetFarmDataTool
Output: JSON string with trend analysis

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
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
from collections import defaultdict

# Import configuration system
from ...config.trend_analysis_config import get_trend_analysis_config

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
class TrendData:
    """Structured trend data."""
    year: str
    yield_value: float
    cost_per_hectare: float
    quality_score: float
    surface: float

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class AnalyzeTrendsTool(BaseTool):
    """
    Vector Database Ready Tool: Calculate year-over-year trends from farm data.
    
    Job: Take farm data records and calculate trends over time.
    Input: JSON string of records from GetFarmDataTool
    Output: JSON string with trend analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "analyze_trends_tool"
    description: str = "Analyse les tendances année par année avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "trend_analysis_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_trend_analysis_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading trend analysis knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        records_json: str
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate records JSON
        if config.require_records:
            try:
                data = json.loads(records_json)
                if "error" in data:
                    errors.append(ValidationError("records_json", "Records data contains errors", "error"))
                elif not data.get("records"):
                    errors.append(ValidationError("records_json", "No records provided", "error"))
                else:
                    records = data.get("records", [])
                    if len(records) < config.min_records:
                        errors.append(ValidationError("records_json", f"Minimum {config.min_records} records required", "error"))
                    elif len(records) > config.max_records:
                        errors.append(ValidationError("records_json", f"Maximum {config.max_records} records allowed", "error"))
            except json.JSONDecodeError:
                errors.append(ValidationError("records_json", "Invalid JSON format", "error"))
        
        return errors
    
    def _group_records_by_year(
        self, 
        records: List[FarmDataRecord]
    ) -> Dict[str, List[FarmDataRecord]]:
        """Group records by year for trend analysis."""
        year_groups = defaultdict(list)
        
        for record in records:
            year = record.date[:4]  # Extract year from date
            year_groups[year].append(record)
        
        return dict(year_groups)
    
    def _calculate_yearly_averages(
        self, 
        year_groups: Dict[str, List[FarmDataRecord]]
    ) -> Dict[str, TrendData]:
        """Calculate yearly averages for trend analysis."""
        yearly_data = {}
        
        for year, records in year_groups.items():
            if not records:
                continue
            
            # Calculate weighted averages
            total_surface = sum(record.surface for record in records)
            if total_surface == 0:
                continue
            
            weighted_yield = sum(record.yield_value * record.surface for record in records) / total_surface
            weighted_cost = sum(record.cost_per_hectare * record.surface for record in records) / total_surface
            average_quality = statistics.mean(record.quality_score for record in records)
            
            yearly_data[year] = TrendData(
                year=year,
                yield_value=weighted_yield,
                cost_per_hectare=weighted_cost,
                quality_score=average_quality,
                surface=total_surface
            )
        
        return yearly_data
    
    def _calculate_trend_percentage(
        self, 
        current_value: float, 
        previous_value: float
    ) -> float:
        """Calculate percentage change between two values."""
        if previous_value == 0:
            return 0.0
        return ((current_value - previous_value) / previous_value) * 100
    
    def _analyze_yield_trends(
        self, 
        yearly_data: Dict[str, TrendData], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze yield trends over time."""
        if len(yearly_data) < 2:
            return {"error": "Insufficient data for yield trend analysis"}
        
        # Sort by year
        sorted_years = sorted(yearly_data.keys())
        
        # Calculate year-over-year changes
        yield_changes = []
        for i in range(1, len(sorted_years)):
            current_year = sorted_years[i]
            previous_year = sorted_years[i-1]
            
            current_yield = yearly_data[current_year].yield_value
            previous_yield = yearly_data[previous_year].yield_value
            
            change_percent = self._calculate_trend_percentage(current_yield, previous_yield)
            yield_changes.append({
                "year": current_year,
                "previous_year": previous_year,
                "current_yield": current_yield,
                "previous_yield": previous_yield,
                "change_percent": round(change_percent, 2)
            })
        
        # Calculate overall trend
        if yield_changes:
            avg_change = statistics.mean(change["change_percent"] for change in yield_changes)
            
            # Determine trend category
            trend_indicators = knowledge_base.get("trend_indicators", {}).get("yield_trends", {})
            trend_category = "stable"
            
            for category, thresholds in trend_indicators.items():
                min_change = thresholds.get("min_change", -999)
                max_change = thresholds.get("max_change", 999)
                
                if min_change <= avg_change <= max_change:
                    trend_category = category
                    break
            
            return {
                "yearly_changes": yield_changes,
                "average_change_percent": round(avg_change, 2),
                "trend_category": trend_category,
                "trend_description": trend_indicators.get(trend_category, {}).get("description", "")
            }
        
        return {"error": "No yield trend data available"}
    
    def _analyze_cost_trends(
        self, 
        yearly_data: Dict[str, TrendData], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cost trends over time."""
        if len(yearly_data) < 2:
            return {"error": "Insufficient data for cost trend analysis"}
        
        # Sort by year
        sorted_years = sorted(yearly_data.keys())
        
        # Calculate year-over-year changes
        cost_changes = []
        for i in range(1, len(sorted_years)):
            current_year = sorted_years[i]
            previous_year = sorted_years[i-1]
            
            current_cost = yearly_data[current_year].cost_per_hectare
            previous_cost = yearly_data[previous_year].cost_per_hectare
            
            change_percent = self._calculate_trend_percentage(current_cost, previous_cost)
            cost_changes.append({
                "year": current_year,
                "previous_year": previous_year,
                "current_cost": current_cost,
                "previous_cost": previous_cost,
                "change_percent": round(change_percent, 2)
            })
        
        # Calculate overall trend
        if cost_changes:
            avg_change = statistics.mean(change["change_percent"] for change in cost_changes)
            
            # Determine trend category
            trend_indicators = knowledge_base.get("trend_indicators", {}).get("cost_trends", {})
            trend_category = "cost_stable"
            
            for category, thresholds in trend_indicators.items():
                min_change = thresholds.get("min_change", -999)
                max_change = thresholds.get("max_change", 999)
                
                if min_change <= avg_change <= max_change:
                    trend_category = category
                    break
            
            return {
                "yearly_changes": cost_changes,
                "average_change_percent": round(avg_change, 2),
                "trend_category": trend_category,
                "trend_description": trend_indicators.get(trend_category, {}).get("description", "")
            }
        
        return {"error": "No cost trend data available"}
    
    def _analyze_quality_trends(
        self, 
        yearly_data: Dict[str, TrendData], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze quality trends over time."""
        if len(yearly_data) < 2:
            return {"error": "Insufficient data for quality trend analysis"}
        
        # Sort by year
        sorted_years = sorted(yearly_data.keys())
        
        # Calculate year-over-year changes
        quality_changes = []
        for i in range(1, len(sorted_years)):
            current_year = sorted_years[i]
            previous_year = sorted_years[i-1]
            
            current_quality = yearly_data[current_year].quality_score
            previous_quality = yearly_data[previous_year].quality_score
            
            change_percent = self._calculate_trend_percentage(current_quality, previous_quality)
            quality_changes.append({
                "year": current_year,
                "previous_year": previous_year,
                "current_quality": current_quality,
                "previous_quality": previous_quality,
                "change_percent": round(change_percent, 2)
            })
        
        # Calculate overall trend
        if quality_changes:
            avg_change = statistics.mean(change["change_percent"] for change in quality_changes)
            
            # Determine trend category
            trend_indicators = knowledge_base.get("trend_indicators", {}).get("quality_trends", {})
            trend_category = "quality_stable"
            
            for category, thresholds in trend_indicators.items():
                min_change = thresholds.get("min_change", -999)
                max_change = thresholds.get("max_change", 999)
                
                if min_change <= avg_change <= max_change:
                    trend_category = category
                    break
            
            return {
                "yearly_changes": quality_changes,
                "average_change_percent": round(avg_change, 2),
                "trend_category": trend_category,
                "trend_description": trend_indicators.get(trend_category, {}).get("description", "")
            }
        
        return {"error": "No quality trend data available"}
    
    def _run(
        self,
        records_json: str,
        **kwargs
    ) -> str:
        """
        Calculate year-over-year trends from farm data.
        
        Args:
            records_json: JSON string of records from GetFarmDataTool
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(records_json)
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
            
            # Parse records data
            data = json.loads(records_json)
            
            if "error" in data:
                return records_json  # Pass through errors
            
            records_data = data.get("records", [])
            
            if not records_data:
                return json.dumps({"error": "Aucune donnée fournie pour l'analyse des tendances"})
            
            # Convert to FarmDataRecord objects
            records = [FarmDataRecord(**record) for record in records_data]
            
            # Group records by year
            year_groups = self._group_records_by_year(records)
            
            # Check if we have enough years for trend analysis
            if len(year_groups) < config.min_years_for_trend:
                return json.dumps({
                    "error": f"Minimum {config.min_years_for_trend} years required for trend analysis",
                    "years_available": len(year_groups)
                })
            
            # Calculate yearly averages
            yearly_data = self._calculate_yearly_averages(year_groups)
            
            # Analyze trends
            yield_trends = {}
            cost_trends = {}
            quality_trends = {}
            
            if config.include_yield_trends:
                yield_trends = self._analyze_yield_trends(yearly_data, knowledge_base)
            
            if config.include_cost_trends:
                cost_trends = self._analyze_cost_trends(yearly_data, knowledge_base)
            
            if config.include_quality_trends:
                quality_trends = self._analyze_quality_trends(yearly_data, knowledge_base)
            
            result = {
                "trend_analysis": {
                    "yield_trends": yield_trends,
                    "cost_trends": cost_trends,
                    "quality_trends": quality_trends
                },
                "yearly_data": {year: asdict(data) for year, data in yearly_data.items()},
                "summary": {
                    "years_analyzed": len(yearly_data),
                    "records_analyzed": len(records),
                    "trend_period": f"{min(yearly_data.keys())} - {max(yearly_data.keys())}"
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
            logger.error(f"Analyze trends error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'analyse des tendances: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        records_json: str,
        **kwargs
    ) -> str:
        """
        Asynchronous version of trend analysis.
        """
        # For now, just call the sync version
        return self._run(records_json, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
