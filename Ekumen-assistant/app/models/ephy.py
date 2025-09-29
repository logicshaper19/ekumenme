"""
EPHY database models for Ekumen-assistant
Mirrors the Ekumenbackend EPHY models to access the same database
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    ForeignKey, DECIMAL, Date, Enum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum


class ProductType(enum.Enum):
    """Product types enum."""
    PPP = "PPP"  # Plant Protection Products
    MFSC = "MFSC"  # Fertilizers
    MELANGE = "MELANGE"  # Mixture
    ADJUVANT = "ADJUVANT"  # Adjuvant
    PRODUIT_MIXTE = "PRODUIT_MIXTE"  # Mixed Product


class CommercialType(enum.Enum):
    """Commercial types enum."""
    PRODUIT_REFERENCE = "Produit de référence"
    PRODUIT_REVENTE = "Produit de revente"
    DEUXIEME_GAMME = "Deuxième gamme"


class GammeUsage(enum.Enum):
    """Usage ranges enum."""
    PROFESSIONNEL = "Professionnel"
    AMATEUR = "Amateur / emploi autorisé dans les jardins"


class EtatAutorisation(enum.Enum):
    """Authorization states enum."""
    AUTORISE = "AUTORISE"
    RETIRE = "RETIRE"
    AUTORISE_FR = "Autorisé"
    RETRAIT_FR = "Retrait"


class SubstanceActive(Base):
    """Active substances table."""
    __tablename__ = "substances_actives"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_substance = Column(String(300), nullable=False)
    numero_cas = Column(String(50))
    etat_autorisation = Column(String(50))
    variants = Column(Text)  # Array of variant names as text
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit_substances = relationship("ProduitSubstance", back_populates="substance")


class Titulaire(Base):
    """Companies/holders table."""
    __tablename__ = "titulaires"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(300), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    produits = relationship("Produit", back_populates="titulaire")


class Produit(Base):
    """Main products table."""
    __tablename__ = "produits"
    
    numero_amm = Column(String(20), primary_key=True)
    nom_produit = Column(String(300), nullable=False)
    type_produit = Column(Enum(ProductType))
    seconds_noms_commerciaux = Column(Text)  # Pipe-separated alternative names
    titulaire_id = Column(Integer, ForeignKey("titulaires.id"))
    type_commercial = Column(Enum(CommercialType))
    gamme_usage = Column(Enum(GammeUsage))
    mentions_autorisees = Column(Text)
    restrictions_usage = Column(Text)
    restrictions_usage_libelle = Column(Text)
    etat_autorisation = Column(Enum(EtatAutorisation))
    date_retrait_produit = Column(Date)
    date_premiere_autorisation = Column(Date)
    numero_amm_reference = Column(Text)  # Use Text for unlimited length AMM references
    nom_produit_reference = Column(Text)  # Reference product name (unlimited length)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    titulaire = relationship("Titulaire", back_populates="produits")
    produit_substances = relationship("ProduitSubstance", back_populates="produit")
    produit_fonctions = relationship("ProduitFonction", back_populates="produit")
    produit_formulations = relationship("ProduitFormulation", back_populates="produit")
    usages = relationship("UsageProduit", back_populates="produit")
    produit_phrases_risque = relationship("ProduitPhraseRisque", back_populates="produit")
    produit_classifications = relationship("ProduitClassification", back_populates="produit")
    conditions_emploi = relationship("ConditionEmploi", back_populates="produit")


class Formulation(Base):
    """Product formulations reference table."""
    __tablename__ = "formulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    libelle = Column(String(200), nullable=False, unique=True)

    # Relationships
    produit_formulations = relationship("ProduitFormulation", back_populates="formulation")


class Fonction(Base):
    """Product functions reference table."""
    __tablename__ = "fonctions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    libelle = Column(String(200), nullable=False, unique=True)

    # Relationships
    produit_fonctions = relationship("ProduitFonction", back_populates="fonction")


class ProduitSubstance(Base):
    """Many-to-many relationship between products and active substances."""
    __tablename__ = "produit_substances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    substance_id = Column(Integer, ForeignKey("substances_actives.id"))
    concentration = Column(DECIMAL(10, 4))
    unite_concentration = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_substances")
    substance = relationship("SubstanceActive", back_populates="produit_substances")


class ProduitFonction(Base):
    """Many-to-many relationship between products and functions."""
    __tablename__ = "produit_fonctions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    fonction_id = Column(Integer, ForeignKey("fonctions.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_fonctions")
    fonction = relationship("Fonction", back_populates="produit_fonctions")


class ProduitFormulation(Base):
    """Many-to-many relationship between products and formulations."""
    __tablename__ = "produit_formulations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    formulation_id = Column(Integer, ForeignKey("formulations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_formulations")
    formulation = relationship("Formulation", back_populates="produit_formulations")





class UsageProduit(Base):
    """Product usage conditions table."""
    __tablename__ = "usages_produits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    identifiant_usage = Column(String(100))
    identifiant_usage_lib_court = Column(String(200))
    type_culture_libelle = Column(String(200))  # Direct from CSV
    culture_commentaire = Column(Text)
    dose_min_par_apport = Column(DECIMAL(10, 4))
    dose_min_par_apport_unite = Column(String(20))
    dose_max_par_apport = Column(DECIMAL(10, 4))
    dose_max_par_apport_unite = Column(String(20))
    dose_retenue = Column(DECIMAL(10, 4))
    dose_retenue_unite = Column(String(20))
    stade_cultural_min_bbch = Column(Integer)
    stade_cultural_max_bbch = Column(Integer)
    etat_usage = Column(String(50))  # "Autorisé", "Retrait", etc.
    date_decision = Column(Date)
    saison_application_min = Column(String(50))
    saison_application_max = Column(String(50))
    saison_application_min_commentaire = Column(Text)
    saison_application_max_commentaire = Column(Text)
    delai_avant_recolte_jour = Column(Integer)
    delai_avant_recolte_bbch = Column(Integer)
    nombre_max_application = Column(Integer)
    date_fin_distribution = Column(Date)
    date_fin_utilisation = Column(Date)
    condition_emploi = Column(Text)
    znt_aquatique_m = Column(DECIMAL(6, 2))
    znt_arthropodes_non_cibles_m = Column(DECIMAL(6, 2))
    znt_plantes_non_cibles_m = Column(DECIMAL(6, 2))
    mentions_autorisees = Column(Text)
    intervalle_minimum_entre_applications_jour = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    produit = relationship("Produit", back_populates="usages")


class PhraseRisque(Base):
    """Risk phrases table."""
    __tablename__ = "phrases_risque"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code_phrase = Column(String(20), nullable=False)
    libelle_phrase = Column(Text, nullable=False)
    type_phrase = Column(String(10))  # H, P, EUH
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit_phrases_risque = relationship("ProduitPhraseRisque", back_populates="phrase_risque")


class ProduitPhraseRisque(Base):
    """Many-to-many relationship between products and risk phrases."""
    __tablename__ = "produit_phrases_risque"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    phrase_risque_id = Column(Integer, ForeignKey("phrases_risque.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_phrases_risque")
    phrase_risque = relationship("PhraseRisque", back_populates="produit_phrases_risque")





class ProduitClassification(Base):
    """Product classifications (from file 4)."""
    __tablename__ = "produit_classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    nom_produit = Column(String(300))
    libelle_court = Column(String(50))
    libelle_long = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    produit = relationship("Produit", back_populates="produit_classifications")


class ConditionEmploi(Base):
    """Employment conditions (from file 5)."""
    __tablename__ = "conditions_emploi"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_produit = Column(String(10))  # PPP, MFSC
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    nom_produit = Column(String(300))
    categorie_condition_emploi = Column(String(200))
    condition_emploi_libelle = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    produit = relationship("Produit", back_populates="conditions_emploi")


class PermisImportation(Base):
    """Import permits (from file 3)."""
    __tablename__ = "permis_importation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_produit = Column(String(300))
    numero_permis = Column(String(20))
    etat_autorisation = Column(String(50))
    detenteur_pcp = Column(String(300))
    produit_reference_francais = Column(String(300))
    numero_amm_reference_francais = Column(String(20))
    nom_produit_importe = Column(String(300))
    numero_amm_produit_importe = Column(String(50))
    etat_membre_origine = Column(String(100))
    mentions_etiquetage = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
