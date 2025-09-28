"""
Safety Guidelines Configuration

This module provides configurable parameters for safety guidelines retrieval.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class SafetyGuidelinesConfig:
    """Configuration for safety guidelines retrieval."""
    
    # Analysis parameters
    require_product_or_practice: bool = True
    validate_safety_level: bool = True
    include_equipment_requirements: bool = True
    include_emergency_procedures: bool = True
    include_general_guidelines: bool = True
    
    # Validation parameters
    default_safety_level: str = "medium"
    require_emergency_info: bool = True
    require_equipment_info: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class SafetyGuidelinesConfigManager:
    """Manager for safety guidelines configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = SafetyGuidelinesConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "safety_guidelines_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = SafetyGuidelinesConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> SafetyGuidelinesConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
safety_guidelines_config_manager = SafetyGuidelinesConfigManager()

def get_safety_guidelines_config() -> SafetyGuidelinesConfig:
    """Get current safety guidelines configuration."""
    return safety_guidelines_config_manager.get_config()
