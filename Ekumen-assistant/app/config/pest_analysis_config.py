"""
Pest Analysis Configuration

This module provides configurable parameters for pest identification analysis.
Allows for easy tuning of analysis algorithms without code changes.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class PestAnalysisConfig:
    """Configuration for pest identification analysis."""
    
    # Confidence thresholds
    minimum_confidence: float = 0.3
    high_confidence: float = 0.8
    moderate_confidence: float = 0.6
    
    # Weighting factors for analysis
    damage_pattern_weight: float = 0.6
    pest_indicator_weight: float = 0.4
    
    # Scoring bonuses
    damage_match_bonus: float = 0.1
    indicator_match_bonus: float = 0.05
    
    # Analysis parameters
    max_identifications: int = 5
    include_prevention: bool = True
    include_monitoring: bool = True
    include_economic_threshold: bool = True
    
    # Validation parameters
    min_symptoms: int = 1
    max_symptoms: int = 20
    supported_crops: list = None
    
    def __post_init__(self):
        if self.supported_crops is None:
            self.supported_crops = ["blé", "maïs", "colza"]

@dataclass
class PestValidationConfig:
    """Configuration for input validation."""
    
    # Crop validation
    require_crop_type: bool = True
    allow_unknown_crops: bool = False
    
    # Symptom validation
    require_damage_symptoms: bool = True
    min_symptom_length: int = 2
    max_symptom_length: int = 100
    
    # Pest indicator validation
    require_pest_indicators: bool = False
    max_pest_indicators: int = 20
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class PestAnalysisConfigManager:
    """
    Manager for pest analysis configuration.
    
    Loads configuration from JSON files and provides easy access to parameters.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.analysis_config = PestAnalysisConfig()
        self.validation_config = PestValidationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "pest_analysis_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load analysis config
                if 'analysis_config' in config_data:
                    analysis_data = config_data['analysis_config']
                    self.analysis_config = PestAnalysisConfig(**analysis_data)
                
                # Load validation config
                if 'validation_config' in config_data:
                    validation_data = config_data['validation_config']
                    self.validation_config = PestValidationConfig(**validation_data)
                
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
                "description": "Pest analysis configuration"
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
    
    def get_analysis_config(self) -> PestAnalysisConfig:
        """Get current analysis configuration."""
        return self.analysis_config
    
    def get_validation_config(self) -> PestValidationConfig:
        """Get current validation configuration."""
        return self.validation_config
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.analysis_config = PestAnalysisConfig()
        self.validation_config = PestValidationConfig()

# Global configuration manager instance
pest_config_manager = PestAnalysisConfigManager()

# Convenience functions
def get_pest_analysis_config() -> PestAnalysisConfig:
    """Get current pest analysis configuration."""
    return pest_config_manager.get_analysis_config()

def get_pest_validation_config() -> PestValidationConfig:
    """Get current pest validation configuration."""
    return pest_config_manager.get_validation_config()

def update_pest_analysis_config(**kwargs):
    """Update pest analysis configuration parameters."""
    pest_config_manager.update_analysis_config(**kwargs)

def update_pest_validation_config(**kwargs):
    """Update pest validation configuration parameters."""
    pest_config_manager.update_validation_config(**kwargs)

def save_pest_config(config_path: Optional[str] = None):
    """Save current pest configuration to file."""
    pest_config_manager.save_config(config_path)

def reset_pest_config():
    """Reset pest configuration to default values."""
    pest_config_manager.reset_to_defaults()
