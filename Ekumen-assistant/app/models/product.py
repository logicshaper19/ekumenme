"""
Product models for EPHY database integration.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class ProductType(enum.Enum):
    """Product type enumeration"""
    FONGICIDE = "fongicide"
    INSECTICIDE = "insecticide"
    HERBICIDE = "herbicide"
    ACARICIDE = "acaricide"
    NEMATICIDE = "nematicide"
    MOLLUSCICIDE = "molluscicide"
    RODENTICIDE = "rodenticide"
    AUTRE = "autre"


class AuthorizationStatus(enum.Enum):
    """Authorization status enumeration"""
    AUTORISE = "autorise"
    RETIRE = "retire"
    SUSPENDU = "suspendu"
    EXPIRE = "expire"


class UsageStatus(enum.Enum):
    """Usage status enumeration"""
    AUTORISE = "autorise"
    RETIRE = "retire"
    SUSPENDU = "suspendu"


class Product(Base):
    """EPHY Product model"""
    __tablename__ = "products"
    __table_args__ = {"schema": "regulatory"}

    id = Column(Integer, primary_key=True, index=True)
    amm = Column(String(20), unique=True, index=True, nullable=False)
    nom_produit = Column(String(255), nullable=False)
    titulaire = Column(String(255))
    distributeur = Column(String(255))
    type_produit = Column(Enum(ProductType))
    statut_autorisation = Column(Enum(AuthorizationStatus))
    date_autorisation = Column(DateTime)
    date_retrait = Column(DateTime)
    date_expiration = Column(DateTime)
    
    # Relationships
    substances = relationship("ProductSubstance", back_populates="product")
    usages = relationship("Usage", back_populates="product")
    conditions_emploi = relationship("ConditionEmploi", back_populates="product")
    classifications = relationship("ClassificationDanger", back_populates="product")
    phrases_risque = relationship("PhraseRisque", back_populates="product")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SubstanceActive(Base):
    """Active substance model"""
    __tablename__ = "substances_actives"
    __table_args__ = {"schema": "regulatory"}

    id = Column(Integer, primary_key=True, index=True)
    code_substance = Column(String(20), unique=True, index=True)
    nom_substance = Column(String(255), nullable=False)
    nom_chimique = Column(Text)
    cas_number = Column(String(50))
    
    # Relationships
    products = relationship("ProductSubstance", back_populates="substance")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductSubstance(Base):
    """Product-Substance relationship"""
    __tablename__ = "product_substances"
    __table_args__ = {"schema": "regulatory"}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("regulatory.products.id"))
    substance_id = Column(Integer, ForeignKey("regulatory.substances_actives.id"))
    concentration = Column(Numeric(10, 4))
    unite_concentration = Column(String(20))
    
    # Relationships
    product = relationship("Product", back_populates="substances")
    substance = relationship("SubstanceActive", back_populates="products")


class Usage(Base):
    """Product usage model"""
    __tablename__ = "usages"
    __table_args__ = {"schema": "regulatory"}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("regulatory.products.id"))
    numero_usage = Column(String(20))
    culture = Column(String(255))
    cible = Column(String(255))
    dose_min = Column(Numeric(10, 4))
    dose_max = Column(Numeric(10, 4))
    unite_dose = Column(String(20))
    statut = Column(Enum(UsageStatus))
    
    # Relationships
    product = relationship("Product", back_populates="usages")

    created_at = Column(DateTime, default=datetime.utcnow)


class ConditionEmploi(Base):
    """Employment conditions model"""
    __tablename__ = "conditions_emploi"
    __table_args__ = {"schema": "regulatory"}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("regulatory.products.id"))
    type_condition = Column(String(100))
    description = Column(Text)
    valeur = Column(String(255))
    unite = Column(String(50))
    
    # Relationships
    product = relationship("Product", back_populates="conditions_emploi")


class ClassificationDanger(Base):
    """Danger classification model"""
    __tablename__ = "classifications_danger"
    __table_args__ = {"schema": "regulatory"}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("regulatory.products.id"))
    classe_danger = Column(String(100))
    categorie = Column(String(50))
    mention_danger = Column(String(10))  # H-code
    
    # Relationships
    product = relationship("Product", back_populates="classifications")


class PhraseRisque(Base):
    """Risk phrase model"""
    __tablename__ = "phrases_risque"
    __table_args__ = {"schema": "regulatory"}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("regulatory.products.id"))
    code_phrase = Column(String(10))  # P-code or R-code
    texte_phrase = Column(Text)
    type_phrase = Column(String(20))  # 'precaution' or 'risque'
    
    # Relationships
    product = relationship("Product", back_populates="phrases_risque")
