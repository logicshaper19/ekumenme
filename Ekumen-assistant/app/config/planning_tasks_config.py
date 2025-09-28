"""
Planning Tasks Configuration

This module provides configurable parameters for planning task generation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class PlanningTasksConfig:
    """Configuration for planning task generation."""
    
    # Analysis parameters
    default_priority_threshold: int = 3
    require_crops: bool = True
    validate_surface_area: bool = True
    validate_planning_objective: bool = True
    
    # Validation parameters
    min_surface_ha: float = 0.1
    max_surface_ha: float = 1000.0
    min_crops: int = 1
    max_crops: int = 10
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class PlanningTasksConfigManager:
    """Manager for planning tasks configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = PlanningTasksConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "planning_tasks_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = PlanningTasksConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> PlanningTasksConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
planning_tasks_config_manager = PlanningTasksConfigManager()

def get_planning_tasks_config() -> PlanningTasksConfig:
    """Get current planning tasks configuration."""
    return planning_tasks_config_manager.get_config()
