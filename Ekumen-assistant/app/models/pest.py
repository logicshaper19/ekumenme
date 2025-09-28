"""
Pest Model for Agricultural Pest Knowledge Base

This model stores comprehensive pest information for crop protection,
supporting semantic search and detailed agricultural pest management.
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.database import Base

class Pest(Base):
    """
    Pest model for storing agricultural pest knowledge.
    
    Supports semantic search, damage pattern matching, and treatment recommendations
    for comprehensive crop protection management.
    """
    __tablename__ = "pests"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    scientific_name = Column(String(300), nullable=True)
    common_names = Column(JSON, nullable=True)  # List of alternative names
    
    # Pest classification
    pest_type = Column(String(100), nullable=False, index=True)  # insect, mite, nematode, etc.
    pest_family = Column(String(200), nullable=True)
    life_cycle = Column(String(100), nullable=True)  # annual, perennial, etc.
    severity_level = Column(String(50), nullable=False, index=True)  # low, moderate, high, critical
    
    # Crop associations
    affected_crops = Column(JSON, nullable=False)  # List of crop types
    primary_crop = Column(String(100), nullable=False, index=True)
    
    # Damage and identification
    damage_patterns = Column(JSON, nullable=False)  # List of damage descriptions
    pest_indicators = Column(JSON, nullable=False)  # Signs of pest presence
    visual_identification = Column(JSON, nullable=True)  # Visual characteristics
    behavioral_signs = Column(JSON, nullable=True)  # Behavioral indicators
    
    # Life cycle and biology
    development_stages = Column(JSON, nullable=True)  # Life cycle stages
    reproduction_rate = Column(String(50), nullable=True)  # high, moderate, low
    overwintering_strategy = Column(String(200), nullable=True)
    host_range = Column(JSON, nullable=True)  # Other host plants
    
    # Environmental preferences
    favorable_conditions = Column(JSON, nullable=True)  # Temperature, humidity, etc.
    seasonal_activity = Column(JSON, nullable=True)  # Active seasons
    geographic_distribution = Column(JSON, nullable=True)  # Regions where found
    
    # Treatment and management
    treatment_options = Column(JSON, nullable=False)  # Treatment methods
    prevention_methods = Column(JSON, nullable=True)  # Prevention strategies
    biological_control = Column(JSON, nullable=True)  # Biological control agents
    chemical_control = Column(JSON, nullable=True)  # Chemical control options
    cultural_control = Column(JSON, nullable=True)  # Cultural practices
    
    # Economic and agricultural impact
    yield_impact = Column(String(50), nullable=True)  # low, moderate, high
    economic_threshold = Column(Float, nullable=True)  # Economic damage threshold
    action_threshold = Column(Float, nullable=True)  # Treatment threshold
    resistance_management = Column(JSON, nullable=True)  # Resistance strategies
    
    # Monitoring and detection
    monitoring_methods = Column(JSON, nullable=True)  # How to monitor
    trap_types = Column(JSON, nullable=True)  # Trap recommendations
    scouting_frequency = Column(String(100), nullable=True)  # How often to scout
    
    # Knowledge base metadata
    confidence_score = Column(Float, default=1.0)  # Confidence in information
    data_source = Column(String(200), nullable=True)  # Source of information
    last_verified = Column(DateTime, nullable=True)  # Last verification date
    
    # Search and semantic fields
    description = Column(Text, nullable=True)  # Full description
    keywords = Column(JSON, nullable=True)  # Search keywords
    search_vector = Column(Text, nullable=True)  # For full-text search
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Pest(id={self.id}, name='{self.name}', type='{self.pest_type}', severity='{self.severity_level}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pest to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "scientific_name": self.scientific_name,
            "common_names": self.common_names,
            "pest_type": self.pest_type,
            "pest_family": self.pest_family,
            "life_cycle": self.life_cycle,
            "severity_level": self.severity_level,
            "affected_crops": self.affected_crops,
            "primary_crop": self.primary_crop,
            "damage_patterns": self.damage_patterns,
            "pest_indicators": self.pest_indicators,
            "visual_identification": self.visual_identification,
            "behavioral_signs": self.behavioral_signs,
            "development_stages": self.development_stages,
            "reproduction_rate": self.reproduction_rate,
            "overwintering_strategy": self.overwintering_strategy,
            "host_range": self.host_range,
            "favorable_conditions": self.favorable_conditions,
            "seasonal_activity": self.seasonal_activity,
            "geographic_distribution": self.geographic_distribution,
            "treatment_options": self.treatment_options,
            "prevention_methods": self.prevention_methods,
            "biological_control": self.biological_control,
            "chemical_control": self.chemical_control,
            "cultural_control": self.cultural_control,
            "yield_impact": self.yield_impact,
            "economic_threshold": self.economic_threshold,
            "action_threshold": self.action_threshold,
            "resistance_management": self.resistance_management,
            "monitoring_methods": self.monitoring_methods,
            "trap_types": self.trap_types,
            "scouting_frequency": self.scouting_frequency,
            "confidence_score": self.confidence_score,
            "data_source": self.data_source,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "description": self.description,
            "keywords": self.keywords,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_legacy_data(cls, pest_name: str, crop_type: str, pest_data: Dict[str, Any]) -> 'Pest':
        """Create Pest instance from legacy hardcoded data."""
        return cls(
            name=pest_name,
            pest_type="insect",  # Default, can be updated
            severity_level=pest_data.get("severity", "moderate"),
            affected_crops=[crop_type],
            primary_crop=crop_type,
            damage_patterns=pest_data.get("damage_patterns", []),
            pest_indicators=pest_data.get("pest_indicators", []),
            treatment_options=pest_data.get("treatment", []),
            prevention_methods=pest_data.get("prevention", []),
            confidence_score=0.8,  # Legacy data confidence
            data_source="legacy_hardcoded_data",
            description=f"Pest affecting {crop_type}: {pest_name}",
            keywords=[pest_name, crop_type] + pest_data.get("damage_patterns", []),
            is_active=True
        )
