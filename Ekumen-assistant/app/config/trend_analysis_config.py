"""
Trend Analysis Configuration

This module provides configurable parameters for trend analysis.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class TrendAnalysisConfig:
    """Configuration for trend analysis."""
    
    # Analysis parameters
    require_records: bool = True
    validate_data_quality: bool = True
    include_yield_trends: bool = True
    include_cost_trends: bool = True
    include_quality_trends: bool = True
    
    # Validation parameters
    min_records: int = 2
    max_records: int = 10000
    min_years_for_trend: int = 2
    require_time_series: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class TrendAnalysisConfigManager:
    """Manager for trend analysis configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = TrendAnalysisConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "trend_analysis_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = TrendAnalysisConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> TrendAnalysisConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
trend_analysis_config_manager = TrendAnalysisConfigManager()

def get_trend_analysis_config() -> TrendAnalysisConfig:
    """Get current trend analysis configuration."""
    return trend_analysis_config_manager.get_config()
