"""
Calculate Performance Metrics Tool - Vector Database Ready Tool

Job: Calculate performance metrics from farm data records.
Input: JSON string of records from GetFarmDataTool
Output: JSON string with calculated metrics

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

# Import configuration system
from ...config.performance_metrics_config import get_performance_metrics_config

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
class PerformanceMetrics:
    """Structured performance metrics."""
    yield_metrics: Dict[str, float]
    cost_metrics: Dict[str, float]
    quality_metrics: Dict[str, float]
    overall_score: float

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class CalculatePerformanceMetricsTool(BaseTool):
    """
    Vector Database Ready Tool: Calculate performance metrics from farm data records.
    
    Job: Take farm data records and calculate key performance metrics.
    Input: JSON string of records from GetFarmDataTool
    Output: JSON string with calculated metrics
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "calculate_performance_metrics_tool"
    description: str = "Calcule les métriques de performance avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "performance_metrics_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_performance_metrics_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading performance metrics knowledge base: {e}")
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
    
    def _calculate_yield_metrics(
        self, 
        records: List[FarmDataRecord], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate yield-related performance metrics."""
        if not records:
            return {}
        
        yield_indicators = knowledge_base.get("performance_indicators", {}).get("yield_metrics", {})
        
        # Calculate average yield weighted by surface
        total_surface = sum(record.surface for record in records)
        if total_surface == 0:
            return {}
        
        weighted_yield = sum(record.yield_value * record.surface for record in records) / total_surface
        
        # Calculate yield variance
        yield_values = [record.yield_value for record in records]
        yield_variance = statistics.variance(yield_values) if len(yield_values) > 1 else 0
        
        # Calculate yield efficiency (yield per unit surface)
        yield_efficiency = weighted_yield
        
        return {
            "average_yield": round(weighted_yield, 2),
            "yield_variance": round(yield_variance, 2),
            "yield_efficiency": round(yield_efficiency, 2)
        }
    
    def _calculate_cost_metrics(
        self, 
        records: List[FarmDataRecord], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate cost-related performance metrics."""
        if not records:
            return {}
        
        cost_indicators = knowledge_base.get("performance_indicators", {}).get("cost_metrics", {})
        
        # Calculate average cost weighted by surface
        total_surface = sum(record.surface for record in records)
        if total_surface == 0:
            return {}
        
        weighted_cost = sum(record.cost_per_hectare * record.surface for record in records) / total_surface
        
        # Calculate cost per yield
        total_yield = sum(record.yield_value * record.surface for record in records)
        cost_per_yield = (weighted_cost * total_surface) / total_yield if total_yield > 0 else 0
        
        # Calculate cost efficiency (inverse of cost per hectare)
        cost_efficiency = 1000 / weighted_cost if weighted_cost > 0 else 0
        
        return {
            "average_cost": round(weighted_cost, 2),
            "cost_per_yield": round(cost_per_yield, 2),
            "cost_efficiency": round(cost_efficiency, 2)
        }
    
    def _calculate_quality_metrics(
        self, 
        records: List[FarmDataRecord], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate quality-related performance metrics."""
        if not records:
            return {}
        
        quality_indicators = knowledge_base.get("performance_indicators", {}).get("quality_metrics", {})
        
        # Calculate average quality
        quality_scores = [record.quality_score for record in records]
        average_quality = statistics.mean(quality_scores)
        
        # Calculate quality consistency (inverse of standard deviation)
        quality_consistency = 10 - statistics.stdev(quality_scores) if len(quality_scores) > 1 else 10
        
        # Calculate quality trend (simplified - would need time series data)
        quality_trend = average_quality  # Simplified calculation
        
        return {
            "average_quality": round(average_quality, 2),
            "quality_consistency": round(quality_consistency, 2),
            "quality_trend": round(quality_trend, 2)
        }
    
    def _calculate_overall_score(
        self, 
        yield_metrics: Dict[str, float], 
        cost_metrics: Dict[str, float], 
        quality_metrics: Dict[str, float],
        knowledge_base: Dict[str, Any]
    ) -> float:
        """Calculate overall performance score."""
        calculation_weights = knowledge_base.get("calculation_weights", {})
        
        yield_weight = calculation_weights.get("yield_weight", 0.4)
        cost_weight = calculation_weights.get("cost_weight", 0.3)
        quality_weight = calculation_weights.get("quality_weight", 0.3)
        
        # Normalize metrics to 0-100 scale
        yield_score = min(100, (yield_metrics.get("average_yield", 0) / 100) * 100)
        cost_score = max(0, 100 - (cost_metrics.get("average_cost", 0) / 10))  # Lower cost = higher score
        quality_score = (quality_metrics.get("average_quality", 0) / 10) * 100
        
        overall_score = (yield_score * yield_weight + 
                        cost_score * cost_weight + 
                        quality_score * quality_weight)
        
        return round(overall_score, 2)
    
    def _assess_performance_level(
        self, 
        metrics: Dict[str, float], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, str]:
        """Assess performance levels based on benchmarks."""
        benchmark_thresholds = knowledge_base.get("benchmark_thresholds", {})
        
        # Assess yield performance
        yield_performance = benchmark_thresholds.get("yield_performance", {})
        yield_score = metrics.get("yield_metrics", {}).get("average_yield", 0)
        yield_level = "poor"
        for level, threshold in yield_performance.items():
            if "min" in threshold and yield_score >= threshold["min"]:
                yield_level = level
            elif "max" in threshold and yield_score <= threshold["max"]:
                yield_level = level
        
        # Assess cost performance
        cost_performance = benchmark_thresholds.get("cost_efficiency", {})
        cost_score = metrics.get("cost_metrics", {}).get("average_cost", 0)
        cost_level = "poor"
        for level, threshold in cost_performance.items():
            if "min" in threshold and cost_score >= threshold["min"]:
                cost_level = level
            elif "max" in threshold and cost_score <= threshold["max"]:
                cost_level = level
        
        # Assess quality performance
        quality_performance = benchmark_thresholds.get("quality_performance", {})
        quality_score = metrics.get("quality_metrics", {}).get("average_quality", 0)
        quality_level = "poor"
        for level, threshold in quality_performance.items():
            if "min" in threshold and quality_score >= threshold["min"]:
                quality_level = level
            elif "max" in threshold and quality_score <= threshold["max"]:
                quality_level = level
        
        return {
            "yield_level": yield_level,
            "cost_level": cost_level,
            "quality_level": quality_level
        }
    
    def _run(
        self,
        records_json: str,
        **kwargs
    ) -> str:
        """
        Calculate performance metrics from farm data records.
        
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
                return json.dumps({"error": "Aucune donnée fournie pour le calcul des métriques"})
            
            # Convert to FarmDataRecord objects
            records = [FarmDataRecord(**record) for record in records_data]
            
            # Calculate metrics
            yield_metrics = {}
            cost_metrics = {}
            quality_metrics = {}
            
            if config.include_yield_metrics:
                yield_metrics = self._calculate_yield_metrics(records, knowledge_base)
            
            if config.include_cost_metrics:
                cost_metrics = self._calculate_cost_metrics(records, knowledge_base)
            
            if config.include_quality_metrics:
                quality_metrics = self._calculate_quality_metrics(records, knowledge_base)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(yield_metrics, cost_metrics, quality_metrics, knowledge_base)
            
            # Assess performance levels
            all_metrics = {
                "yield_metrics": yield_metrics,
                "cost_metrics": cost_metrics,
                "quality_metrics": quality_metrics
            }
            performance_levels = self._assess_performance_level(all_metrics, knowledge_base)
            
            result = {
                "performance_metrics": {
                    "yield_metrics": yield_metrics,
                    "cost_metrics": cost_metrics,
                    "quality_metrics": quality_metrics,
                    "overall_score": overall_score
                },
                "performance_assessment": performance_levels,
                "summary": {
                    "total_records_analyzed": len(records),
                    "metrics_calculated": len(yield_metrics) + len(cost_metrics) + len(quality_metrics),
                    "overall_performance": "excellent" if overall_score >= 80 else "good" if overall_score >= 60 else "average" if overall_score >= 40 else "poor"
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
            logger.error(f"Calculate performance metrics error: {e}")
            return json.dumps({
                "error": f"Erreur lors du calcul des métriques de performance: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        records_json: str,
        **kwargs
    ) -> str:
        """
        Asynchronous version of performance metrics calculation.
        """
        # For now, just call the sync version
        return self._run(records_json, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
