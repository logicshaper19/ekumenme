"""
Resource Requirements Configuration

This module provides configurable parameters for resource requirements analysis.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class ResourceRequirementsConfig:
    """Configuration for resource requirements analysis."""
    
    # Analysis parameters
    require_tasks: bool = True
    validate_equipment_requirements: bool = True
    validate_labor_requirements: bool = True
    validate_material_requirements: bool = True
    
    # Validation parameters
    min_tasks: int = 1
    max_tasks: int = 100
    require_analysis_type: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class ResourceRequirementsConfigManager:
    """Manager for resource requirements configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = ResourceRequirementsConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "resource_requirements_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = ResourceRequirementsConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> ResourceRequirementsConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
resource_requirements_config_manager = ResourceRequirementsConfigManager()

def get_resource_requirements_config() -> ResourceRequirementsConfig:
    """Get current resource requirements configuration."""
    return resource_requirements_config_manager.get_config()
