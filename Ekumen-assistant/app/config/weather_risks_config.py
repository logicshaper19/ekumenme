"""
Weather Risks Configuration

This module provides configurable parameters for weather risk analysis.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class WeatherRisksConfig:
    """Configuration for weather risk analysis."""
    
    # Analysis parameters
    default_risk_threshold: float = 0.5
    high_risk_threshold: float = 0.8
    require_weather_data: bool = True
    validate_crop_type: bool = True
    
    # Validation parameters
    min_forecast_days: int = 1
    max_forecast_days: int = 14
    require_location: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class WeatherRisksConfigManager:
    """Manager for weather risks configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = WeatherRisksConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "weather_risks_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = WeatherRisksConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> WeatherRisksConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
weather_risks_config_manager = WeatherRisksConfigManager()

def get_weather_risks_config() -> WeatherRisksConfig:
    """Get current weather risks configuration."""
    return weather_risks_config_manager.get_config()
