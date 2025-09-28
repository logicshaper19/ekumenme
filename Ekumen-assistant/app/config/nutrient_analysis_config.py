"""
Nutrient Analysis Configuration

This module provides configurable parameters for nutrient deficiency analysis.
Allows for easy tuning of analysis algorithms without code changes.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class AnalysisConfig:
    """Configuration for nutrient deficiency analysis."""
    
    # Confidence thresholds
    minimum_confidence: float = 0.3
    high_confidence: float = 0.8
    moderate_confidence: float = 0.6
    
    # Weighting factors for analysis
    symptom_weight: float = 0.7
    soil_weight: float = 0.3
    
    # Scoring bonuses
    symptom_match_bonus: float = 0.1
    soil_match_bonus: float = 0.05
    
    # Analysis parameters
    max_deficiencies: int = 5
    include_prevention: bool = True
    include_dosage: bool = True
    
    # Validation parameters
    min_symptoms: int = 1
    max_symptoms: int = 20
    supported_crops: list = None
    
    def __post_init__(self):
        if self.supported_crops is None:
            self.supported_crops = ["blé", "maïs", "colza"]

@dataclass
class ValidationConfig:
    """Configuration for input validation."""
    
    # Crop validation
    require_crop_type: bool = True
    allow_unknown_crops: bool = False
    
    # Symptom validation
    require_symptoms: bool = True
    min_symptom_length: int = 2
    max_symptom_length: int = 100
    
    # Soil validation
    require_soil_conditions: bool = False
    max_soil_parameters: int = 20
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class NutrientAnalysisConfigManager:
    """
    Manager for nutrient analysis configuration.
    
    Loads configuration from JSON files and provides easy access to parameters.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.analysis_config = AnalysisConfig()
        self.validation_config = ValidationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "nutrient_analysis_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load analysis config
                if 'analysis_config' in config_data:
                    analysis_data = config_data['analysis_config']
                    self.analysis_config = AnalysisConfig(**analysis_data)
                
                # Load validation config
                if 'validation_config' in config_data:
                    validation_data = config_data['validation_config']
                    self.validation_config = ValidationConfig(**validation_data)
                
        except Exception as e:
            # Use default config if loading fails
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            print("Using default configuration.")
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to file."""
        save_path = config_path or self.config_path
        
        config_data = {
            "analysis_config": asdict(self.analysis_config),
            "validation_config": asdict(self.validation_config),
            "metadata": {
                "version": "1.0.0",
                "last_updated": "2024-09-28",
                "description": "Nutrient analysis configuration"
            }
        }
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config to {save_path}: {e}")
    
    def update_analysis_config(self, **kwargs):
        """Update analysis configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.analysis_config, key):
                setattr(self.analysis_config, key, value)
            else:
                print(f"Warning: Unknown analysis config parameter: {key}")
    
    def update_validation_config(self, **kwargs):
        """Update validation configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.validation_config, key):
                setattr(self.validation_config, key, value)
            else:
                print(f"Warning: Unknown validation config parameter: {key}")
    
    def get_analysis_config(self) -> AnalysisConfig:
        """Get current analysis configuration."""
        return self.analysis_config
    
    def get_validation_config(self) -> ValidationConfig:
        """Get current validation configuration."""
        return self.validation_config
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.analysis_config = AnalysisConfig()
        self.validation_config = ValidationConfig()

# Global configuration manager instance
config_manager = NutrientAnalysisConfigManager()

# Convenience functions
def get_analysis_config() -> AnalysisConfig:
    """Get current analysis configuration."""
    return config_manager.get_analysis_config()

def get_validation_config() -> ValidationConfig:
    """Get current validation configuration."""
    return config_manager.get_validation_config()

def update_analysis_config(**kwargs):
    """Update analysis configuration parameters."""
    config_manager.update_analysis_config(**kwargs)

def update_validation_config(**kwargs):
    """Update validation configuration parameters."""
    config_manager.update_validation_config(**kwargs)

def save_config(config_path: Optional[str] = None):
    """Save current configuration to file."""
    config_manager.save_config(config_path)

def reset_config():
    """Reset configuration to default values."""
    config_manager.reset_to_defaults()
