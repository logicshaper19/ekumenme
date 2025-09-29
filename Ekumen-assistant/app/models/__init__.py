# Model imports for proper relationship resolution
from .user import User, UserSession, UserActivity
from .farm import Farm, Parcel, CropRotation
from .organization import Organization, OrganizationMembership, OrganizationFarmAccess, KnowledgeBaseEntry
from .conversation import Conversation, Message
from .intervention import VoiceJournalEntry, ProductUsage
from .disease import Disease
from .pest import Pest
from .ephy import (
    Produit, SubstanceActive, ProduitSubstance,
    UsageProduit, Titulaire, Formulation, Fonction,
    PhraseRisque, ProduitPhraseRisque, ProduitClassification,
    ConditionEmploi, PermisImportation,
    ProductType, CommercialType, GammeUsage, EtatAutorisation
)

__all__ = [
    "User", "UserSession", "UserActivity",
    "Farm", "Parcel", "CropRotation",
    "Organization", "OrganizationMembership", "OrganizationFarmAccess", "KnowledgeBaseEntry",
    "Conversation", "Message",
    "VoiceJournalEntry", "ProductUsage",
    "Disease", "Pest",
    "Produit", "SubstanceActive", "ProduitSubstance", "UsageProduit",
    "Titulaire", "Formulation", "Fonction",
    "PhraseRisque", "ProduitPhraseRisque", "ProduitClassification",
    "ConditionEmploi", "PermisImportation",
    "ProductType", "CommercialType", "GammeUsage", "EtatAutorisation"
]
