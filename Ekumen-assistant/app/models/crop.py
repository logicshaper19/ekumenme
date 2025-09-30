"""
Crop Model for Agricultural Crop Reference Data

This model provides a centralized, standardized repository for crop information
with EPPO codes for international compatibility.

Features:
- EPPO code standardization
- Multilingual support (French, English)
- Scientific classification
- Crop categorization
- Referential integrity for diseases and BBCH stages
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import Base


class Crop(Base):
    """
    Crop reference model
    
    Central repository for crop information with EPPO standardization.
    Used by diseases, BBCH stages, and other agricultural data.
    
    EPPO codes provide international standardization for crop identification,
    enabling language-independent queries and integration with external databases.
    """
    __tablename__ = "crops"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    
    # Names (multilingual)
    name_fr = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="French crop name (e.g., 'blé', 'maïs')"
    )
    name_en = Column(
        String(100),
        nullable=True,
        index=True,
        doc="English crop name (e.g., 'wheat', 'corn')"
    )
    scientific_name = Column(
        String(200),
        nullable=True,
        doc="Scientific/botanical name (e.g., 'Triticum aestivum')"
    )
    
    # EPPO standardization
    eppo_code = Column(
        String(6),
        nullable=False,
        unique=True,
        index=True,
        doc="Official EPPO code (e.g., 'TRZAX' for wheat)"
    )
    
    # Classification
    category = Column(
        String(50),
        nullable=True,
        index=True,
        doc="Crop category: cereal, oilseed, root_crop, legume, fruit, vegetable, forage"
    )
    family = Column(
        String(100),
        nullable=True,
        doc="Botanical family (e.g., 'Poaceae', 'Brassicaceae')"
    )
    
    # Additional metadata
    common_names = Column(
        Text,
        nullable=True,
        doc="JSON array of alternative/regional names"
    )
    description = Column(
        Text,
        nullable=True,
        doc="Crop description and characteristics"
    )
    
    # Agricultural characteristics
    growing_season = Column(
        String(50),
        nullable=True,
        doc="Typical growing season (e.g., 'winter', 'summer', 'year-round')"
    )
    typical_duration_days = Column(
        Integer,
        nullable=True,
        doc="Typical crop cycle duration in days"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether this crop is actively used in the system"
    )
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships (will be added when other models are updated)
    # diseases = relationship("Disease", back_populates="crop")
    # bbch_stages = relationship("BBCHStage", back_populates="crop")
    
    # Indexes
    __table_args__ = (
        Index('ix_crops_name_fr', 'name_fr'),
        Index('ix_crops_eppo_code', 'eppo_code'),
        Index('ix_crops_category', 'category'),
        Index('ix_crops_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Crop(id={self.id}, name_fr='{self.name_fr}', eppo='{self.eppo_code}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert crop to dictionary for API responses"""
        return {
            "id": self.id,
            "name_fr": self.name_fr,
            "name_en": self.name_en,
            "scientific_name": self.scientific_name,
            "eppo_code": self.eppo_code,
            "category": self.category,
            "family": self.family,
            "common_names": self.common_names,
            "description": self.description,
            "growing_season": self.growing_season,
            "typical_duration_days": self.typical_duration_days,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_eppo_code(cls, eppo_code: str, session) -> Optional['Crop']:
        """
        Get crop by EPPO code
        
        Args:
            eppo_code: EPPO code (e.g., 'TRZAX')
            session: Database session
            
        Returns:
            Crop instance or None
        """
        return session.query(cls).filter(
            cls.eppo_code == eppo_code.upper(),
            cls.is_active == True
        ).first()
    
    @classmethod
    def from_french_name(cls, name_fr: str, session) -> Optional['Crop']:
        """
        Get crop by French name
        
        Args:
            name_fr: French crop name (e.g., 'blé')
            session: Database session
            
        Returns:
            Crop instance or None
        """
        return session.query(cls).filter(
            cls.name_fr == name_fr.lower(),
            cls.is_active == True
        ).first()
    
    @classmethod
    def get_by_category(cls, category: str, session) -> list:
        """
        Get all crops in a category
        
        Args:
            category: Crop category (e.g., 'cereal')
            session: Database session
            
        Returns:
            List of Crop instances
        """
        return session.query(cls).filter(
            cls.category == category,
            cls.is_active == True
        ).order_by(cls.name_fr).all()
    
    @classmethod
    def get_all_active(cls, session) -> list:
        """
        Get all active crops
        
        Args:
            session: Database session
            
        Returns:
            List of Crop instances
        """
        return session.query(cls).filter(
            cls.is_active == True
        ).order_by(cls.name_fr).all()
    
    @property
    def display_name(self) -> str:
        """
        Get display name (French name with scientific name if available)
        
        Returns:
            Formatted display name
        """
        if self.scientific_name:
            return f"{self.name_fr} ({self.scientific_name})"
        return self.name_fr
    
    @property
    def is_cereal(self) -> bool:
        """Check if crop is a cereal"""
        return self.category == "cereal"
    
    @property
    def is_oilseed(self) -> bool:
        """Check if crop is an oilseed"""
        return self.category == "oilseed"
    
    @property
    def is_root_crop(self) -> bool:
        """Check if crop is a root crop"""
        return self.category == "root_crop"
    
    @property
    def is_legume(self) -> bool:
        """Check if crop is a legume"""
        return self.category == "legume"


# Helper functions for crop lookups

def get_crop_by_eppo(eppo_code: str, session) -> Optional[Crop]:
    """
    Get crop by EPPO code
    
    Args:
        eppo_code: EPPO code (e.g., 'TRZAX')
        session: Database session
        
    Returns:
        Crop instance or None
    """
    return Crop.from_eppo_code(eppo_code, session)


def get_crop_by_name(name_fr: str, session) -> Optional[Crop]:
    """
    Get crop by French name
    
    Args:
        name_fr: French crop name (e.g., 'blé')
        session: Database session
        
    Returns:
        Crop instance or None
    """
    return Crop.from_french_name(name_fr, session)


def validate_crop_exists(eppo_code: str, session) -> bool:
    """
    Check if crop exists and is active
    
    Args:
        eppo_code: EPPO code to validate
        session: Database session
        
    Returns:
        True if crop exists and is active
    """
    return session.query(Crop).filter(
        Crop.eppo_code == eppo_code.upper(),
        Crop.is_active == True
    ).count() > 0


def get_all_crop_eppo_codes(session) -> list:
    """
    Get list of all active crop EPPO codes
    
    Args:
        session: Database session
        
    Returns:
        List of EPPO codes
    """
    result = session.query(Crop.eppo_code).filter(
        Crop.is_active == True
    ).order_by(Crop.eppo_code).all()
    return [row[0] for row in result]

