"""
Water Management Configuration

This module provides configurable parameters for water management assessment.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class WaterManagementConfig:
    """Configuration for water management assessment."""
    
    # Analysis parameters
    require_water_usage: bool = True
    validate_water_quality: bool = True
    include_irrigation_efficiency: bool = True
    include_water_quality: bool = True
    include_conservation_measures: bool = True
    include_runoff_control: bool = True
    
    # Validation parameters
    min_water_efficiency: float = 0.0
    max_water_efficiency: float = 100.0
    min_ph: float = 4.0
    max_ph: float = 12.0
    min_salinity: float = 0.0
    max_salinity: float = 10.0
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class WaterManagementConfigManager:
    """Manager for water management configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = WaterManagementConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "water_management_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = WaterManagementConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> WaterManagementConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
water_management_config_manager = WaterManagementConfigManager()

def get_water_management_config() -> WaterManagementConfig:
    """Get current water management configuration."""
    return water_management_config_manager.get_config()
