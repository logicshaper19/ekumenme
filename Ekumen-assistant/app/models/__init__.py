# Model imports for proper relationship resolution
from .user import User, UserSession, UserActivity
from .organization import Organization, OrganizationMembership, OrganizationFarmAccess, KnowledgeBaseEntry
from .conversation import Conversation, Message
from .feedback import ResponseFeedback, FeedbackType, FeedbackCategory
from .intervention import VoiceJournalEntry, ProductUsage, InterventionHistory
from .crop import Crop
from .disease import Disease
from .pest import Pest
from .ephy import (
    Produit, SubstanceActive, ProduitSubstance,
    UsageProduit, Titulaire, Formulation, Fonction,
    PhraseRisque, ProduitPhraseRisque, ProduitClassification,
    ConditionEmploi, PermisImportation,
    ProductType, CommercialType, GammeUsage, EtatAutorisation
)
from .mesparcelles import Exploitation, Parcelle, Intervention, Intrant

__all__ = [
    "User", "UserSession", "UserActivity",
    "Organization", "OrganizationMembership", "OrganizationFarmAccess", "KnowledgeBaseEntry",
    "Conversation", "Message",
    "ResponseFeedback", "FeedbackType", "FeedbackCategory",
    "VoiceJournalEntry", "ProductUsage", "InterventionHistory",
    "Crop", "Disease", "Pest",
    "Produit", "SubstanceActive", "ProduitSubstance", "UsageProduit",
    "Titulaire", "Formulation", "Fonction",
    "PhraseRisque", "ProduitPhraseRisque", "ProduitClassification",
    "ConditionEmploi", "PermisImportation",
    "ProductType", "CommercialType", "GammeUsage", "EtatAutorisation",
    "Exploitation", "Parcelle", "Intervention", "Intrant"
]
