"""
Intervention Windows Configuration

This module provides configurable parameters for intervention window analysis.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class InterventionWindowsConfig:
    """Configuration for intervention window analysis."""
    
    # Analysis parameters
    default_confidence_threshold: float = 0.7
    high_confidence_threshold: float = 0.9
    require_weather_data: bool = True
    validate_intervention_type: bool = True
    
    # Validation parameters
    min_forecast_days: int = 1
    max_forecast_days: int = 14
    require_location: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class InterventionWindowsConfigManager:
    """Manager for intervention windows configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = InterventionWindowsConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "intervention_windows_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = InterventionWindowsConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> InterventionWindowsConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
intervention_windows_config_manager = InterventionWindowsConfigManager()

def get_intervention_windows_config() -> InterventionWindowsConfig:
    """Get current intervention windows configuration."""
    return intervention_windows_config_manager.get_config()
