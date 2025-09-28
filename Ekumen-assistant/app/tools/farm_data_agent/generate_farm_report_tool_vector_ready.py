"""
Generate Farm Report Tool - Vector Database Ready Tool

Job: Generate structured farm reports from analysis results.
Input: JSON strings from other farm data tools
Output: JSON string with comprehensive farm report

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
from ...config.farm_report_config import get_farm_report_config

logger = logging.getLogger(__name__)

@dataclass
class ReportSection:
    """Structured report section."""
    title: str
    content: str
    priority: int
    required: bool

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class GenerateFarmReportTool(BaseTool):
    """
    Vector Database Ready Tool: Generate structured farm reports from analysis results.
    
    Job: Take results from other farm data tools and generate comprehensive report.
    Input: JSON strings from other farm data tools
    Output: JSON string with comprehensive farm report
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "generate_farm_report_tool"
    description: str = "Génère un rapport d'exploitation structuré avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "farm_report_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_farm_report_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading farm report knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        records_json: str,
        metrics_json: Optional[str] = None,
        benchmark_json: Optional[str] = None,
        trends_json: Optional[str] = None
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
        
        # Validate optional data if required
        if config.require_metrics_data and not metrics_json:
            errors.append(ValidationError("metrics_json", "Metrics data is required", "error"))
        
        if config.require_benchmark_data and not benchmark_json:
            errors.append(ValidationError("benchmark_json", "Benchmark data is required", "error"))
        
        if config.require_trends_data and not trends_json:
            errors.append(ValidationError("trends_json", "Trends data is required", "error"))
        
        return errors
    
    def _generate_executive_summary(
        self, 
        records_data: Dict[str, Any], 
        metrics_data: Optional[Dict[str, Any]], 
        knowledge_base: Dict[str, Any]
    ) -> str:
        """Generate executive summary section."""
        if not config.include_executive_summary:
            return ""
        
        # Extract key metrics
        summary_data = records_data.get("summary", {})
        total_records = summary_data.get("total_records", 0)
        total_surface = summary_data.get("total_surface_ha", 0)
        total_yield = summary_data.get("total_yield_production", 0)
        total_cost = summary_data.get("total_cost_eur", 0)
        avg_quality = summary_data.get("average_quality_score", 0)
        
        # Get overall performance from metrics if available
        overall_score = 0
        if metrics_data and "performance_metrics" in metrics_data:
            overall_score = metrics_data["performance_metrics"].get("overall_score", 0)
        
        # Determine performance category
        performance_categories = knowledge_base.get("performance_categories", {})
        performance_category = "average"
        for category, info in performance_categories.items():
            score_range = info.get("score_range", [0, 100])
            if score_range[0] <= overall_score <= score_range[1]:
                performance_category = category
                break
        
        # Generate summary
        template = knowledge_base.get("report_templates", {}).get("executive_summary", {})
        template_text = template.get("template", "L'exploitation présente {overall_performance} avec un score global de {overall_score}/100.")
        
        return template_text.format(
            overall_performance=performance_category,
            overall_score=overall_score,
            strengths="rendement stable",
            improvements="optimisation des coûts"
        )
    
    def _generate_performance_analysis(
        self, 
        records_data: Dict[str, Any], 
        metrics_data: Optional[Dict[str, Any]], 
        knowledge_base: Dict[str, Any]
    ) -> str:
        """Generate performance analysis section."""
        if not config.include_performance_analysis:
            return ""
        
        # Extract performance data
        summary_data = records_data.get("summary", {})
        yield_avg = summary_data.get("total_yield_production", 0) / summary_data.get("total_surface_ha", 1) if summary_data.get("total_surface_ha", 0) > 0 else 0
        cost_avg = summary_data.get("total_cost_eur", 0) / summary_data.get("total_surface_ha", 1) if summary_data.get("total_surface_ha", 0) > 0 else 0
        quality_avg = summary_data.get("average_quality_score", 0)
        
        # Generate analysis
        template = knowledge_base.get("report_templates", {}).get("performance_analysis", {})
        template_text = template.get("template", "Analyse détaillée: Rendement moyen {yield_avg} q/ha, Coût moyen {cost_avg} €/ha, Qualité moyenne {quality_avg}/10.")
        
        return template_text.format(
            yield_avg=round(yield_avg, 2),
            cost_avg=round(cost_avg, 2),
            quality_avg=round(quality_avg, 2)
        )
    
    def _generate_benchmark_comparison(
        self, 
        benchmark_data: Optional[Dict[str, Any]], 
        knowledge_base: Dict[str, Any]
    ) -> str:
        """Generate benchmark comparison section."""
        if not config.include_benchmark_comparison or not benchmark_data:
            return ""
        
        # Extract benchmark information
        performance_category = benchmark_data.get("performance_category", "average")
        performance_metrics = benchmark_data.get("performance_metrics", {})
        overall_performance = performance_metrics.get("overall_performance", 0)
        
        # Generate comparison
        template = knowledge_base.get("report_templates", {}).get("benchmark_comparison", {})
        template_text = template.get("template", "Comparaison aux standards: {benchmark_summary}")
        
        benchmark_summary = f"Performance {performance_category} ({overall_performance}% du benchmark)"
        
        return template_text.format(benchmark_summary=benchmark_summary)
    
    def _generate_trend_analysis(
        self, 
        trends_data: Optional[Dict[str, Any]], 
        knowledge_base: Dict[str, Any]
    ) -> str:
        """Generate trend analysis section."""
        if not config.include_trend_analysis or not trends_data:
            return ""
        
        # Extract trend information
        trend_analysis = trends_data.get("trend_analysis", {})
        yield_trends = trend_analysis.get("yield_trends", {})
        cost_trends = trend_analysis.get("cost_trends", {})
        quality_trends = trend_analysis.get("quality_trends", {})
        
        # Generate trend summary
        trend_summary = "Tendances stables"
        if yield_trends and "trend_category" in yield_trends:
            trend_summary = f"Rendement: {yield_trends['trend_category']}"
        
        template = knowledge_base.get("report_templates", {}).get("trend_analysis", {})
        template_text = template.get("template", "Tendances observées: {trend_summary}")
        
        return template_text.format(trend_summary=trend_summary)
    
    def _generate_recommendations(
        self, 
        records_data: Dict[str, Any], 
        metrics_data: Optional[Dict[str, Any]], 
        benchmark_data: Optional[Dict[str, Any]], 
        trends_data: Optional[Dict[str, Any]], 
        knowledge_base: Dict[str, Any]
    ) -> str:
        """Generate recommendations section."""
        if not config.include_recommendations:
            return ""
        
        # Generate recommendations based on data
        recommendations = []
        
        # Performance-based recommendations
        if metrics_data and "performance_metrics" in metrics_data:
            overall_score = metrics_data["performance_metrics"].get("overall_score", 0)
            if overall_score < 60:
                recommendations.append("Améliorer les pratiques culturales")
            if overall_score < 80:
                recommendations.append("Optimiser la gestion des intrants")
        
        # Benchmark-based recommendations
        if benchmark_data and "performance_category" in benchmark_data:
            category = benchmark_data["performance_category"]
            if category in ["below_average", "poor"]:
                recommendations.append("Analyser les écarts par rapport aux standards")
        
        # Trend-based recommendations
        if trends_data and "trend_analysis" in trends_data:
            yield_trends = trends_data["trend_analysis"].get("yield_trends", {})
            if yield_trends.get("trend_category") == "negative":
                recommendations.append("Investiguer les causes de baisse de rendement")
        
        # Default recommendations if none generated
        if not recommendations:
            recommendations = ["Maintenir les bonnes pratiques actuelles", "Surveiller les indicateurs de performance"]
        
        template = knowledge_base.get("report_templates", {}).get("recommendations", {})
        template_text = template.get("template", "Recommandations prioritaires: {priority_recommendations}")
        
        return template_text.format(priority_recommendations="; ".join(recommendations))
    
    def _run(
        self,
        records_json: str,
        metrics_json: Optional[str] = None,
        benchmark_json: Optional[str] = None,
        trends_json: Optional[str] = None,
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
            # Validate inputs
            validation_errors = self._validate_inputs(records_json, metrics_json, benchmark_json, trends_json)
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
            
            # Parse input data
            records_data = json.loads(records_json)
            metrics_data = json.loads(metrics_json) if metrics_json else None
            benchmark_data = json.loads(benchmark_json) if benchmark_json else None
            trends_data = json.loads(trends_json) if trends_json else None
            
            # Check for errors in input data
            if "error" in records_data:
                return records_json  # Pass through errors
            
            # Generate report sections
            report_sections = {}
            
            if config.include_executive_summary:
                report_sections["executive_summary"] = self._generate_executive_summary(records_data, metrics_data, knowledge_base)
            
            if config.include_performance_analysis:
                report_sections["performance_analysis"] = self._generate_performance_analysis(records_data, metrics_data, knowledge_base)
            
            if config.include_benchmark_comparison:
                report_sections["benchmark_comparison"] = self._generate_benchmark_comparison(benchmark_data, knowledge_base)
            
            if config.include_trend_analysis:
                report_sections["trend_analysis"] = self._generate_trend_analysis(trends_data, knowledge_base)
            
            if config.include_recommendations:
                report_sections["recommendations"] = self._generate_recommendations(records_data, metrics_data, benchmark_data, trends_data, knowledge_base)
            
            # Generate report metadata
            report_metadata = {
                "generated_at": datetime.now().isoformat(),
                "sections_included": list(report_sections.keys()),
                "data_sources": {
                    "records": bool(records_data),
                    "metrics": bool(metrics_data),
                    "benchmark": bool(benchmark_data),
                    "trends": bool(trends_data)
                }
            }
            
            result = {
                "farm_report": {
                    "sections": report_sections,
                    "metadata": report_metadata
                },
                "summary": {
                    "total_sections": len(report_sections),
                    "report_completeness": len(report_sections) / 5 * 100,  # 5 possible sections
                    "data_sources_used": sum(report_metadata["data_sources"].values())
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
            logger.error(f"Generate farm report error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la génération du rapport d'exploitation: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        records_json: str,
        metrics_json: Optional[str] = None,
        benchmark_json: Optional[str] = None,
        trends_json: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of farm report generation.
        """
        # For now, just call the sync version
        return self._run(records_json, metrics_json, benchmark_json, trends_json, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
