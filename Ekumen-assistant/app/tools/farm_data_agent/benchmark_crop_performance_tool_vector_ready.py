"""
Benchmark Crop Performance Tool - Vector Database Ready Tool

Job: Compare crop performance against industry benchmarks.
Input: crop, average_yield, average_quality
Output: JSON string with benchmark comparison

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

# Import configuration system
from ...config.crop_benchmark_config import get_crop_benchmark_config

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Structured benchmark result."""
    crop: str
    yield_performance: float
    quality_performance: float
    overall_performance: float
    performance_category: str
    benchmark_yield: float
    benchmark_quality: float

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class BenchmarkCropPerformanceTool(BaseTool):
    """
    Vector Database Ready Tool: Compare crop performance against industry benchmarks.
    
    Job: Take crop performance data and compare against industry standards.
    Input: crop, average_yield, average_quality
    Output: JSON string with benchmark comparison
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "benchmark_crop_performance_tool"
    description: str = "Compare les performances des cultures aux standards avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "crop_benchmark_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_crop_benchmark_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading crop benchmark knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        crop: str,
        average_yield: float,
        average_quality: float,
        region: str = "france"
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate crop type
        if config.require_crop_type and not crop:
            errors.append(ValidationError("crop", "Crop type is required", "error"))
        
        # Validate yield range
        if config.validate_yield_range:
            if average_yield < config.min_yield:
                errors.append(ValidationError("average_yield", f"Yield too low (minimum {config.min_yield})", "error"))
            elif average_yield > config.max_yield:
                errors.append(ValidationError("average_yield", f"Yield too high (maximum {config.max_yield})", "warning"))
        
        # Validate quality range
        if config.validate_quality_range:
            if average_quality < config.min_quality:
                errors.append(ValidationError("average_quality", f"Quality too low (minimum {config.min_quality})", "error"))
            elif average_quality > config.max_quality:
                errors.append(ValidationError("average_quality", f"Quality too high (maximum {config.max_quality})", "warning"))
        
        return errors
    
    def _get_industry_benchmark(
        self, 
        crop: str, 
        region: str,
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, float]:
        """Get industry benchmark for a specific crop and region."""
        industry_benchmarks = knowledge_base.get("industry_benchmarks", {})
        regional_factors = knowledge_base.get("regional_factors", {})
        
        # Get base benchmark
        crop_benchmark = industry_benchmarks.get(crop.lower(), {})
        if not crop_benchmark:
            # Default benchmark if crop not found
            crop_benchmark = {
                "yield_benchmark": 65.0,
                "quality_benchmark": 7.5,
                "cost_benchmark": 450.0
            }
        
        # Apply regional adjustment
        if self._get_config().include_regional_adjustment:
            region_factors = regional_factors.get(region.lower(), {})
            yield_multiplier = region_factors.get("yield_multiplier", 1.0)
            quality_multiplier = region_factors.get("quality_multiplier", 1.0)
            cost_multiplier = region_factors.get("cost_multiplier", 1.0)
            
            return {
                "yield_benchmark": crop_benchmark["yield_benchmark"] * yield_multiplier,
                "quality_benchmark": crop_benchmark["quality_benchmark"] * quality_multiplier,
                "cost_benchmark": crop_benchmark["cost_benchmark"] * cost_multiplier
            }
        
        return {
            "yield_benchmark": crop_benchmark["yield_benchmark"],
            "quality_benchmark": crop_benchmark["quality_benchmark"],
            "cost_benchmark": crop_benchmark["cost_benchmark"]
        }
    
    def _calculate_performance_metrics(
        self, 
        average_yield: float, 
        average_quality: float, 
        benchmark: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate performance metrics against benchmarks."""
        yield_benchmark = benchmark["yield_benchmark"]
        quality_benchmark = benchmark["quality_benchmark"]
        
        # Calculate performance ratios
        yield_performance = (average_yield / yield_benchmark) * 100 if yield_benchmark > 0 else 0
        quality_performance = (average_quality / quality_benchmark) * 100 if quality_benchmark > 0 else 0
        
        # Calculate overall performance (weighted average)
        overall_performance = (yield_performance * 0.6 + quality_performance * 0.4)
        
        return {
            "yield_performance": round(yield_performance, 1),
            "quality_performance": round(quality_performance, 1),
            "overall_performance": round(overall_performance, 1)
        }
    
    def _determine_performance_category(
        self, 
        performance_metrics: Dict[str, float], 
        knowledge_base: Dict[str, Any]
    ) -> str:
        """Determine performance category based on metrics."""
        performance_categories = knowledge_base.get("performance_categories", {})
        
        yield_performance = performance_metrics["yield_performance"] / 100  # Convert to ratio
        quality_performance = performance_metrics["quality_performance"] / 100  # Convert to ratio
        
        # Check categories from best to worst
        for category, thresholds in performance_categories.items():
            yield_threshold = thresholds.get("yield_threshold", 1.0)
            quality_threshold = thresholds.get("quality_threshold", 1.0)
            
            if yield_performance >= yield_threshold and quality_performance >= quality_threshold:
                return category
        
        return "poor"  # Default to poor if no category matches
    
    def _generate_benchmark_insights(
        self, 
        crop: str, 
        performance_metrics: Dict[str, float], 
        performance_category: str,
        benchmark: Dict[str, float],
        knowledge_base: Dict[str, Any]
    ) -> List[str]:
        """Generate insights based on benchmark comparison."""
        insights = []
        
        yield_performance = performance_metrics["yield_performance"]
        quality_performance = performance_metrics["quality_performance"]
        overall_performance = performance_metrics["overall_performance"]
        
        # Yield insights
        if yield_performance >= 120:
            insights.append(f"🌾 Excellent rendement: {yield_performance:.1f}% du benchmark")
        elif yield_performance >= 100:
            insights.append(f"🌾 Bon rendement: {yield_performance:.1f}% du benchmark")
        elif yield_performance >= 80:
            insights.append(f"🌾 Rendement moyen: {yield_performance:.1f}% du benchmark")
        else:
            insights.append(f"🌾 Rendement faible: {yield_performance:.1f}% du benchmark")
        
        # Quality insights
        if quality_performance >= 115:
            insights.append(f"⭐ Excellente qualité: {quality_performance:.1f}% du benchmark")
        elif quality_performance >= 100:
            insights.append(f"⭐ Bonne qualité: {quality_performance:.1f}% du benchmark")
        elif quality_performance >= 85:
            insights.append(f"⭐ Qualité moyenne: {quality_performance:.1f}% du benchmark")
        else:
            insights.append(f"⭐ Qualité faible: {quality_performance:.1f}% du benchmark")
        
        # Overall performance insights
        if overall_performance >= 110:
            insights.append(f"🏆 Performance globale excellente: {overall_performance:.1f}%")
        elif overall_performance >= 100:
            insights.append(f"🏆 Performance globale bonne: {overall_performance:.1f}%")
        elif overall_performance >= 90:
            insights.append(f"🏆 Performance globale moyenne: {overall_performance:.1f}%")
        else:
            insights.append(f"🏆 Performance globale faible: {overall_performance:.1f}%")
        
        # Category-specific insights
        performance_categories = knowledge_base.get("performance_categories", {})
        category_info = performance_categories.get(performance_category, {})
        if category_info:
            insights.append(f"📊 Catégorie: {performance_category} - {category_info.get('description', '')}")
        
        return insights
    
    def _run(
        self,
        crop: str,
        average_yield: float,
        average_quality: float,
        region: str = "france",
        **kwargs
    ) -> str:
        """
        Compare crop performance against industry benchmarks.
        
        Args:
            crop: Type of crop (blé, maïs, tournesol, etc.)
            average_yield: Average yield in q/ha
            average_quality: Average quality score (0-10)
            region: Region for benchmark comparison (france, europe, global)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(crop, average_yield, average_quality, region)
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
            
            # Get industry benchmark
            benchmark = self._get_industry_benchmark(crop, region, knowledge_base)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(average_yield, average_quality, benchmark)
            
            # Determine performance category
            performance_category = self._determine_performance_category(performance_metrics, knowledge_base)
            
            # Generate insights
            insights = self._generate_benchmark_insights(crop, performance_metrics, performance_category, benchmark, knowledge_base)
            
            result = {
                "crop": crop,
                "region": region,
                "input_data": {
                    "average_yield": average_yield,
                    "average_quality": average_quality
                },
                "benchmark_data": benchmark,
                "performance_metrics": performance_metrics,
                "performance_category": performance_category,
                "insights": insights,
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
            logger.error(f"Benchmark crop performance error: {e}")
            return json.dumps({
                "error": f"Erreur lors du benchmark des performances de culture: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        crop: str,
        average_yield: float,
        average_quality: float,
        region: str = "france",
        **kwargs
    ) -> str:
        """
        Asynchronous version of crop performance benchmarking.
        """
        # For now, just call the sync version
        return self._run(crop, average_yield, average_quality, region, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
