"""
Biodiversity Assessment Configuration

This module provides configurable parameters for biodiversity assessment.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class BiodiversityAssessmentConfig:
    """Configuration for biodiversity assessment."""
    
    # Analysis parameters
    require_practice_type: bool = True
    validate_land_use: bool = True
    include_species_richness: bool = True
    include_habitat_quality: bool = True
    include_ecosystem_services: bool = True
    include_conservation_status: bool = True
    
    # Validation parameters
    min_conservation_value: float = 0.0
    max_conservation_value: float = 1.0
    require_conservation_measures: bool = False
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class BiodiversityAssessmentConfigManager:
    """Manager for biodiversity assessment configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = BiodiversityAssessmentConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "biodiversity_assessment_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = BiodiversityAssessmentConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> BiodiversityAssessmentConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
biodiversity_assessment_config_manager = BiodiversityAssessmentConfigManager()

def get_biodiversity_assessment_config() -> BiodiversityAssessmentConfig:
    """Get current biodiversity assessment configuration."""
    return biodiversity_assessment_config_manager.get_config()
