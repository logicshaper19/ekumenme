"""
Regulatory Compliance Configuration

This module provides configurable parameters for regulatory compliance checking.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

@dataclass
class RegulatoryComplianceConfig:
    """Configuration for regulatory compliance checking."""
    
    # Analysis parameters
    require_practice_type: bool = True
    validate_products: bool = True
    validate_location: bool = True
    validate_timing: bool = True
    include_amm_check: bool = True
    include_znt_check: bool = True
    include_timing_check: bool = True
    include_equipment_check: bool = True
    
    # Validation parameters
    min_compliance_score: float = 0.0
    max_compliance_score: float = 100.0
    require_critical_violations: bool = True
    require_major_violations: bool = True
    
    # Error handling
    strict_validation: bool = True
    return_validation_errors: bool = True

class RegulatoryComplianceConfigManager:
    """Manager for regulatory compliance configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = RegulatoryComplianceConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "regulatory_compliance_config.json")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = RegulatoryComplianceConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def get_config(self) -> RegulatoryComplianceConfig:
        """Get current configuration."""
        return self.config

# Global configuration manager
regulatory_compliance_config_manager = RegulatoryComplianceConfigManager()

def get_regulatory_compliance_config() -> RegulatoryComplianceConfig:
    """Get current regulatory compliance configuration."""
    return regulatory_compliance_config_manager.get_config()
