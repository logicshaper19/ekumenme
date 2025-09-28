"""
Crop Benchmark Configuration

This module provides configurable parameters for crop performance benchmarking.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class CropBenchmarkConfig:
    """Configuration for crop performance benchmarking."""
    
    # Analysis parameters
    require_crop_type: bool = True
    validate_yield_range: bool = True
    validate_quality_range: bool = True
    include_regional_adjustment: bool = True
    
    # Validation parameters
    min_yield: float = 0.0
    max_yield: float = 200.0
    min_quality: float = 0.0
    max_quality: float = 10.0
    default_region: str = "france"
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class CropBenchmarkConfigManager:
    """Manager for crop benchmark configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = CropBenchmarkConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "crop_benchmark_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = CropBenchmarkConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> CropBenchmarkConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
crop_benchmark_config_manager = CropBenchmarkConfigManager()

def get_crop_benchmark_config() -> CropBenchmarkConfig:
    """Get current crop benchmark configuration."""
    return crop_benchmark_config_manager.get_config()
