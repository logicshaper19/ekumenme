"""
Evapotranspiration Configuration

This module provides configurable parameters for evapotranspiration calculation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class EvapotranspirationConfig:
    """Configuration for evapotranspiration calculation."""
    
    # Analysis parameters
    default_calculation_method: str = "penman_monteith"
    require_weather_data: bool = True
    validate_crop_type: bool = True
    validate_soil_type: bool = True
    
    # Validation parameters
    min_temperature: float = -20.0
    max_temperature: float = 50.0
    min_humidity: float = 0.0
    max_humidity: float = 100.0
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class EvapotranspirationConfigManager:
    """Manager for evapotranspiration configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = EvapotranspirationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "evapotranspiration_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = EvapotranspirationConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> EvapotranspirationConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
evapotranspiration_config_manager = EvapotranspirationConfigManager()

def get_evapotranspiration_config() -> EvapotranspirationConfig:
    """Get current evapotranspiration configuration."""
    return evapotranspiration_config_manager.get_config()
