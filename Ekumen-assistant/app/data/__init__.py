"""
Agricultural data package.
Contains databases for diseases, pests, and nutrient deficiencies.
"""

from .french_crop_diseases import disease_db, FrenchCropDiseaseDatabase
from .french_crop_pests import pest_db, FrenchCropPestDatabase
from .french_nutrient_deficiencies import deficiency_db, FrenchNutrientDeficiencyDatabase

__all__ = [
    "disease_db",
    "FrenchCropDiseaseDatabase",
    "pest_db", 
    "FrenchCropPestDatabase",
    "deficiency_db",
    "FrenchNutrientDeficiencyDatabase"
]
