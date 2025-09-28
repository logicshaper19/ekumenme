"""
Planning Report Configuration

This module provides configurable parameters for planning report generation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class PlanningReportConfig:
    """Configuration for planning report generation."""
    
    # Analysis parameters
    require_tasks: bool = True
    validate_report_sections: bool = True
    include_executive_summary: bool = True
    include_recommendations: bool = True
    
    # Validation parameters
    min_report_sections: int = 2
    max_report_sections: int = 10
    require_report_format: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class PlanningReportConfigManager:
    """Manager for planning report configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = PlanningReportConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "planning_report_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = PlanningReportConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> PlanningReportConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
planning_report_config_manager = PlanningReportConfigManager()

def get_planning_report_config() -> PlanningReportConfig:
    """Get current planning report configuration."""
    return planning_report_config_manager.get_config()
