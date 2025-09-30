"""
BBCH Growth Stage Model

BBCH Scale (Biologische Bundesanstalt, Bundessortenamt and CHemical industry)
European standard for describing crop phenological development stages (0-99)

Used for:
- Precise crop development tracking
- Stage-specific crop coefficients (Kc) for ET calculations
- Regulatory compliance (pesticide application timing)
- Intervention planning and recommendations
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base


class BBCHStage(Base):
    """
    BBCH growth stage model
    
    Stores crop-specific phenological stages with:
    - BBCH decimal code (0-99)
    - Principal growth stage (0-9)
    - Multilingual descriptions
    - Crop coefficient (Kc) for evapotranspiration
    - Typical duration
    """
    
    __tablename__ = "bbch_stages"

    # BBCH codes (bbch_code is the primary key in the database)
    bbch_code = Column(
        Integer,
        primary_key=True,
        nullable=False,
        index=True,
        doc="BBCH decimal code (0-99)"
    )
    principal_stage = Column(
        Integer,
        nullable=False,
        index=True,
        doc="Principal growth stage (0-9): 0=germination, 1=leaf, 2=tillering, 3=stem, 4=vegetative, 5=heading, 6=flowering, 7=fruit, 8=ripening, 9=senescence"
    )

    # Crop identification
    crop_type = Column(String(50), nullable=True, index=True)
    crop_eppo_code = Column(
        String(6),
        nullable=True,
        index=True,
        doc="EPPO code for crop (e.g., TRZAX for wheat) - links to crops table"
    )
    
    # Descriptions
    description_fr = Column(
        Text,
        nullable=False,
        doc="French description of growth stage"
    )
    description_en = Column(
        Text,
        nullable=True,
        doc="English description of growth stage"
    )
    
    # Agricultural parameters (optional - may not be populated)
    typical_duration_days = Column(
        Integer,
        nullable=True,
        doc="Typical duration of this stage in days (climate-dependent)"
    )
    kc_value = Column(
        Numeric(precision=3, scale=2),
        nullable=True,
        doc="Crop coefficient (Kc) for evapotranspiration calculation (0.0-2.0)"
    )
    
    # Additional information
    notes = Column(
        Text,
        nullable=True,
        doc="Additional notes (e.g., 'Critical stage', 'Peak water demand', 'Harvest ready')"
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('bbch_code >= 0 AND bbch_code <= 99', name='ck_bbch_code_range'),
        CheckConstraint('principal_stage >= 0 AND principal_stage <= 9', name='ck_principal_stage_range'),
        CheckConstraint('kc_value IS NULL OR (kc_value >= 0 AND kc_value <= 2.0)', name='ck_kc_value_range'),
        Index('ix_bbch_crop_type', 'crop_type'),
        Index('ix_bbch_crop_code', 'crop_type', 'bbch_code'),
        Index('ix_bbch_principal', 'crop_type', 'principal_stage'),
    )
    
    def __repr__(self):
        return f"<BBCHStage(crop={self.crop_type}, code={self.bbch_code}, stage={self.description_fr})>"
    
    @property
    def fao56_stage(self) -> str:
        """
        Map BBCH code to FAO-56 crop development stage
        
        FAO-56 defines 4 stages:
        - Initial: Planting to ~10% ground cover
        - Development: ~10% to ~70-80% ground cover
        - Mid-season: ~70-80% ground cover to maturity
        - Late season: Maturity to harvest
        
        Returns:
            One of: 'initial', 'development', 'mid_season', 'late_season'
        """
        if self.bbch_code < 20:
            return 'initial'
        elif self.bbch_code < 50:
            return 'development'
        elif self.bbch_code < 80:
            return 'mid_season'
        else:
            return 'late_season'
    
    @property
    def is_critical_stage(self) -> bool:
        """
        Check if this is a critical growth stage
        
        Critical stages typically include:
        - Flowering (60-69)
        - Early fruit development (70-79)
        
        Returns:
            True if critical stage
        """
        return 60 <= self.bbch_code <= 79
    
    @property
    def principal_stage_name(self) -> str:
        """
        Get human-readable name for principal stage
        
        Returns:
            French name of principal stage
        """
        stage_names = {
            0: "Germination",
            1: "Développement des feuilles",
            2: "Formation des talles/ramifications",
            3: "Élongation de la tige",
            4: "Développement des organes récoltables",
            5: "Apparition de l'inflorescence",
            6: "Floraison",
            7: "Développement du fruit",
            8: "Maturation",
            9: "Sénescence"
        }
        return stage_names.get(self.principal_stage, "Inconnu")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "bbch_code": self.bbch_code,
            "principal_stage": self.principal_stage,
            "principal_stage_name": self.principal_stage_name,
            "crop_type": self.crop_type,
            "crop_eppo_code": self.crop_eppo_code,
            "description_fr": self.description_fr,
            "description_en": self.description_en,
            "typical_duration_days": self.typical_duration_days,
            "kc_value": float(self.kc_value) if self.kc_value else None,
            "fao56_stage": self.fao56_stage,
            "is_critical_stage": self.is_critical_stage,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Helper functions for BBCH lookups

def get_kc_for_bbch(crop_type: str, bbch_code: int, session) -> float:
    """
    Get crop coefficient (Kc) for specific BBCH stage
    
    Args:
        crop_type: Crop type (e.g., 'blé', 'maïs')
        bbch_code: BBCH code (0-99)
        session: Database session
        
    Returns:
        Kc value (float) or default value if not found
    """
    stage = session.query(BBCHStage).filter(
        BBCHStage.crop_type == crop_type,
        BBCHStage.bbch_code == bbch_code
    ).first()
    
    if stage and stage.kc_value:
        return float(stage.kc_value)
    
    # Fallback to nearest stage
    nearest = session.query(BBCHStage).filter(
        BBCHStage.crop_type == crop_type,
        BBCHStage.kc_value.isnot(None)
    ).order_by(
        func.abs(BBCHStage.bbch_code - bbch_code)
    ).first()
    
    if nearest and nearest.kc_value:
        return float(nearest.kc_value)
    
    # Ultimate fallback
    return 0.8


def get_bbch_range_for_fao56_stage(crop_type: str, fao56_stage: str, session) -> list:
    """
    Get BBCH codes for a FAO-56 stage
    
    Args:
        crop_type: Crop type
        fao56_stage: One of 'initial', 'development', 'mid_season', 'late_season'
        session: Database session
        
    Returns:
        List of BBCH codes in that stage
    """
    stage_ranges = {
        'initial': (0, 19),
        'development': (20, 49),
        'mid_season': (50, 79),
        'late_season': (80, 99)
    }
    
    min_code, max_code = stage_ranges.get(fao56_stage, (0, 99))
    
    stages = session.query(BBCHStage).filter(
        BBCHStage.crop_type == crop_type,
        BBCHStage.bbch_code >= min_code,
        BBCHStage.bbch_code <= max_code
    ).order_by(BBCHStage.bbch_code).all()
    
    return [stage.bbch_code for stage in stages]

