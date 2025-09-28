"""
Planning Costs Configuration

This module provides configurable parameters for planning cost calculation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class PlanningCostsConfig:
    """Configuration for planning cost calculation."""
    
    # Analysis parameters
    require_tasks: bool = True
    validate_cost_components: bool = True
    include_labor_costs: bool = True
    include_equipment_costs: bool = True
    include_material_costs: bool = True
    
    # Validation parameters
    min_tasks: int = 1
    max_tasks: int = 100
    require_region: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class PlanningCostsConfigManager:
    """Manager for planning costs configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = PlanningCostsConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "planning_costs_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = PlanningCostsConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> PlanningCostsConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
planning_costs_config_manager = PlanningCostsConfigManager()

def get_planning_costs_config() -> PlanningCostsConfig:
    """Get current planning costs configuration."""
    return planning_costs_config_manager.get_config()
