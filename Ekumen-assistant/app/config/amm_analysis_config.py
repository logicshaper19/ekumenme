"""
AMM Analysis Configuration

This module provides configurable parameters for AMM lookup analysis.
Allows for easy tuning of analysis algorithms without code changes.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class AMMAnalysisConfig:
    """Configuration for AMM lookup analysis."""
    
    # Confidence thresholds
    minimum_confidence: float = 0.3
    high_confidence: float = 0.8
    moderate_confidence: float = 0.6
    
    # Weighting factors for analysis
    product_name_weight: float = 0.4
    active_ingredient_weight: float = 0.4
    product_type_weight: float = 0.2
    
    # Scoring bonuses
    exact_match_bonus: float = 0.2
    partial_match_bonus: float = 0.1
    
    # Analysis parameters
    max_results: int = 10
    include_restrictions: bool = True
    include_safety_measures: bool = True
    include_dosage_info: bool = True
    include_environmental_info: bool = True
    
    # Validation parameters
    min_search_criteria: int = 1
    max_search_criteria: int = 10
    supported_product_types: list = None
    
    # Search parameters
    case_sensitive: bool = False
    fuzzy_matching: bool = True
    similarity_threshold: float = 0.7
    
    def __post_init__(self):
        if self.supported_product_types is None:
            self.supported_product_types = [
                "herbicide", "insecticide", "fongicide", "engrais", 
                "fertilisant", "pesticide", "biocontrôle"
            ]

@dataclass
class AMMValidationConfig:
    """Configuration for input validation."""
    
    # Product name validation
    require_product_name: bool = False
    min_product_name_length: int = 2
    max_product_name_length: int = 100
    
    # Active ingredient validation
    require_active_ingredient: bool = False
    min_active_ingredient_length: int = 2
    max_active_ingredient_length: int = 100
    
    # Product type validation
    require_product_type: bool = False
    validate_product_type: bool = True
    
    # Search criteria validation
    require_at_least_one_criteria: bool = True
    max_total_criteria: int = 10
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class AMMAnalysisConfigManager:
    """
    Manager for AMM analysis configuration.
    
    Loads configuration from JSON files and provides easy access to parameters.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.analysis_config = AMMAnalysisConfig()
        self.validation_config = AMMValidationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "amm_analysis_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load analysis config
                if 'analysis_config' in config_data:
                    analysis_data = config_data['analysis_config']
                    self.analysis_config = AMMAnalysisConfig(**analysis_data)
                
                # Load validation config
                if 'validation_config' in config_data:
                    validation_data = config_data['validation_config']
                    self.validation_config = AMMValidationConfig(**validation_data)
                
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
                "description": "AMM analysis configuration"
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
    
    def get_analysis_config(self) -> AMMAnalysisConfig:
        """Get current analysis configuration."""
        return self.analysis_config
    
    def get_validation_config(self) -> AMMValidationConfig:
        """Get current validation configuration."""
        return self.validation_config
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.analysis_config = AMMAnalysisConfig()
        self.validation_config = AMMValidationConfig()

# Global configuration manager instance
amm_config_manager = AMMAnalysisConfigManager()

# Convenience functions
def get_amm_analysis_config() -> AMMAnalysisConfig:
    """Get current AMM analysis configuration."""
    return amm_config_manager.get_analysis_config()

def get_amm_validation_config() -> AMMValidationConfig:
    """Get current AMM validation configuration."""
    return amm_config_manager.get_validation_config()

def update_amm_analysis_config(**kwargs):
    """Update AMM analysis configuration parameters."""
    amm_config_manager.update_analysis_config(**kwargs)

def update_amm_validation_config(**kwargs):
    """Update AMM validation configuration parameters."""
    amm_config_manager.update_validation_config(**kwargs)

def save_amm_config(config_path: Optional[str] = None):
    """Save current AMM configuration to file."""
    amm_config_manager.save_config(config_path)

def reset_amm_config():
    """Reset AMM configuration to default values."""
    amm_config_manager.reset_to_defaults()
