"""
Disease Model for Agricultural Disease Knowledge Base

This model stores comprehensive disease information for crop health diagnosis,
supporting semantic search and detailed agricultural knowledge management.
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.database import Base

class Disease(Base):
    """
    Disease model for storing agricultural disease knowledge.
    
    Supports semantic search, symptom matching, and treatment recommendations
    for comprehensive crop health management.
    """
    __tablename__ = "diseases"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    scientific_name = Column(String(300), nullable=True)
    common_names = Column(JSON, nullable=True)  # List of alternative names
    
    # Disease classification
    disease_type = Column(String(100), nullable=False, index=True)  # fungal, bacterial, viral, etc.
    pathogen_name = Column(String(200), nullable=True)
    severity_level = Column(String(50), nullable=False, index=True)  # low, moderate, high, critical
    eppo_code = Column(String(10), nullable=True, index=True)  # EPPO code for international standardization
    
    # Crop associations
    affected_crops = Column(JSON, nullable=False)  # List of crop types
    primary_crop = Column(String(100), nullable=False, index=True)
    primary_crop_eppo = Column(String(6), nullable=True, index=True)  # EPPO code for primary crop (e.g., TRZAX for wheat)
    crop_id = Column(Integer, nullable=True, index=True, doc="Foreign key to crops table (optional for referential integrity)")
    
    # Symptoms and identification
    symptoms = Column(JSON, nullable=False)  # List of symptom descriptions
    visual_indicators = Column(JSON, nullable=True)  # Visual signs
    damage_patterns = Column(JSON, nullable=True)  # Damage descriptions
    
    # Environmental conditions
    favorable_conditions = Column(JSON, nullable=True)  # Temperature, humidity, etc.
    seasonal_occurrence = Column(JSON, nullable=True)  # Seasons when disease occurs
    geographic_distribution = Column(JSON, nullable=True)  # Regions where found
    
    # Treatment and management
    treatment_options = Column(JSON, nullable=False)  # Treatment methods
    prevention_methods = Column(JSON, nullable=True)  # Prevention strategies
    organic_treatments = Column(JSON, nullable=True)  # Organic treatment options
    chemical_treatments = Column(JSON, nullable=True)  # Chemical treatment options
    
    # Economic and agricultural impact
    yield_impact = Column(String(50), nullable=True)  # low, moderate, high
    economic_threshold = Column(Float, nullable=True)  # Economic damage threshold
    resistance_management = Column(JSON, nullable=True)  # Resistance strategies
    
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
        return f"<Disease(id={self.id}, name='{self.name}', type='{self.disease_type}', severity='{self.severity_level}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert disease to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "scientific_name": self.scientific_name,
            "common_names": self.common_names,
            "disease_type": self.disease_type,
            "pathogen_name": self.pathogen_name,
            "severity_level": self.severity_level,
            "affected_crops": self.affected_crops,
            "primary_crop": self.primary_crop,
            "primary_crop_eppo": self.primary_crop_eppo,
            "crop_id": self.crop_id,
            "eppo_code": self.eppo_code,
            "symptoms": self.symptoms,
            "visual_indicators": self.visual_indicators,
            "damage_patterns": self.damage_patterns,
            "favorable_conditions": self.favorable_conditions,
            "seasonal_occurrence": self.seasonal_occurrence,
            "geographic_distribution": self.geographic_distribution,
            "treatment_options": self.treatment_options,
            "prevention_methods": self.prevention_methods,
            "organic_treatments": self.organic_treatments,
            "chemical_treatments": self.chemical_treatments,
            "yield_impact": self.yield_impact,
            "economic_threshold": self.economic_threshold,
            "resistance_management": self.resistance_management,
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
    def from_legacy_data(cls, disease_name: str, crop_type: str, disease_data: Dict[str, Any]) -> 'Disease':
        """Create Disease instance from legacy hardcoded data."""
        return cls(
            name=disease_name,
            disease_type="fungal",  # Default, can be updated
            severity_level=disease_data.get("severity", "moderate"),
            affected_crops=[crop_type],
            primary_crop=crop_type,
            symptoms=disease_data.get("symptoms", []),
            favorable_conditions=disease_data.get("conditions", {}),
            treatment_options=disease_data.get("treatment", []),
            prevention_methods=disease_data.get("prevention", []),
            confidence_score=0.8,  # Legacy data confidence
            data_source="legacy_hardcoded_data",
            description=f"Disease affecting {crop_type}: {disease_name}",
            keywords=[disease_name, crop_type] + disease_data.get("symptoms", []),
            is_active=True
        )
