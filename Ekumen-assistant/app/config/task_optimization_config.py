"""
Task Optimization Configuration

This module provides configurable parameters for task sequence optimization.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class TaskOptimizationConfig:
    """Configuration for task sequence optimization."""
    
    # Analysis parameters
    default_algorithm: str = "greedy"
    require_tasks: bool = True
    validate_optimization_objective: bool = True
    max_optimization_time_seconds: int = 30
    
    # Validation parameters
    min_tasks: int = 1
    max_tasks: int = 100
    require_optimization_objective: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class TaskOptimizationConfigManager:
    """Manager for task optimization configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = TaskOptimizationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "task_optimization_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = TaskOptimizationConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> TaskOptimizationConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
task_optimization_config_manager = TaskOptimizationConfigManager()

def get_task_optimization_config() -> TaskOptimizationConfig:
    """Get current task optimization configuration."""
    return task_optimization_config_manager.get_config()
