"""
Farm Report Configuration

This module provides configurable parameters for farm report generation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class FarmReportConfig:
    """Configuration for farm report generation."""
    
    # Report parameters
    require_records: bool = True
    include_executive_summary: bool = True
    include_performance_analysis: bool = True
    include_benchmark_comparison: bool = True
    include_trend_analysis: bool = True
    include_recommendations: bool = True
    
    # Validation parameters
    min_records: int = 1
    max_records: int = 10000
    require_metrics_data: bool = False
    require_benchmark_data: bool = False
    require_trends_data: bool = False
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class FarmReportConfigManager:
    """Manager for farm report configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = FarmReportConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "farm_report_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = FarmReportConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> FarmReportConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
farm_report_config_manager = FarmReportConfigManager()

def get_farm_report_config() -> FarmReportConfig:
    """Get current farm report configuration."""
    return farm_report_config_manager.get_config()
