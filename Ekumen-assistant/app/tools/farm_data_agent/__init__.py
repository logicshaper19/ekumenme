"""
Farm Data Agent Tools Package.

This package contains all farm data-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- get_farm_data_tool: Retrieve raw farm data records with SIRET-based multi-tenancy
- calculate_performance_metrics_tool: Calculate performance metrics with statistical analysis
- benchmark_crop_performance_tool: Compare against industry benchmarks with percentile ranking
- analyze_trends_tool: Calculate year-over-year trends with regression analysis

Note: generate_farm_report_tool removed (meta-orchestration - agent's job)
"""

from .get_farm_data_tool import get_farm_data_tool
from .calculate_performance_metrics_tool import calculate_performance_metrics_tool
from .benchmark_crop_performance_tool import benchmark_crop_performance_tool
from .analyze_trends_tool import analyze_trends_tool

__all__ = [
    "get_farm_data_tool",
    "calculate_performance_metrics_tool",
    "benchmark_crop_performance_tool",
    "analyze_trends_tool"
]
