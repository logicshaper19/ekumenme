"""
Soil Health Configuration

This module provides configurable parameters for soil health analysis.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class SoilHealthConfig:
    """Configuration for soil health analysis."""
    
    # Analysis parameters
    require_soil_indicators: bool = True
    validate_indicator_values: bool = True
    include_organic_matter: bool = True
    include_ph_level: bool = True
    include_nutrient_content: bool = True
    include_water_capacity: bool = True
    include_soil_structure: bool = True
    include_biological_activity: bool = True
    
    # Validation parameters
    min_organic_matter: float = 0.0
    max_organic_matter: float = 20.0
    min_ph: float = 3.0
    max_ph: float = 10.0
    min_nutrients: float = 0.0
    max_nutrients: float = 1000.0
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class SoilHealthConfigManager:
    """Manager for soil health configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = SoilHealthConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "soil_health_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = SoilHealthConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> SoilHealthConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
soil_health_config_manager = SoilHealthConfigManager()

def get_soil_health_config() -> SoilHealthConfig:
    """Get current soil health configuration."""
    return soil_health_config_manager.get_config()
