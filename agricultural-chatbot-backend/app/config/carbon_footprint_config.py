"""
Carbon Footprint Configuration

This module provides configurable parameters for carbon footprint analysis.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class CarbonFootprintConfig:
    """Configuration for carbon footprint analysis."""
    
    # Analysis parameters
    minimum_emission_threshold: float = 10.0
    high_emission_threshold: float = 50.0
    default_area_ha: float = 1.0
    default_duration_days: int = 1
    
    # Validation parameters
    require_practice_type: bool = True
    validate_area_range: bool = True
    min_area_ha: float = 0.1
    max_area_ha: float = 1000.0
    min_duration_days: int = 1
    max_duration_days: int = 365
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class CarbonFootprintConfigManager:
    """Manager for carbon footprint configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = CarbonFootprintConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "carbon_footprint_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = CarbonFootprintConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> CarbonFootprintConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
carbon_config_manager = CarbonFootprintConfigManager()

def get_carbon_footprint_config() -> CarbonFootprintConfig:
    """Get current carbon footprint configuration."""
    return carbon_config_manager.get_config()
