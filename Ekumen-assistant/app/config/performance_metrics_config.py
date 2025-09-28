"""
Performance Metrics Configuration

This module provides configurable parameters for performance metrics calculation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class PerformanceMetricsConfig:
    """Configuration for performance metrics calculation."""
    
    # Analysis parameters
    require_records: bool = True
    validate_data_quality: bool = True
    include_yield_metrics: bool = True
    include_cost_metrics: bool = True
    include_quality_metrics: bool = True
    
    # Validation parameters
    min_records: int = 1
    max_records: int = 10000
    require_benchmark_comparison: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class PerformanceMetricsConfigManager:
    """Manager for performance metrics configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = PerformanceMetricsConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "performance_metrics_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = PerformanceMetricsConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> PerformanceMetricsConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
performance_metrics_config_manager = PerformanceMetricsConfigManager()

def get_performance_metrics_config() -> PerformanceMetricsConfig:
    """Get current performance metrics configuration."""
    return performance_metrics_config_manager.get_config()
