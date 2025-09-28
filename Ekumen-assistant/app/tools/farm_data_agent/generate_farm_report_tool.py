"""
Generate Farm Report Tool - Single Purpose Tool

Job: Generate structured farm reports from analysis results.
Input: JSON strings from other farm data tools
Output: JSON string with comprehensive farm report

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
from datetime import datetime

logger = logging.getLogger(__name__)

class GenerateFarmReportTool(BaseTool):
    """
    Tool: Generate structured farm reports from analysis results.
    
    Job: Take results from other farm data tools and generate comprehensive report.
    Input: JSON strings from other farm data tools
    Output: JSON string with comprehensive farm report
    """
    
    name: str = "generate_farm_report_tool"
    description: str = "Génère un rapport d'exploitation structuré"
    
    def _run(
        self,
        records_json: str,
        metrics_json: str = None,
        benchmark_json: str = None,
        trends_json: str = None,
        **kwargs
    ) -> str:
        """
        Generate structured farm report from analysis results.
        
        Args:
            records_json: JSON string from GetFarmDataTool
            metrics_json: JSON string from CalculatePerformanceMetricsTool (optional)
            benchmark_json: JSON string from BenchmarkCropPerformanceTool (optional)
            trends_json: JSON string from AnalyzeTrendsTool (optional)
        """
        try:
            # Parse input data
            records_data = json.loads(records_json)
            metrics_data = json.loads(metrics_json) if metrics_json else None
            benchmark_data = json.loads(benchmark_json) if benchmark_json else None
            trends_data = json.loads(trends_json) if trends_json else None
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(records_data, metrics_data, benchmark_data, trends_data)
            
            return json.dumps(report, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Generate farm report error: {e}")
            return json.dumps({"error": f"Erreur lors de la génération du rapport: {str(e)}"})
    
    def _generate_comprehensive_report(self, records_data: Dict, metrics_data: Dict = None, benchmark_data: Dict = None, trends_data: Dict = None) -> Dict[str, Any]:
        """Generate comprehensive farm report."""
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "farm_analysis",
                "version": "1.0"
            },
            "executive_summary": self._generate_executive_summary(records_data, metrics_data, benchmark_data, trends_data),
            "data_overview": self._extract_data_overview(records_data),
            "performance_analysis": self._extract_performance_analysis(metrics_data) if metrics_data else None,
            "benchmark_analysis": self._extract_benchmark_analysis(benchmark_data) if benchmark_data else None,
            "trend_analysis": self._extract_trend_analysis(trends_data) if trends_data else None,
            "recommendations": self._generate_recommendations(records_data, metrics_data, benchmark_data, trends_data)
        }
        
        return report
    
    def _generate_executive_summary(self, records_data: Dict, metrics_data: Dict = None, benchmark_data: Dict = None, trends_data: Dict = None) -> Dict[str, Any]:
        """Generate executive summary."""
        summary = {
            "total_records": records_data.get("total_records", 0),
            "filters": records_data.get("filters", {})
        }
        
        if metrics_data:
            overall_metrics = metrics_data.get("overall_metrics", {})
            summary["average_yield"] = overall_metrics.get("average_yield_q_ha", 0)
            summary["average_cost"] = overall_metrics.get("average_cost_eur_ha", 0)
            summary["average_quality"] = overall_metrics.get("average_quality_score", 0)
        
        if benchmark_data:
            summary["performance_rank"] = benchmark_data.get("performance_rank", "unknown")
            summary["overall_performance"] = benchmark_data.get("performance_metrics", {}).get("overall_performance_percent", 0)
        
        if trends_data:
            overall_trends = trends_data.get("trend_analysis", {}).get("overall_trends", {})
            summary["yield_trend"] = overall_trends.get("yield_trend", {}).get("trend_direction", "unknown")
            summary["cost_trend"] = overall_trends.get("cost_trend", {}).get("trend_direction", "unknown")
        
        return summary
    
    def _extract_data_overview(self, records_data: Dict) -> Dict[str, Any]:
        """Extract data overview from records data."""
        records = records_data.get("records", [])
        
        # Analyze data by crop
        crops = {}
        parcels = {}
        
        for record in records:
            crop = record.get("crop", "")
            parcel = record.get("parcel", "")
            
            if crop not in crops:
                crops[crop] = 0
            crops[crop] += 1
            
            if parcel not in parcels:
                parcels[parcel] = 0
            parcels[parcel] += 1
        
        return {
            "crops_analyzed": list(crops.keys()),
            "parcels_analyzed": list(parcels.keys()),
            "crop_distribution": crops,
            "parcel_distribution": parcels
        }
    
    def _extract_performance_analysis(self, metrics_data: Dict) -> Dict[str, Any]:
        """Extract performance analysis from metrics data."""
        return {
            "overall_metrics": metrics_data.get("overall_metrics", {}),
            "crop_metrics": metrics_data.get("crop_metrics", {}),
            "parcel_metrics": metrics_data.get("parcel_metrics", {})
        }
    
    def _extract_benchmark_analysis(self, benchmark_data: Dict) -> Dict[str, Any]:
        """Extract benchmark analysis from benchmark data."""
        return {
            "farm_performance": benchmark_data.get("farm_performance", {}),
            "industry_benchmark": benchmark_data.get("industry_benchmark", {}),
            "performance_metrics": benchmark_data.get("performance_metrics", {}),
            "performance_rank": benchmark_data.get("performance_rank", ""),
            "benchmark_insights": benchmark_data.get("benchmark_insights", [])
        }
    
    def _extract_trend_analysis(self, trends_data: Dict) -> Dict[str, Any]:
        """Extract trend analysis from trends data."""
        return {
            "trend_analysis": trends_data.get("trend_analysis", {}),
            "trend_insights": trends_data.get("trend_insights", [])
        }
    
    def _generate_recommendations(self, records_data: Dict, metrics_data: Dict = None, benchmark_data: Dict = None, trends_data: Dict = None) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Data quality recommendations
        total_records = records_data.get("total_records", 0)
        if total_records < 5:
            recommendations.append("Améliorer la collecte de données pour une analyse plus précise")
        elif total_records > 50:
            recommendations.append("Excellent volume de données - Continuer la collecte systématique")
        
        # Performance recommendations
        if metrics_data:
            overall_metrics = metrics_data.get("overall_metrics", {})
            average_yield = overall_metrics.get("average_yield_q_ha", 0)
            average_cost = overall_metrics.get("average_cost_eur_ha", 0)
            
            if average_yield < 60:
                recommendations.append("Optimiser les pratiques culturales pour améliorer le rendement")
            if average_cost > 500:
                recommendations.append("Analyser les coûts pour identifier les économies possibles")
        
        # Benchmark recommendations
        if benchmark_data:
            performance_rank = benchmark_data.get("performance_rank", "")
            if performance_rank == "below_average":
                recommendations.append("Mettre en place un plan d'amélioration des performances")
            elif performance_rank == "top_10_percent":
                recommendations.append("Maintenir l'excellence et partager les bonnes pratiques")
        
        # Trend recommendations
        if trends_data:
            overall_trends = trends_data.get("trend_analysis", {}).get("overall_trends", {})
            yield_trend = overall_trends.get("yield_trend", {}).get("trend_direction", "")
            cost_trend = overall_trends.get("cost_trend", {}).get("trend_direction", "")
            
            if yield_trend == "decreasing":
                recommendations.append("Investiguer les causes de la baisse de rendement")
            if cost_trend == "increasing":
                recommendations.append("Contrôler l'évolution des coûts de production")
        
        return recommendations
