"""
Configuration management service with hot-reload capability
Manages JSON configuration files for agricultural agents
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationMetadata:
    """Metadata for configuration files"""
    file_path: Path
    last_modified: datetime
    version: str
    description: str
    loaded_at: datetime


class ConfigurationService:
    """
    Service for managing configuration files with hot-reload capability
    
    Features:
    - Hot-reload of configuration changes
    - Configuration validation
    - Version tracking
    - Thread-safe access
    """
    
    def __init__(self, config_dir: str = "app/config"):
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, ConfigurationMetadata] = {}
        self._lock = Lock()
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized ConfigurationService with directory: {self.config_dir}")
    
    def get_config(self, config_name: str, auto_reload: bool = True) -> Dict[str, Any]:
        """
        Get configuration with optional auto-reload
        
        Args:
            config_name: Name of config file (without .json extension)
            auto_reload: Whether to check for file changes and reload
            
        Returns:
            Configuration dictionary
        """
        with self._lock:
            config_file = f"{config_name}.json"
            
            # Check if we need to load or reload
            if auto_reload and self._should_reload(config_name):
                self._load_config(config_name)
            elif config_name not in self._configs:
                self._load_config(config_name)
            
            return self._configs.get(config_name, {})
    
    def _should_reload(self, config_name: str) -> bool:
        """Check if configuration file should be reloaded"""
        if config_name not in self._metadata:
            return True
        
        config_file = self.config_dir / f"{config_name}.json"
        if not config_file.exists():
            return False
        
        current_mtime = datetime.fromtimestamp(config_file.stat().st_mtime)
        stored_mtime = self._metadata[config_name].last_modified
        
        return current_mtime > stored_mtime
    
    def _load_config(self, config_name: str) -> None:
        """Load configuration from file"""
        config_file = self.config_dir / f"{config_name}.json"
        
        try:
            if not config_file.exists():
                logger.warning(f"Configuration file not found: {config_file}")
                self._configs[config_name] = {}
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate configuration
            self._validate_config(config_name, config_data)
            
            # Store configuration
            self._configs[config_name] = config_data
            
            # Update metadata
            file_stat = config_file.stat()
            metadata = ConfigurationMetadata(
                file_path=config_file,
                last_modified=datetime.fromtimestamp(file_stat.st_mtime),
                version=config_data.get('metadata', {}).get('version', '1.0.0'),
                description=config_data.get('metadata', {}).get('description', ''),
                loaded_at=datetime.now()
            )
            self._metadata[config_name] = metadata
            
            logger.info(f"Loaded configuration: {config_name} (version: {metadata.version})")
            
        except Exception as e:
            logger.error(f"Failed to load configuration {config_name}: {e}")
            # Keep existing config if reload fails
            if config_name not in self._configs:
                self._configs[config_name] = {}
    
    def _validate_config(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """Validate configuration data"""
        # Basic validation - ensure metadata exists
        if 'metadata' not in config_data:
            logger.warning(f"Configuration {config_name} missing metadata section")
        
        # Specific validation for regulatory compliance config
        if config_name == 'regulatory_compliance_config':
            self._validate_regulatory_config(config_data)
    
    def _validate_regulatory_config(self, config_data: Dict[str, Any]) -> None:
        """Validate regulatory compliance configuration"""
        required_sections = [
            'validation_settings',
            'znt_requirements', 
            'application_limits',
            'safety_intervals'
        ]
        
        for section in required_sections:
            if section not in config_data:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate ZNT requirements
        znt = config_data.get('znt_requirements', {})
        if 'cours_eau' in znt:
            cours_eau = znt['cours_eau']
            if cours_eau.get('minimum_meters', 0) < 0:
                raise ValueError("ZNT minimum_meters must be >= 0")
    
    def get_regulatory_config(self) -> Dict[str, Any]:
        """Get regulatory compliance configuration"""
        return self.get_config('regulatory_compliance_config')
    
    def get_znt_requirements(self, zone_type: str = 'cours_eau') -> Dict[str, Any]:
        """Get ZNT requirements for specific zone type"""
        config = self.get_regulatory_config()
        return config.get('znt_requirements', {}).get(zone_type, {})
    
    def get_application_limits(self, substance: str) -> Dict[str, Any]:
        """Get application limits for specific substance"""
        config = self.get_regulatory_config()
        return config.get('application_limits', {}).get(substance.lower(), {})
    
    def get_safety_intervals(self, crop_type: str = None) -> Dict[str, Any]:
        """Get safety intervals, optionally for specific crop"""
        config = self.get_regulatory_config()
        intervals = config.get('safety_intervals', {})
        
        if crop_type:
            crop_specific = intervals.get('crop_specific', {})
            if crop_type in crop_specific:
                return {
                    'pre_harvest_days': crop_specific[crop_type],
                    'source': 'crop_specific'
                }
        
        return {
            'pre_harvest_days': intervals.get('default_pre_harvest_days', 14),
            'source': 'default'
        }
    
    def get_seasonal_adjustments(self, season: str = None) -> Dict[str, Any]:
        """Get seasonal adjustment factors"""
        config = self.get_regulatory_config()
        adjustments = config.get('seasonal_adjustments', {})
        
        if season:
            return adjustments.get(season, {})
        
        return adjustments
    
    def get_regional_factors(self, region: str = None) -> Dict[str, Any]:
        """Get regional adjustment factors"""
        config = self.get_regulatory_config()
        factors = config.get('regional_factors', {})
        
        if region:
            return factors.get(region.lower(), {})
        
        return factors
    
    def get_compliance_scoring_config(self) -> Dict[str, Any]:
        """Get compliance scoring configuration"""
        config = self.get_regulatory_config()
        return config.get('compliance_scoring', {})
    
    def reload_all_configs(self) -> None:
        """Force reload of all configurations"""
        with self._lock:
            config_names = list(self._configs.keys())
            for config_name in config_names:
                self._load_config(config_name)
            
            logger.info(f"Reloaded {len(config_names)} configurations")
    
    def get_config_info(self, config_name: str) -> Optional[ConfigurationMetadata]:
        """Get metadata information about a configuration"""
        return self._metadata.get(config_name)
    
    def list_configurations(self) -> Dict[str, ConfigurationMetadata]:
        """List all loaded configurations with metadata"""
        return self._metadata.copy()


# Global configuration service instance
_config_service: Optional[ConfigurationService] = None


def get_configuration_service() -> ConfigurationService:
    """Get global configuration service instance"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
    return _config_service


def get_regulatory_config() -> Dict[str, Any]:
    """Convenience function to get regulatory configuration"""
    return get_configuration_service().get_regulatory_config()
