"""
Product models for agricultural chatbot
Handles French agricultural product registration database (MFSC and PPP products)
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Integer, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class ProductType(str, enum.Enum):
    """Types of agricultural products"""
    MFSC = "MFSC"  # Matières Fertilisantes et Supports de Culture
    PPP = "PPP"    # Produits Phytopharmaceutiques


class AuthorizationStatus(str, enum.Enum):
    """Product authorization status"""
    AUTORISE = "AUTORISE"
    RETIRE = "RETIRE"
    SUSPENDU = "SUSPENDU"
    EN_COURS = "EN_COURS"


class UsageStatus(str, enum.Enum):
    """Usage authorization status"""
    AUTORISE = "Autorise"
    RETIRE = "Retire"
    SUSPENDU = "Suspendu"
    EN_COURS = "En cours"


class Product(Base):
    """Core product table (combines MFSC and PPP products)"""
    
    __tablename__ = "products"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Product identification
    type_produit = Column(SQLEnum(ProductType), nullable=False, index=True)
    numero_amm = Column(String(20), unique=True, nullable=False, index=True)  # French AMM number
    nom_produit = Column(String(200), nullable=False, index=True)
    seconds_noms_commerciaux = Column(Text, nullable=True)
    titulaire = Column(String(200), nullable=True)  # Product holder
    
    # Product details
    type_commercial = Column(String(50), nullable=True)
    gamme_usage = Column(String(50), nullable=True)
    etat_autorisation = Column(SQLEnum(AuthorizationStatus), default=AuthorizationStatus.AUTORISE, nullable=False, index=True)
    
    # Dates
    date_retrait_produit = Column(DateTime, nullable=True)
    date_premiere_autorisation = Column(DateTime, nullable=True)
    
    # Reference product
    num_amm_reference = Column(String(20), nullable=True)
    nom_produit_reference = Column(String(200), nullable=True)
    
    # Composition and claims
    composition = Column(Text, nullable=True)
    revendication = Column(Text, nullable=True)
    denomination_classe = Column(String(100), nullable=True)
    formulations = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    substances = relationship("ProductSubstance", back_populates="product", cascade="all, delete-orphan", lazy="select")
    usages = relationship("Usage", back_populates="product", cascade="all, delete-orphan", lazy="select")
    conditions_emploi = relationship("ConditionEmploi", back_populates="product", cascade="all, delete-orphan", lazy="select")
    classifications_danger = relationship("ClassificationDanger", back_populates="product", cascade="all, delete-orphan", lazy="select")
    phrases_risque = relationship("PhraseRisque", back_populates="product", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Product(id={self.id}, numero_amm={self.numero_amm}, nom_produit={self.nom_produit})>"
    
    @property
    def is_authorized(self) -> bool:
        """Check if product is currently authorized"""
        return self.etat_autorisation == AuthorizationStatus.AUTORISE
    
    @property
    def active_substances(self) -> list:
        """Get list of active substances"""
        return [ps.substance for ps in self.substances if ps.substance.etat_autorisation == AuthorizationStatus.AUTORISE]


class SubstanceActive(Base):
    """Active substances registry"""
    
    __tablename__ = "substances_actives"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Substance identification
    nom_substance = Column(String(200), nullable=False, index=True)
    numero_cas = Column(String(20), nullable=True, index=True)
    etat_autorisation = Column(SQLEnum(AuthorizationStatus), nullable=False, index=True)
    variants = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    products = relationship("ProductSubstance", back_populates="substance", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<SubstanceActive(id={self.id}, nom_substance={self.nom_substance})>"
    
    @property
    def is_authorized(self) -> bool:
        """Check if substance is currently authorized"""
        return self.etat_autorisation == AuthorizationStatus.AUTORISE


class ProductSubstance(Base):
    """Product-substance relationships with concentrations"""
    
    __tablename__ = "product_substances"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    substance_id = Column(Integer, ForeignKey("substances_actives.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Concentration details
    concentration_value = Column(Numeric(10, 3), nullable=True)
    concentration_unit = Column(String(10), nullable=True)
    fonction = Column(String(50), nullable=True)  # Insecticide, Fongicide, etc.
    
    # Relationships
    product = relationship("Product", back_populates="substances", lazy="select")
    substance = relationship("SubstanceActive", back_populates="products", lazy="select")
    
    def __repr__(self):
        return f"<ProductSubstance(product_id={self.product_id}, substance_id={self.substance_id})>"


class Usage(Base):
    """Usage authorizations (applications, crops, dosages)"""
    
    __tablename__ = "usages"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Usage identification
    identifiant_usage = Column(String(50), nullable=True, index=True)
    identifiant_usage_lib_court = Column(String(200), nullable=True)
    
    # Crop information
    type_culture_libelle = Column(String(100), nullable=True, index=True)
    culture_commentaire = Column(Text, nullable=True)
    
    # Growth stages (BBCH scale)
    stade_cultural_min_bbch = Column(Integer, nullable=True)
    stade_cultural_max_bbch = Column(Integer, nullable=True)
    
    # Dosage information
    dose_min_par_apport = Column(Numeric(10, 3), nullable=True)
    dose_max_par_apport = Column(Numeric(10, 3), nullable=True)
    dose_retenue = Column(Numeric(10, 3), nullable=True)
    dose_unite = Column(String(20), nullable=True)
    
    # Application limits
    nombre_max_application = Column(Integer, nullable=True)
    delai_avant_recolte_jour = Column(Integer, nullable=True)  # Pre-harvest interval in days
    delai_avant_recolte_bbch = Column(Integer, nullable=True)
    intervalle_minimum_applications_jour = Column(Integer, nullable=True)
    
    # Authorization status
    etat_usage = Column(SQLEnum(UsageStatus), default=UsageStatus.AUTORISE, nullable=False, index=True)
    
    # Dates
    date_decision = Column(DateTime, nullable=True)
    date_fin_distribution = Column(DateTime, nullable=True)
    date_fin_utilisation = Column(DateTime, nullable=True)
    
    # Application seasons
    saison_application_min = Column(String(50), nullable=True)
    saison_application_max = Column(String(50), nullable=True)
    saison_application_min_commentaire = Column(Text, nullable=True)
    saison_application_max_commentaire = Column(Text, nullable=True)
    
    # Usage conditions
    condition_emploi = Column(Text, nullable=True)
    mentions_autorisees = Column(Text, nullable=True)
    restrictions_usage = Column(Text, nullable=True)
    restrictions_usage_libelle = Column(Text, nullable=True)
    
    # Buffer zones (ZNT - Zones de Non Traitement)
    znt_aquatique_m = Column(Integer, nullable=True)  # Aquatic buffer zone in meters
    znt_arthropodes_non_cibles_m = Column(Integer, nullable=True)  # Non-target arthropods buffer zone
    znt_plantes_non_cibles_m = Column(Integer, nullable=True)  # Non-target plants buffer zone
    
    # Relationships
    product = relationship("Product", back_populates="usages", lazy="select")
    
    def __repr__(self):
        return f"<Usage(id={self.id}, product_id={self.product_id}, type_culture={self.type_culture_libelle})>"
    
    @property
    def is_authorized(self) -> bool:
        """Check if usage is currently authorized"""
        return self.etat_usage == UsageStatus.AUTORISE
    
    @property
    def has_buffer_zones(self) -> bool:
        """Check if usage has buffer zone requirements"""
        return any([
            self.znt_aquatique_m,
            self.znt_arthropodes_non_cibles_m,
            self.znt_plantes_non_cibles_m
        ])


class ConditionEmploi(Base):
    """Safety conditions and requirements"""
    
    __tablename__ = "conditions_emploi"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Condition details
    categorie_condition = Column(String(100), nullable=True, index=True)
    condition_emploi_libelle = Column(Text, nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="conditions_emploi", lazy="select")
    
    def __repr__(self):
        return f"<ConditionEmploi(id={self.id}, product_id={self.product_id}, categorie={self.categorie_condition})>"


class ClassificationDanger(Base):
    """Hazard classifications (GHS)"""
    
    __tablename__ = "classifications_danger"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Classification details
    libelle_court = Column(String(20), nullable=False, index=True)
    libelle_long = Column(Text, nullable=False)
    type_classification = Column(String(50), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="classifications_danger", lazy="select")
    
    def __repr__(self):
        return f"<ClassificationDanger(id={self.id}, product_id={self.product_id}, libelle={self.libelle_court})>"


class PhraseRisque(Base):
    """Risk phrases (H-codes, P-codes)"""
    
    __tablename__ = "phrases_risque"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Risk phrase details
    code_phrase = Column(String(10), nullable=False, index=True)
    libelle_court_phrase = Column(Text, nullable=True)
    libelle_long_phrase = Column(Text, nullable=True)
    type_phrase = Column(String(10), nullable=True, index=True)  # H, P, EUH
    
    # Relationships
    product = relationship("Product", back_populates="phrases_risque", lazy="select")
    
    def __repr__(self):
        return f"<PhraseRisque(id={self.id}, product_id={self.product_id}, code={self.code_phrase})>"


class PermisImportation(Base):
    """Import permits and foreign equivalencies"""
    
    __tablename__ = "permis_importation"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Product information
    nom_produit = Column(String(200), nullable=False)
    numero_permis = Column(String(20), unique=True, nullable=False, index=True)
    etat_autorisation = Column(SQLEnum(AuthorizationStatus), nullable=True)
    detenteur_pcp = Column(String(200), nullable=True)
    
    # Reference product (French)
    produit_reference_francais = Column(String(200), nullable=True, index=True)
    numero_amm_reference_francais = Column(String(20), nullable=True, index=True)
    
    # Imported product
    nom_produit_importe = Column(String(200), nullable=True)
    numero_amm_produit_importe = Column(String(50), nullable=True)
    etat_membre_origine = Column(String(50), nullable=True)
    
    # Additional information
    mentions_etiquetage = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<PermisImportation(id={self.id}, numero_permis={self.numero_permis})>"


class AuditLog(Base):
    """Audit trail for product database changes"""
    
    __tablename__ = "audit_log"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Audit information
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    operation = Column(String(10), nullable=False, index=True)  # INSERT, UPDATE, DELETE
    
    # Change data
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    changed_by = Column(String(100), nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, table={self.table_name}, operation={self.operation})>"
