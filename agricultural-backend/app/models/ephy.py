"""
EPHY database models.
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
    numero_amm_reference = Column(String(20))
    nom_produit_reference = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referencing foreign key
    __table_args__ = (
        ForeignKey(["numero_amm_reference"], ["produits.numero_amm"]),
    )
    
    # Relationships
    titulaire = relationship("Titulaire", back_populates="produits")
    produit_substances = relationship("ProduitSubstance", back_populates="produit")
    produit_fonctions = relationship("ProduitFonction", back_populates="produit")
    produit_formulations = relationship("ProduitFormulation", back_populates="produit")
    compositions_fertilisants = relationship("CompositionFertilisant", back_populates="produit")
    produit_phrases_risque = relationship("ProduitPhraseRisque", back_populates="produit")
    produit_classifications = relationship("ProduitClassification", back_populates="produit")
    conditions_emploi = relationship("ConditionEmploi", back_populates="produit")
    usages_produits = relationship("UsageProduit", back_populates="produit")


class ProduitSubstance(Base):
    """Product-substance active relationships (many-to-many)."""
    __tablename__ = "produit_substances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    substance_id = Column(Integer, ForeignKey("substances_actives.id"))
    concentration = Column(DECIMAL(10, 4))
    unite_concentration = Column(String(20))  # g/L, g/kg, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_substances")
    substance = relationship("SubstanceActive", back_populates="produit_substances")


class ProduitFonction(Base):
    """Product-function relationships (many-to-many)."""
    __tablename__ = "produit_fonctions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    fonction_id = Column(Integer, ForeignKey("fonctions.id"))
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_fonctions")
    fonction = relationship("Fonction", back_populates="produit_fonctions")


class ProduitFormulation(Base):
    """Product-formulation relationships (many-to-many)."""
    __tablename__ = "produit_formulations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    formulation_id = Column(Integer, ForeignKey("formulations.id"))
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_formulations")
    formulation = relationship("Formulation", back_populates="produit_formulations")


class CompositionFertilisant(Base):
    """Fertilizer composition details (for MFSC products)."""
    __tablename__ = "compositions_fertilisants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    element = Column(String(100), nullable=False)  # N, P2O5, K2O, etc.
    valeur_min = Column(DECIMAL(10, 4))
    valeur_max = Column(DECIMAL(10, 4))
    unite = Column(String(20))
    type_element = Column(String(50))  # 'principal', 'secondaire', 'oligo-element'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit = relationship("Produit", back_populates="compositions_fertilisants")


class AutorisationImport(Base):
    """Import authorization table (for imported products)."""
    __tablename__ = "autorisations_import"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_produit = Column(String(300), nullable=False)
    numero_permis = Column(String(20), nullable=False)
    etat_autorisation = Column(Enum(EtatAutorisation))
    detenteur_pcp = Column(String(300))
    produit_reference_francais = Column(String(300))
    numero_amm_reference_francais = Column(String(20), ForeignKey("produits.numero_amm"))
    nom_produit_importe = Column(String(300))
    numero_amm_produit_importe = Column(String(50))
    etat_membre_origine = Column(String(100))
    mentions_etiquetage = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit_reference = relationship("Produit", foreign_keys=[numero_amm_reference_francais])


class PhraseRisque(Base):
    """Risk phrases and hazard statements table."""
    __tablename__ = "phrases_risque"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False)  # H226, H302, etc.
    libelle_court = Column(String(100))
    libelle_long = Column(Text)
    type_phrase = Column(String(50))  # 'H' for hazard, 'P' for precautionary
    
    # Relationships
    produit_phrases_risque = relationship("ProduitPhraseRisque", back_populates="phrase")


class ProduitPhraseRisque(Base):
    """Product risk phrases relationship table."""
    __tablename__ = "produit_phrases_risque"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    phrase_id = Column(Integer, ForeignKey("phrases_risque.id"))
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_phrases_risque")
    phrase = relationship("PhraseRisque", back_populates="produit_phrases_risque")


class CategorieClassification(Base):
    """Classification categories table."""
    __tablename__ = "categories_classification"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True)  # C4, C1, TCC1, etc.
    libelle_court = Column(String(100))
    libelle_long = Column(Text)
    
    # Relationships
    produit_classifications = relationship("ProduitClassification", back_populates="categorie")


class ProduitClassification(Base):
    """Product classifications relationship table."""
    __tablename__ = "produit_classifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    categorie_id = Column(Integer, ForeignKey("categories_classification.id"))
    
    # Relationships
    produit = relationship("Produit", back_populates="produit_classifications")
    categorie = relationship("CategorieClassification", back_populates="produit_classifications")


class CategorieConditionEmploi(Base):
    """Usage conditions categories table."""
    __tablename__ = "categories_conditions_emploi"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    libelle = Column(String(200), nullable=False, unique=True)  # "Protection de l'opérateur", etc.
    
    # Relationships
    conditions_emploi = relationship("ConditionEmploi", back_populates="categorie")


class ConditionEmploi(Base):
    """Usage conditions table."""
    __tablename__ = "conditions_emploi"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    categorie_id = Column(Integer, ForeignKey("categories_conditions_emploi.id"))
    condition_libelle = Column(Text, nullable=False)
    
    # Relationships
    produit = relationship("Produit", back_populates="conditions_emploi")
    categorie = relationship("CategorieConditionEmploi", back_populates="conditions_emploi")


class TypeCulture(Base):
    """Crop types for usage table."""
    __tablename__ = "types_culture"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    libelle = Column(String(200), nullable=False, unique=True)
    
    # Relationships
    usages_produits = relationship("UsageProduit", back_populates="type_culture")


class UsageProduit(Base):
    """Product usages (detailed application information) table."""
    __tablename__ = "usages_produits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_amm = Column(String(20), ForeignKey("produits.numero_amm"))
    identifiant_usage = Column(String(100))
    identifiant_usage_lib_court = Column(String(200))
    type_culture_id = Column(Integer, ForeignKey("types_culture.id"))
    culture_commentaire = Column(Text)
    dose_min_par_apport = Column(DECIMAL(10, 4))
    dose_min_unite = Column(String(20))
    dose_max_par_apport = Column(DECIMAL(10, 4))
    dose_max_unite = Column(String(20))
    dose_retenue = Column(DECIMAL(10, 4))
    dose_retenue_unite = Column(String(20))
    stade_cultural_min_bbch = Column(Integer)
    stade_cultural_max_bbch = Column(Integer)
    etat_usage = Column(Enum(EtatAutorisation))
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
    mentions_autorisees_usage = Column(Text)
    intervalle_minimum_entre_applications_jour = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produit = relationship("Produit", back_populates="usages_produits")
    type_culture = relationship("TypeCulture", back_populates="usages_produits")
