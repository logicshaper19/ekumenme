"""
Official EPPO Codes for French Agricultural Crops

EPPO (European and Mediterranean Plant Protection Organization) codes
provide international standardization for crop identification.

Reference: https://gd.eppo.int/

This module provides:
- Centralized crop EPPO code mapping
- Validation functions for crop names
- Bidirectional lookup (name ↔ EPPO code)
"""

from typing import Dict, Optional, List
from enum import Enum


# Official EPPO codes for major French crops
CROP_EPPO_CODES: Dict[str, str] = {
    # Cereals (Céréales)
    "blé": "TRZAX",           # Triticum aestivum (Wheat)
    "orge": "HORVX",          # Hordeum vulgare (Barley)
    "maïs": "ZEAMX",          # Zea mays (Corn/Maize)
    "seigle": "SECCE",        # Secale cereale (Rye)
    "avoine": "AVESA",        # Avena sativa (Oat)
    "triticale": "TTLSP",     # Triticosecale (Triticale)
    
    # Oilseeds (Oléagineux)
    "colza": "BRSNN",         # Brassica napus (Rapeseed/Canola)
    "tournesol": "HELAN",     # Helianthus annuus (Sunflower)
    "soja": "GLXMA",          # Glycine max (Soybean)
    "lin": "LIUUT",           # Linum usitatissimum (Flax)
    
    # Root crops (Cultures racines)
    "betterave": "BEAVA",     # Beta vulgaris (Sugar beet)
    "pomme de terre": "SOLTU", # Solanum tuberosum (Potato)
    "carotte": "DAUCA",       # Daucus carota (Carrot)
    
    # Legumes (Légumineuses)
    "pois": "PIBSX",          # Pisum sativum (Pea)
    "féverole": "VICFX",      # Vicia faba (Faba bean)
    "luzerne": "MEDSA",       # Medicago sativa (Alfalfa)
    "haricot": "PHSVX",       # Phaseolus vulgaris (Bean)
    
    # Fruits & Vines (Fruits et vignes)
    "vigne": "VITVI",         # Vitis vinifera (Grapevine)
    "pommier": "MABSD",       # Malus domestica (Apple)
    "poirier": "PYUCO",       # Pyrus communis (Pear)
    
    # Forages (Fourrages)
    "prairie": "POAPR",       # Poa pratensis (Meadow grass)
    "ray-grass": "LOLSS",     # Lolium species (Ryegrass)
    
    # Vegetables (Légumes)
    "tomate": "LYPES",        # Solanum lycopersicum (Tomato)
    "salade": "LACSA",        # Lactuca sativa (Lettuce)
}


# Reverse mapping: EPPO code → French name
EPPO_TO_CROP: Dict[str, str] = {v: k for k, v in CROP_EPPO_CODES.items()}


# Crop name aliases (alternative spellings/names)
CROP_ALIASES: Dict[str, str] = {
    "ble": "blé",
    "mais": "maïs",
    "pomme_de_terre": "pomme de terre",
    "pommes de terre": "pomme de terre",
    "feverole": "féverole",
    "wheat": "blé",
    "corn": "maïs",
    "barley": "orge",
    "rapeseed": "colza",
    "canola": "colza",
    "sunflower": "tournesol",
    "potato": "pomme de terre",
    "grapevine": "vigne",
}


class CropCategory(str, Enum):
    """Crop categories for classification"""
    CEREAL = "céréale"
    OILSEED = "oléagineux"
    ROOT_CROP = "culture_racine"
    LEGUME = "légumineuse"
    FRUIT = "fruit"
    VEGETABLE = "légume"
    FORAGE = "fourrage"


# Crop category mapping
CROP_CATEGORIES: Dict[str, CropCategory] = {
    "blé": CropCategory.CEREAL,
    "orge": CropCategory.CEREAL,
    "maïs": CropCategory.CEREAL,
    "seigle": CropCategory.CEREAL,
    "avoine": CropCategory.CEREAL,
    "triticale": CropCategory.CEREAL,
    "colza": CropCategory.OILSEED,
    "tournesol": CropCategory.OILSEED,
    "soja": CropCategory.OILSEED,
    "lin": CropCategory.OILSEED,
    "betterave": CropCategory.ROOT_CROP,
    "pomme de terre": CropCategory.ROOT_CROP,
    "carotte": CropCategory.ROOT_CROP,
    "pois": CropCategory.LEGUME,
    "féverole": CropCategory.LEGUME,
    "luzerne": CropCategory.LEGUME,
    "haricot": CropCategory.LEGUME,
    "vigne": CropCategory.FRUIT,
    "pommier": CropCategory.FRUIT,
    "poirier": CropCategory.FRUIT,
    "prairie": CropCategory.FORAGE,
    "ray-grass": CropCategory.FORAGE,
    "tomate": CropCategory.VEGETABLE,
    "salade": CropCategory.VEGETABLE,
}


def normalize_crop_name(crop_name: str) -> str:
    """
    Normalize crop name to standard form.
    
    Handles:
    - Case insensitivity
    - Aliases (e.g., "ble" → "blé")
    - Whitespace trimming
    
    Args:
        crop_name: Raw crop name input
        
    Returns:
        Normalized crop name
        
    Raises:
        ValueError: If crop name is invalid
    """
    if not crop_name:
        raise ValueError("Crop name cannot be empty")
    
    # Normalize: lowercase, strip whitespace
    normalized = crop_name.lower().strip()
    
    # Check aliases
    if normalized in CROP_ALIASES:
        normalized = CROP_ALIASES[normalized]
    
    return normalized


def get_eppo_code(crop_name: str) -> Optional[str]:
    """
    Get EPPO code for a crop name.
    
    Args:
        crop_name: Crop name (French or alias)
        
    Returns:
        EPPO code (e.g., "TRZAX") or None if not found
        
    Example:
        >>> get_eppo_code("blé")
        'TRZAX'
        >>> get_eppo_code("wheat")
        'TRZAX'
    """
    try:
        normalized = normalize_crop_name(crop_name)
        return CROP_EPPO_CODES.get(normalized)
    except ValueError:
        return None


def get_crop_name(eppo_code: str) -> Optional[str]:
    """
    Get French crop name from EPPO code.
    
    Args:
        eppo_code: EPPO code (e.g., "TRZAX")
        
    Returns:
        French crop name or None if not found
        
    Example:
        >>> get_crop_name("TRZAX")
        'blé'
    """
    if not eppo_code:
        return None
    return EPPO_TO_CROP.get(eppo_code.upper())


def validate_crop(crop_name: str) -> bool:
    """
    Check if crop name is recognized.
    
    Args:
        crop_name: Crop name to validate
        
    Returns:
        True if crop is recognized, False otherwise
        
    Example:
        >>> validate_crop("blé")
        True
        >>> validate_crop("unknown_crop")
        False
    """
    try:
        normalized = normalize_crop_name(crop_name)
        return normalized in CROP_EPPO_CODES
    except ValueError:
        return False


def get_crop_category(crop_name: str) -> Optional[CropCategory]:
    """
    Get category for a crop.
    
    Args:
        crop_name: Crop name
        
    Returns:
        CropCategory or None if not found
    """
    try:
        normalized = normalize_crop_name(crop_name)
        return CROP_CATEGORIES.get(normalized)
    except ValueError:
        return None


def get_all_crops() -> List[str]:
    """
    Get list of all supported crop names.
    
    Returns:
        List of French crop names
    """
    return list(CROP_EPPO_CODES.keys())


def get_crops_by_category(category: CropCategory) -> List[str]:
    """
    Get all crops in a specific category.
    
    Args:
        category: Crop category
        
    Returns:
        List of crop names in that category
    """
    return [
        crop for crop, cat in CROP_CATEGORIES.items()
        if cat == category
    ]


def validate_crop_strict(crop_name: str) -> str:
    """
    Validate crop name and return normalized form.
    
    Args:
        crop_name: Crop name to validate
        
    Returns:
        Normalized crop name
        
    Raises:
        ValueError: If crop is not recognized
        
    Example:
        >>> validate_crop_strict("ble")
        'blé'
        >>> validate_crop_strict("invalid")
        ValueError: Unknown crop: 'invalid'. Supported crops: blé, maïs, ...
    """
    normalized = normalize_crop_name(crop_name)
    
    if normalized not in CROP_EPPO_CODES:
        supported = ", ".join(sorted(CROP_EPPO_CODES.keys())[:10])
        raise ValueError(
            f"Unknown crop: '{crop_name}'. "
            f"Supported crops include: {supported}..."
        )
    
    return normalized


# Export main functions
__all__ = [
    "CROP_EPPO_CODES",
    "EPPO_TO_CROP",
    "CROP_ALIASES",
    "CROP_CATEGORIES",
    "CropCategory",
    "normalize_crop_name",
    "get_eppo_code",
    "get_crop_name",
    "validate_crop",
    "validate_crop_strict",
    "get_crop_category",
    "get_all_crops",
    "get_crops_by_category",
]

