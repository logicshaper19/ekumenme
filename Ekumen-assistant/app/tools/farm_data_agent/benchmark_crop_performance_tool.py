"""
Benchmark Crop Performance Tool - Single Purpose Tool

Job: Compare crop performance against industry benchmarks.
Input: crop, average_yield, average_quality
Output: JSON string with benchmark comparison

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

logger = logging.getLogger(__name__)

class BenchmarkCropPerformanceTool(BaseTool):
    """
    Tool: Compare crop performance against industry benchmarks.
    
    Job: Take crop performance data and compare against industry standards.
    Input: crop, average_yield, average_quality
    Output: JSON string with benchmark comparison
    """
    
    name: str = "benchmark_crop_performance_tool"
    description: str = "Compare les performances des cultures aux standards de l'industrie"
    
    def _run(
        self,
        crop: str,
        average_yield: float,
        average_quality: float,
        **kwargs
    ) -> str:
        """
        Benchmarks a crop's yield and quality against industry standards and provides a performance rank.
        """
        try:
            # Get industry benchmarks
            benchmark = self._get_industry_benchmark(crop)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(average_yield, average_quality, benchmark)
            
            # Determine performance rank
            performance_rank = self._calculate_performance_rank(performance_metrics)
            
            # Generate benchmark insights
            benchmark_insights = self._generate_benchmark_insights(performance_metrics, performance_rank)
            
            result = {
                "crop": crop,
                "farm_performance": {
                    "average_yield": average_yield,
                    "average_quality": average_quality
                },
                "industry_benchmark": benchmark,
                "performance_metrics": performance_metrics,
                "performance_rank": performance_rank,
                "benchmark_insights": benchmark_insights
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Benchmark crop performance error: {e}")
            return json.dumps({"error": f"Erreur lors du benchmark: {str(e)}"})
    
    def _get_industry_benchmark(self, crop: str) -> Dict[str, float]:
        """Get industry benchmarks for a specific crop."""
        industry_benchmarks = {
            "blé": {"yield": 70.0, "quality": 8.0},
            "maïs": {"yield": 90.0, "quality": 8.5},
            "colza": {"yield": 35.0, "quality": 7.5},
            "tournesol": {"yield": 25.0, "quality": 7.0},
            "orge": {"yield": 65.0, "quality": 7.8},
            "avoine": {"yield": 55.0, "quality": 7.2}
        }
        
        return industry_benchmarks.get(crop, {"yield": 65.0, "quality": 7.5})  # Default benchmark
    
    def _calculate_performance_metrics(self, farm_yield: float, farm_quality: float, benchmark: Dict[str, float]) -> Dict[str, float]:
        """Calculate performance metrics compared to benchmark."""
        yield_performance = (farm_yield / benchmark["yield"]) * 100
        quality_performance = (farm_quality / benchmark["quality"]) * 100
        overall_performance = (yield_performance + quality_performance) / 2
        
        return {
            "yield_performance_percent": round(yield_performance, 1),
            "quality_performance_percent": round(quality_performance, 1),
            "overall_performance_percent": round(overall_performance, 1)
        }
    
    def _calculate_performance_rank(self, performance_metrics: Dict[str, float]) -> str:
        """Calculate performance rank based on overall performance."""
        overall_performance = performance_metrics["overall_performance_percent"]
        
        if overall_performance > 110:
            return "top_10_percent"
        elif overall_performance > 100:
            return "top_25_percent"
        elif overall_performance > 90:
            return "above_average"
        elif overall_performance > 80:
            return "average"
        else:
            return "below_average"
    
    def _generate_benchmark_insights(self, performance_metrics: Dict[str, float], performance_rank: str) -> List[str]:
        """Generate benchmark insights."""
        insights = []
        
        overall_performance = performance_metrics["overall_performance_percent"]
        yield_performance = performance_metrics["yield_performance_percent"]
        quality_performance = performance_metrics["quality_performance_percent"]
        
        # Overall performance insights
        if overall_performance > 110:
            insights.append("🏆 Performance exceptionnelle - Top 10% de l'industrie")
        elif overall_performance > 100:
            insights.append("🥇 Performance excellente - Top 25% de l'industrie")
        elif overall_performance > 90:
            insights.append("✅ Performance au-dessus de la moyenne")
        elif overall_performance > 80:
            insights.append("📊 Performance dans la moyenne")
        else:
            insights.append("⚠️ Performance en dessous de la moyenne - Amélioration nécessaire")
        
        # Yield-specific insights
        if yield_performance > 110:
            insights.append("🌾 Rendement exceptionnel - Dépassement des standards")
        elif yield_performance > 100:
            insights.append("🌾 Rendement excellent - Au-dessus des standards")
        elif yield_performance < 80:
            insights.append("🌾 Rendement faible - Optimisation nécessaire")
        
        # Quality-specific insights
        if quality_performance > 110:
            insights.append("⭐ Qualité exceptionnelle - Standards dépassés")
        elif quality_performance > 100:
            insights.append("⭐ Qualité excellente - Au-dessus des standards")
        elif quality_performance < 80:
            insights.append("⭐ Qualité faible - Amélioration nécessaire")
        
        # Balanced performance insights
        if abs(yield_performance - quality_performance) > 20:
            if yield_performance > quality_performance:
                insights.append("⚖️ Déséquilibre: Rendement élevé mais qualité à améliorer")
            else:
                insights.append("⚖️ Déséquilibre: Qualité élevée mais rendement à améliorer")
        else:
            insights.append("⚖️ Performance équilibrée entre rendement et qualité")
        
        return insights
