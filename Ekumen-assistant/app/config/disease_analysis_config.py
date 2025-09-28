"""
Disease Analysis Configuration

This module provides configurable parameters for disease diagnosis analysis.
Allows for easy tuning of analysis algorithms without code changes.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class DiseaseAnalysisConfig:
    """Configuration for disease diagnosis analysis."""
    
    # Confidence thresholds
    minimum_confidence: float = 0.3
    high_confidence: float = 0.8
    moderate_confidence: float = 0.6
    
    # Weighting factors for analysis
    symptom_weight: float = 0.7
    environmental_weight: float = 0.3
    
    # Scoring bonuses
    symptom_match_bonus: float = 0.1
    environmental_match_bonus: float = 0.05
    
    # Analysis parameters
    max_diagnoses: int = 5
    include_prevention: bool = True
    include_monitoring: bool = True
    include_economic_threshold: bool = True
    include_spread_conditions: bool = True
    
    # Validation parameters
    min_symptoms: int = 1
    max_symptoms: int = 20
    supported_crops: list = None
    
    # Environmental condition thresholds
    humidity_thresholds: Dict[str, float] = None
    temperature_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.supported_crops is None:
            self.supported_crops = ["blé", "maïs", "colza"]
        
        if self.humidity_thresholds is None:
            self.humidity_thresholds = {
                "low": 40.0,
                "moderate": 70.0,
                "high": 80.0,
                "very_high": 85.0
            }
        
        if self.temperature_thresholds is None:
            self.temperature_thresholds = {
                "cool": 20.0,
                "moderate": 25.0,
                "warm": 30.0
            }

@dataclass
class DiseaseValidationConfig:
    """Configuration for input validation."""
    
    # Crop validation
    require_crop_type: bool = True
    allow_unknown_crops: bool = False
    
    # Symptom validation
    require_symptoms: bool = True
    min_symptom_length: int = 2
    max_symptom_length: int = 100
    
    # Environmental condition validation
    require_environmental_conditions: bool = False
    max_environmental_conditions: int = 20
    validate_environmental_values: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class DiseaseAnalysisConfigManager:
    """
    Manager for disease analysis configuration.
    
    Loads configuration from JSON files and provides easy access to parameters.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.analysis_config = DiseaseAnalysisConfig()
        self.validation_config = DiseaseValidationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "disease_analysis_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load analysis config
                if 'analysis_config' in config_data:
                    analysis_data = config_data['analysis_config']
                    self.analysis_config = DiseaseAnalysisConfig(**analysis_data)
                
                # Load validation config
                if 'validation_config' in config_data:
                    validation_data = config_data['validation_config']
                    self.validation_config = DiseaseValidationConfig(**validation_data)
                
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
                "description": "Disease analysis configuration"
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
    
    def get_analysis_config(self) -> DiseaseAnalysisConfig:
        """Get current analysis configuration."""
        return self.analysis_config
    
    def get_validation_config(self) -> DiseaseValidationConfig:
        """Get current validation configuration."""
        return self.validation_config
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.analysis_config = DiseaseAnalysisConfig()
        self.validation_config = DiseaseValidationConfig()

# Global configuration manager instance
disease_config_manager = DiseaseAnalysisConfigManager()

# Convenience functions
def get_disease_analysis_config() -> DiseaseAnalysisConfig:
    """Get current disease analysis configuration."""
    return disease_config_manager.get_analysis_config()

def get_disease_validation_config() -> DiseaseValidationConfig:
    """Get current disease validation configuration."""
    return disease_config_manager.get_validation_config()

def update_disease_analysis_config(**kwargs):
    """Update disease analysis configuration parameters."""
    disease_config_manager.update_analysis_config(**kwargs)

def update_disease_validation_config(**kwargs):
    """Update disease validation configuration parameters."""
    disease_config_manager.update_validation_config(**kwargs)

def save_disease_config(config_path: Optional[str] = None):
    """Save current disease configuration to file."""
    disease_config_manager.save_config(config_path)

def reset_disease_config():
    """Reset disease configuration to default values."""
    disease_config_manager.reset_to_defaults()
