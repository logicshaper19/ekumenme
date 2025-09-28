"""
MesParcelles database models.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    ForeignKey, DECIMAL, UUID, ARRAY, JSON, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from app.core.database import Base
import uuid
from datetime import datetime


class Region(Base):
    """Regions table."""
    __tablename__ = "regions"
    
    id_region = Column(Integer, primary_key=True)
    libelle = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)


class Exploitation(Base):
    """Exploitations (farms/enterprises) table."""
    __tablename__ = "exploitations"
    
    siret = Column(String(20), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ServiceActivation(Base):
    """Service activation tracking table."""
    __tablename__ = "service_activation"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    siret = Column(String(20), ForeignKey("exploitations.siret"))
    millesime_active = Column(ARRAY(Integer))
    millesime_deja_actif = Column(ARRAY(Integer))
    last_updated = Column(DateTime, default=datetime.utcnow)


class ValorisationService(Base):
    """Valorisation services table."""
    __tablename__ = "valorisation_services"
    
    code_national = Column(String(100), primary_key=True)
    libelle = Column(String(200), nullable=False)
    libelle_court = Column(String(100))
    description = Column(Text)


class Culture(Base):
    """Cultures (crops) reference table."""
    __tablename__ = "cultures"
    
    id_culture = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False)


class VarieteCultureCepage(Base):
    """Culture varieties and grape varieties table."""
    __tablename__ = "varietes_cultures_cepages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(200), nullable=False)
    type = Column(String(50))  # 'variete' or 'cepage'


class TypeIntervention(Base):
    """Types of interventions table."""
    __tablename__ = "types_intervention"
    
    id_type_intervention = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False)


class TypeIntrant(Base):
    """Types of intrants (inputs) table."""
    __tablename__ = "types_intrant"
    
    id_type_intrant = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False)
    categorie = Column(String(10))  # 'P' for phytosanitaire, etc.


class Intrant(Base):
    """Intrants (agricultural inputs) reference table."""
    __tablename__ = "intrants"
    
    id_intrant = Column(Integer, primary_key=True)
    libelle = Column(String(300), nullable=False)
    type_intrant_id = Column(Integer, ForeignKey("types_intrant.id_type_intrant"))
    numero_amm_ephy = Column(String(20))  # Link to EPHY database
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    type_intrant = relationship("TypeIntrant")
    phyto_details = relationship("PhytoDetail", back_populates="intrant")
    fertilisant_details = relationship("FertilisantDetail", back_populates="intrant")


class PhytoDetail(Base):
    """Phytosanitary product details table."""
    __tablename__ = "phyto_details"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    intrant_id = Column(Integer, ForeignKey("intrants.id_intrant"))
    code_amm = Column(String(50))  # AMM authorization number
    cible = Column(Text)  # Target pest/disease
    numero_amm_ephy = Column(String(20))  # Direct link to EPHY product
    usage_ephy_id = Column(Integer)  # Link to specific EPHY usage
    dose_utilisee = Column(DECIMAL(10, 4))
    unite_dose = Column(String(20))
    respect_lmr = Column(Boolean, default=True)  # Maximum residue limit compliance
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    intrant = relationship("Intrant", back_populates="phyto_details")


class FertilisantDetail(Base):
    """Fertilizer details table."""
    __tablename__ = "fertilisant_details"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    intrant_id = Column(Integer, ForeignKey("intrants.id_intrant"))
    composition = Column(JSON)  # Store complex fertilizer composition
    
    # Relationships
    intrant = relationship("Intrant", back_populates="fertilisant_details")


class Parcelle(Base):
    """Parcelles (plots/fields) table."""
    __tablename__ = "parcelles"
    
    uuid_parcelle = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    siret_exploitation = Column(String(20), ForeignKey("exploitations.siret"))
    millesime = Column(Integer, nullable=False)
    nom = Column(String(200))
    surface_mesuree_ha = Column(DECIMAL(10, 4))
    insee_commune = Column(String(10))
    geometrie_vide = Column(Boolean, default=False)
    uuid_parcelle_millesime_precedent = Column(PostgresUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referencing foreign key
    __table_args__ = (
        ForeignKey(
            ["uuid_parcelle_millesime_precedent"], 
            ["parcelles.uuid_parcelle"]
        ),
    )
    
    # Relationships
    exploitation = relationship("Exploitation")
    succession_cultures = relationship("SuccessionCulture", back_populates="parcelle")
    cultures_intermediaires = relationship("CultureIntermediaire", back_populates="parcelle")
    interventions = relationship("Intervention", back_populates="parcelle")


class SuccessionCulture(Base):
    """Succession of cultures on a parcel table."""
    __tablename__ = "succession_cultures"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_parcelle = Column(PostgresUUID(as_uuid=True), ForeignKey("parcelles.uuid_parcelle"))
    id_culture = Column(Integer, ForeignKey("cultures.id_culture"))
    rang = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parcelle = relationship("Parcelle", back_populates="succession_cultures")
    culture = relationship("Culture")
    succession_varietes = relationship("SuccessionVariete", back_populates="succession")


class SuccessionVariete(Base):
    """Junction table for varieties/grape varieties in succession cultures."""
    __tablename__ = "succession_varietes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    succession_id = Column(Integer, ForeignKey("succession_cultures.id"))
    variete_id = Column(Integer, ForeignKey("varietes_cultures_cepages.id"))
    
    # Relationships
    succession = relationship("SuccessionCulture", back_populates="succession_varietes")
    variete = relationship("VarieteCultureCepage")


class CultureIntermediaire(Base):
    """Intermediate cultures table."""
    __tablename__ = "cultures_intermediaires"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_parcelle = Column(PostgresUUID(as_uuid=True), ForeignKey("parcelles.uuid_parcelle"))
    id_culture = Column(Integer, ForeignKey("cultures.id_culture"))
    details = Column(JSON)  # Store additional intermediate culture details
    
    # Relationships
    parcelle = relationship("Parcelle", back_populates="cultures_intermediaires")
    culture = relationship("Culture")


class Intervention(Base):
    """Interventions (agricultural operations) table."""
    __tablename__ = "interventions"
    
    uuid_intervention = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_lot = Column(Integer)
    siret_exploitation = Column(String(20), ForeignKey("exploitations.siret"))
    uuid_parcelle = Column(PostgresUUID(as_uuid=True), ForeignKey("parcelles.uuid_parcelle"))
    id_culture = Column(Integer, ForeignKey("cultures.id_culture"))
    surface_travaillee_ha = Column(DECIMAL(10, 4))
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    id_type_intervention = Column(Integer, ForeignKey("types_intervention.id_type_intervention"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exploitation = relationship("Exploitation")
    parcelle = relationship("Parcelle", back_populates="interventions")
    culture = relationship("Culture")
    type_intervention = relationship("TypeIntervention")
    materiels = relationship("InterventionMateriel", back_populates="intervention")
    prestataires = relationship("InterventionPrestataire", back_populates="intervention")
    intrants = relationship("InterventionIntrant", back_populates="intervention")
    extrants = relationship("InterventionExtrant", back_populates="intervention")


class InterventionMateriel(Base):
    """Materials used in interventions table."""
    __tablename__ = "intervention_materiels"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_intervention = Column(PostgresUUID(as_uuid=True), ForeignKey("interventions.uuid_intervention"))
    materiel_details = Column(JSON)  # Store material information as JSON
    
    # Relationships
    intervention = relationship("Intervention", back_populates="materiels")


class InterventionPrestataire(Base):
    """Service providers for interventions table."""
    __tablename__ = "intervention_prestataires"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_intervention = Column(PostgresUUID(as_uuid=True), ForeignKey("interventions.uuid_intervention"))
    prestataire_details = Column(JSON)  # Store service provider information as JSON
    
    # Relationships
    intervention = relationship("Intervention", back_populates="prestataires")


class InterventionIntrant(Base):
    """Inputs used in interventions table."""
    __tablename__ = "intervention_intrants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_intervention = Column(PostgresUUID(as_uuid=True), ForeignKey("interventions.uuid_intervention"))
    id_intrant = Column(Integer, ForeignKey("intrants.id_intrant"))
    quantite_totale = Column(DECIMAL(12, 4), nullable=False)
    unite_intrant_intervention = Column(String(20), nullable=False)
    
    # Relationships
    intervention = relationship("Intervention", back_populates="intrants")
    intrant = relationship("Intrant")


class InterventionExtrant(Base):
    """Outputs from interventions table."""
    __tablename__ = "intervention_extrants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_intervention = Column(PostgresUUID(as_uuid=True), ForeignKey("interventions.uuid_intervention"))
    extrant_details = Column(JSON)  # Store output information as JSON
    
    # Relationships
    intervention = relationship("Intervention", back_populates="extrants")


class ValidationIntervention(Base):
    """Intervention validation table (compliance checking)."""
    __tablename__ = "validations_intervention"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_intervention = Column(PostgresUUID(as_uuid=True), ForeignKey("interventions.uuid_intervention"))
    numero_amm_ephy = Column(String(20))
    usage_autorise = Column(Boolean)
    dose_conforme = Column(Boolean)
    delai_avant_recolte_respecte = Column(Boolean)
    znt_respectees = Column(Boolean)
    date_validation = Column(DateTime, default=datetime.utcnow)
    commentaires = Column(Text)


class ConformiteReglementaire(Base):
    """Table for tracking regulation compliance."""
    __tablename__ = "conformite_reglementaire"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    siret_exploitation = Column(String(20), ForeignKey("exploitations.siret"))
    annee = Column(Integer, nullable=False)
    interventions_controlees = Column(Integer, default=0)
    interventions_conformes = Column(Integer, default=0)
    derniere_verification = Column(DateTime, default=datetime.utcnow)
    commentaires = Column(Text)
    
    # Relationships
    exploitation = relationship("Exploitation")
