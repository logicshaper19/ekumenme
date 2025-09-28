"""
Treatment Plan Configuration

This module provides configurable parameters for treatment plan generation.
Allows for easy tuning of analysis algorithms without code changes.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class TreatmentPlanConfig:
    """Configuration for treatment plan generation."""
    
    # Confidence thresholds
    minimum_confidence: float = 0.6
    high_confidence: float = 0.8
    moderate_confidence: float = 0.7
    
    # Priority weights
    disease_weight: float = 0.4
    pest_weight: float = 0.3
    nutrient_weight: float = 0.3
    
    # Cost estimation
    default_cost: float = 25.0
    cost_multiplier: float = 1.0
    
    # Treatment plan parameters
    max_treatment_steps: int = 20
    include_cost_analysis: bool = True
    include_monitoring_plan: bool = True
    include_prevention_measures: bool = True
    include_treatment_schedule: bool = True
    
    # Priority calculation
    high_priority_threshold: int = 5
    moderate_priority_threshold: int = 2
    low_priority_threshold: int = 1
    
    # Treatment duration estimation
    high_priority_duration: str = "3-4 weeks"
    moderate_priority_duration: str = "2-3 weeks"
    low_priority_duration: str = "1-2 weeks"
    
    # Cost analysis parameters
    default_hectares: int = 10
    cost_per_hectare_calculation: bool = True
    
    # Monitoring parameters
    default_monitoring_frequency: str = "quotidien"
    default_monitoring_duration: str = "2-4 semaines"
    
    # Validation parameters
    require_at_least_one_analysis: bool = True
    max_analyses: int = 10
    supported_crops: list = None
    
    def __post_init__(self):
        if self.supported_crops is None:
            self.supported_crops = ["blé", "maïs", "colza", "tournesol", "légumes"]

@dataclass
class TreatmentValidationConfig:
    """Configuration for input validation."""
    
    # Analysis validation
    require_disease_analysis: bool = False
    require_pest_analysis: bool = False
    require_nutrient_analysis: bool = False
    require_at_least_one_analysis: bool = True
    
    # JSON validation
    validate_json_format: bool = True
    max_json_size: int = 10000  # characters
    
    # Crop validation
    require_crop_type: bool = False
    validate_crop_type: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class TreatmentPlanConfigManager:
    """
    Manager for treatment plan configuration.
    
    Loads configuration from JSON files and provides easy access to parameters.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.treatment_config = TreatmentPlanConfig()
        self.validation_config = TreatmentValidationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "treatment_plan_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load treatment config
                if 'treatment_config' in config_data:
                    treatment_data = config_data['treatment_config']
                    self.treatment_config = TreatmentPlanConfig(**treatment_data)
                
                # Load validation config
                if 'validation_config' in config_data:
                    validation_data = config_data['validation_config']
                    self.validation_config = TreatmentValidationConfig(**validation_data)
                
        except Exception as e:
            # Use default config if loading fails
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            print("Using default configuration.")
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to file."""
        save_path = config_path or self.config_path
        
        config_data = {
            "treatment_config": asdict(self.treatment_config),
            "validation_config": asdict(self.validation_config),
            "metadata": {
                "version": "1.0.0",
                "last_updated": "2024-09-28",
                "description": "Treatment plan configuration"
            }
        }
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config to {save_path}: {e}")
    
    def update_treatment_config(self, **kwargs):
        """Update treatment configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.treatment_config, key):
                setattr(self.treatment_config, key, value)
            else:
                print(f"Warning: Unknown treatment config parameter: {key}")
    
    def update_validation_config(self, **kwargs):
        """Update validation configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.validation_config, key):
                setattr(self.validation_config, key, value)
            else:
                print(f"Warning: Unknown validation config parameter: {key}")
    
    def get_treatment_config(self) -> TreatmentPlanConfig:
        """Get current treatment configuration."""
        return self.treatment_config
    
    def get_validation_config(self) -> TreatmentValidationConfig:
        """Get current validation configuration."""
        return self.validation_config
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.treatment_config = TreatmentPlanConfig()
        self.validation_config = TreatmentValidationConfig()

# Global configuration manager instance
treatment_config_manager = TreatmentPlanConfigManager()

# Convenience functions
def get_treatment_plan_config() -> TreatmentPlanConfig:
    """Get current treatment plan configuration."""
    return treatment_config_manager.get_treatment_config()

def get_treatment_validation_config() -> TreatmentValidationConfig:
    """Get current treatment validation configuration."""
    return treatment_config_manager.get_validation_config()

def update_treatment_plan_config(**kwargs):
    """Update treatment plan configuration parameters."""
    treatment_config_manager.update_treatment_config(**kwargs)

def update_treatment_validation_config(**kwargs):
    """Update treatment validation configuration parameters."""
    treatment_config_manager.update_validation_config(**kwargs)

def save_treatment_config(config_path: Optional[str] = None):
    """Save current treatment configuration to file."""
    treatment_config_manager.save_config(config_path)

def reset_treatment_config():
    """Reset treatment configuration to default values."""
    treatment_config_manager.reset_to_defaults()
