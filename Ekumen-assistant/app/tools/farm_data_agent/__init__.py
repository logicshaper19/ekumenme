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

# Original tools
from .get_farm_data_tool import GetFarmDataTool
from .calculate_performance_metrics_tool import CalculatePerformanceMetricsTool
from .benchmark_crop_performance_tool import BenchmarkCropPerformanceTool
from .analyze_trends_tool import AnalyzeTrendsTool
from .generate_farm_report_tool import GenerateFarmReportTool

# Enhanced tools (Phase 2)
from .get_farm_data_tool_enhanced import get_farm_data_tool_enhanced
from .calculate_performance_metrics_tool_enhanced import calculate_performance_metrics_tool_enhanced
from .benchmark_crop_performance_tool_enhanced import benchmark_crop_performance_tool_enhanced
from .analyze_trends_tool_enhanced import analyze_trends_tool_enhanced
from .generate_farm_report_tool_enhanced import generate_farm_report_tool_enhanced

__all__ = [
    # Original tools
    "GetFarmDataTool",
    "CalculatePerformanceMetricsTool",
    "BenchmarkCropPerformanceTool",
    "AnalyzeTrendsTool",
    "GenerateFarmReportTool",
    # Enhanced tools
    "get_farm_data_tool_enhanced",
    "calculate_performance_metrics_tool_enhanced",
    "benchmark_crop_performance_tool_enhanced",
    "analyze_trends_tool_enhanced",
    "generate_farm_report_tool_enhanced",
]
