"""
Farm Data Configuration

This module provides configurable parameters for farm data retrieval.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class FarmDataConfig:
    """Configuration for farm data retrieval."""
    
    # Analysis parameters
    require_filters: bool = True
    validate_time_period: bool = True
    validate_crop_types: bool = True
    validate_parcel_types: bool = True
    
    # Validation parameters
    max_records_returned: int = 1000
    default_time_period: str = "current_year"
    require_at_least_one_filter: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class FarmDataConfigManager:
    """Manager for farm data configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = FarmDataConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "farm_data_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = FarmDataConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> FarmDataConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
farm_data_config_manager = FarmDataConfigManager()

def get_farm_data_config() -> FarmDataConfig:
    """Get current farm data configuration."""
    return farm_data_config_manager.get_config()
