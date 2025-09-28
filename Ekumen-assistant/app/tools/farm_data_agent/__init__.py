"""
Farm Data Agent Tools Package.

This package contains all farm data-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- GetFarmDataTool: Retrieve raw farm data records
- CalculatePerformanceMetricsTool: Calculate performance metrics
- BenchmarkCropPerformanceTool: Compare against industry benchmarks
- AnalyzeTrendsTool: Calculate year-over-year trends
- GenerateFarmReportTool: Generate structured farm reports
"""

from .get_farm_data_tool import GetFarmDataTool
from .calculate_performance_metrics_tool import CalculatePerformanceMetricsTool
from .benchmark_crop_performance_tool import BenchmarkCropPerformanceTool
from .analyze_trends_tool import AnalyzeTrendsTool
from .generate_farm_report_tool import GenerateFarmReportTool

__all__ = [
    "GetFarmDataTool",
    "CalculatePerformanceMetricsTool",
    "BenchmarkCropPerformanceTool",
    "AnalyzeTrendsTool",
    "GenerateFarmReportTool"
]
