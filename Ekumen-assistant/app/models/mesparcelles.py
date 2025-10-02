"""
MesParcelles models for agricultural data
Handles exploitations, parcelles, and interventions from MesParcelles API
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Exploitation(Base):
    """Farm exploitation model"""
    
    __tablename__ = "exploitations"
    
    # Primary key
    siret = Column(String(14), primary_key=True, index=True)
    
    # Basic information
    nom = Column(String(255), nullable=True)
    region_code = Column(String(2), nullable=True, index=True)
    department_code = Column(String(3), nullable=True, index=True)
    commune_insee = Column(String(5), nullable=True, index=True)
    
    # Farm details
    surface_totale_ha = Column(Numeric(10, 2), nullable=True)
    type_exploitation = Column(String(100), nullable=True)
    
    # Organic certification
    bio = Column(Boolean, default=False)
    certification_bio = Column(String(50), nullable=True)
    date_certification_bio = Column(Date, nullable=True)
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    parcelles = relationship("Parcelle", back_populates="exploitation", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="exploitation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Exploitation(siret={self.siret}, nom={self.nom})>"


class Parcelle(Base):
    """Agricultural parcel/field model"""
    
    __tablename__ = "parcelles"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    siret = Column(String(14), ForeignKey("exploitations.siret"), nullable=False, index=True)
    
    # MesParcelles data
    uuid_parcelle = Column(UUID(as_uuid=True), unique=True, nullable=True, index=True)
    millesime = Column(Integer, nullable=False, index=True)  # Vintage year
    
    # Basic information
    nom = Column(String(255), nullable=False)
    numero_ilot = Column(String(50), nullable=True)
    numero_parcelle = Column(String(50), nullable=True)
    
    # Location
    commune_insee = Column(String(5), nullable=True, index=True)
    
    # Surface
    surface_ha = Column(Numeric(10, 2), nullable=False)
    surface_mesuree_ha = Column(Numeric(10, 2), nullable=True)  # From MesParcelles
    
    # Current crop
    culture_code = Column(String(10), nullable=True, index=True)
    id_culture = Column(Integer, nullable=True)  # MesParcelles culture ID
    variete = Column(String(255), nullable=True)
    id_variete = Column(Integer, nullable=True)  # MesParcelles variety ID
    
    # Crop details
    date_semis = Column(Date, nullable=True)
    bbch_stage = Column(Integer, nullable=True)  # Growth stage (0-99)
    
    # Geometry
    geometrie = Column(JSONB, nullable=True)  # GeoJSON geometry
    geometrie_vide = Column(Boolean, default=False)
    
    # Crop succession
    succession_cultures = Column(JSONB, nullable=True)  # Crop rotation data
    culture_intermediaire = Column(JSONB, nullable=True)  # Cover crops
    
    # Links to previous years
    link_parcelle_millesime_precedent = Column(String(500), nullable=True)
    uuid_parcelle_millesime_precedent = Column(UUID(as_uuid=True), nullable=True)
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    exploitation = relationship("Exploitation", back_populates="parcelles")
    interventions = relationship("Intervention", back_populates="parcelle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Parcelle(nom={self.nom}, surface={self.surface_ha}ha, culture={self.culture_code})>"


class Intervention(Base):
    """Agricultural intervention/operation model"""
    
    __tablename__ = "interventions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    parcelle_id = Column(UUID(as_uuid=True), ForeignKey("parcelles.id"), nullable=False, index=True)
    siret = Column(String(14), ForeignKey("exploitations.siret"), nullable=False, index=True)
    
    # MesParcelles data
    uuid_intervention = Column(UUID(as_uuid=True), unique=True, nullable=True, index=True)
    
    # Intervention details
    type_intervention = Column(String(100), nullable=False, index=True)
    id_type_intervention = Column(Integer, nullable=True)  # MesParcelles type ID
    date_intervention = Column(Date, nullable=False, index=True)
    date_debut = Column(Date, nullable=True)
    date_fin = Column(Date, nullable=True)
    
    # Surface worked
    surface_ha = Column(Numeric(10, 2), nullable=True)
    surface_travaillee_ha = Column(Numeric(10, 2), nullable=True)  # From MesParcelles
    
    # Crop information
    id_culture = Column(Integer, nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Products/inputs used
    produit_utilise = Column(String(255), nullable=True)
    dose_ha = Column(String(100), nullable=True)
    
    # Materials/equipment
    materiel_utilise = Column(String(255), nullable=True)
    
    # Intrants (inputs) - detailed product usage
    intrants = Column(JSONB, nullable=True)  # List of products with quantities
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    parcelle = relationship("Parcelle", back_populates="interventions")
    exploitation = relationship("Exploitation", back_populates="interventions")
    
    def __repr__(self):
        return f"<Intervention(type={self.type_intervention}, date={self.date_intervention})>"


class Intrant(Base):
    """Agricultural input/product model (fertilizers, pesticides, etc.)"""
    
    __tablename__ = "intrants"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Product identification
    libelle = Column(String(255), nullable=False)
    id_intrant = Column(Integer, unique=True, nullable=True, index=True)  # MesParcelles ID
    
    # Product type
    type_intrant = Column(String(100), nullable=True, index=True)
    id_type_intrant = Column(Integer, nullable=True)
    
    # Regulatory
    code_amm = Column(String(20), nullable=True, index=True)  # AMM authorization code
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Intrant(libelle={self.libelle}, code_amm={self.code_amm})>"

