"""
Weather Data Configuration

This module provides configurable parameters for weather data analysis.
Allows for easy tuning of analysis algorithms without code changes.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class WeatherDataConfig:
    """Configuration for weather data analysis."""
    
    # API Configuration
    api_key: str = "b6683958ab174bb6ae0134111252809"
    base_url: str = "https://api.weatherapi.com/v1"
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # Forecast Configuration
    max_days: int = 14
    min_days: int = 1
    default_days: int = 7
    
    # Weather Parameters
    temperature_weight: float = 0.3
    humidity_weight: float = 0.2
    wind_weight: float = 0.2
    precipitation_weight: float = 0.3
    
    # Confidence Thresholds
    minimum_confidence: float = 0.7
    high_confidence: float = 0.9
    moderate_confidence: float = 0.8
    
    # Agricultural Guidelines
    treatment_optimal_temp_min: float = 10.0
    treatment_optimal_temp_max: float = 25.0
    treatment_optimal_humidity_min: float = 40.0
    treatment_optimal_humidity_max: float = 80.0
    treatment_max_wind_speed: float = 20.0
    treatment_max_precipitation: float = 0.0
    
    harvest_optimal_temp_min: float = 15.0
    harvest_optimal_temp_max: float = 30.0
    harvest_optimal_humidity_min: float = 30.0
    harvest_optimal_humidity_max: float = 70.0
    harvest_max_wind_speed: float = 15.0
    harvest_max_precipitation: float = 0.0
    
    planting_optimal_temp_min: float = 10.0
    planting_optimal_temp_max: float = 25.0
    planting_optimal_humidity_min: float = 40.0
    planting_optimal_humidity_max: float = 80.0
    planting_max_wind_speed: float = 15.0
    planting_max_precipitation: float = 5.0
    
    # Data Processing
    include_agricultural_analysis: bool = True
    include_weather_alerts: bool = True
    include_historical_data: bool = False
    cache_duration_hours: int = 1
    
    # Validation Parameters
    require_location: bool = True
    validate_days_range: bool = True
    max_location_length: int = 100
    min_location_length: int = 2
    
    # Error Handling
    use_fallback_data: bool = True
    log_api_errors: bool = True
    return_detailed_errors: bool = True

@dataclass
class WeatherValidationConfig:
    """Configuration for input validation."""
    
    # Location validation
    require_location: bool = True
    min_location_length: int = 2
    max_location_length: int = 100
    validate_location_format: bool = True
    
    # Days validation
    require_days: bool = False
    min_days: int = 1
    max_days: int = 14
    validate_days_range: bool = True
    
    # API validation
    validate_api_key: bool = True
    check_api_limits: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class WeatherDataConfigManager:
    """
    Manager for weather data configuration.
    
    Loads configuration from JSON files and provides easy access to parameters.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.weather_config = WeatherDataConfig()
        self.validation_config = WeatherValidationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "weather_data_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load weather config
                if 'weather_config' in config_data:
                    weather_data = config_data['weather_config']
                    self.weather_config = WeatherDataConfig(**weather_data)
                
                # Load validation config
                if 'validation_config' in config_data:
                    validation_data = config_data['validation_config']
                    self.validation_config = WeatherValidationConfig(**validation_data)
                
        except Exception as e:
            # Use default config if loading fails
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            print("Using default configuration.")
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to file."""
        save_path = config_path or self.config_path
        
        config_data = {
            "weather_config": asdict(self.weather_config),
            "validation_config": asdict(self.validation_config),
            "metadata": {
                "version": "1.0.0",
                "last_updated": "2024-09-28",
                "description": "Weather data configuration"
            }
        }
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config to {save_path}: {e}")
    
    def update_weather_config(self, **kwargs):
        """Update weather configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.weather_config, key):
                setattr(self.weather_config, key, value)
            else:
                print(f"Warning: Unknown weather config parameter: {key}")
    
    def update_validation_config(self, **kwargs):
        """Update validation configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.validation_config, key):
                setattr(self.validation_config, key, value)
            else:
                print(f"Warning: Unknown validation config parameter: {key}")
    
    def get_weather_config(self) -> WeatherDataConfig:
        """Get current weather configuration."""
        return self.weather_config
    
    def get_validation_config(self) -> WeatherValidationConfig:
        """Get current validation configuration."""
        return self.validation_config
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.weather_config = WeatherDataConfig()
        self.validation_config = WeatherValidationConfig()

# Global configuration manager instance
weather_config_manager = WeatherDataConfigManager()

# Convenience functions
def get_weather_data_config() -> WeatherDataConfig:
    """Get current weather data configuration."""
    return weather_config_manager.get_weather_config()

def get_weather_validation_config() -> WeatherValidationConfig:
    """Get current weather validation configuration."""
    return weather_config_manager.get_validation_config()

def update_weather_data_config(**kwargs):
    """Update weather data configuration parameters."""
    weather_config_manager.update_weather_config(**kwargs)

def update_weather_validation_config(**kwargs):
    """Update weather validation configuration parameters."""
    weather_config_manager.update_validation_config(**kwargs)

def save_weather_config(config_path: Optional[str] = None):
    """Save current weather configuration to file."""
    weather_config_manager.save_config(config_path)

def reset_weather_config():
    """Reset weather configuration to default values."""
    weather_config_manager.reset_to_defaults()
