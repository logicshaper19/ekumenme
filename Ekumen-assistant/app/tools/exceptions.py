"""
Tool-specific exceptions with user-friendly messages

Provides granular error handling for agricultural tools with
actionable error messages in French for end users.
"""

from langchain.tools.base import ToolException


# ============================================================================
# Weather Tool Exceptions
# ============================================================================

class WeatherAPIError(ToolException):
    """Weather API is unavailable"""
    def __init__(self, details: str = ""):
        message = "La météo est temporairement indisponible. Veuillez réessayer dans quelques minutes."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class WeatherValidationError(ToolException):
    """Invalid weather parameters"""
    def __init__(self, details: str):
        super().__init__(
            f"Paramètres météo invalides: {details}. "
            f"Vérifiez le nom de la localisation et le nombre de jours (1-14)."
        )


class WeatherTimeoutError(ToolException):
    """Weather API timeout"""
    def __init__(self):
        super().__init__(
            "Le service météo met trop de temps à répondre. "
            "Le service est peut-être surchargé. Réessayez dans un moment."
        )


class WeatherLocationNotFoundError(ToolException):
    """Location not found"""
    def __init__(self, location: str):
        super().__init__(
            f"Localisation '{location}' non trouvée. "
            f"Vérifiez l'orthographe ou utilisez des coordonnées GPS."
        )


class WeatherDataError(ToolException):
    """Weather data missing or malformed"""
    def __init__(self, details: str):
        super().__init__(
            f"Données météo incomplètes: {details}. "
            f"Le service météo n'a pas retourné toutes les informations. Réessayez."
        )


# ============================================================================
# Regulatory Tool Exceptions
# ============================================================================

class RegulatoryAPIError(ToolException):
    """Regulatory database unavailable"""
    def __init__(self, details: str = ""):
        message = "La base de données réglementaire est temporairement indisponible. Veuillez réessayer plus tard."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class ProductNotFoundError(ToolException):
    """Product not found in database"""
    def __init__(self, product_name: str):
        super().__init__(
            f"Produit '{product_name}' non trouvé dans la base AMM. "
            f"Vérifiez l'orthographe ou utilisez le numéro AMM."
        )


class AMMValidationError(ToolException):
    """Invalid AMM code or search parameters"""
    def __init__(self, details: str):
        super().__init__(
            f"Paramètres de recherche AMM invalides: {details}"
        )


class AMMDataError(ToolException):
    """AMM database access error"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur d'accès à la base AMM: {details}. "
            f"Veuillez réessayer plus tard."
        )


class AMMLookupError(ToolException):
    """General AMM lookup error"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur lors de la recherche AMM: {details}"
        )


class ComplianceCheckError(ToolException):
    """Error checking compliance"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur lors de la vérification de conformité: {details}. "
            f"Veuillez vérifier les paramètres et réessayer."
        )


class ZNTCalculationError(ToolException):
    """Error calculating ZNT (no-treatment zones)"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur lors du calcul des ZNT: {details}. "
            f"Vérifiez les données de la parcelle et du produit."
        )


# ============================================================================
# Farm Data Tool Exceptions
# ============================================================================

class FarmDataAPIError(ToolException):
    """Farm data API unavailable"""
    def __init__(self, details: str = ""):
        message = "Les données de l'exploitation sont temporairement indisponibles. Veuillez réessayer."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class FarmNotFoundError(ToolException):
    """Farm not found"""
    def __init__(self, farm_id: str):
        super().__init__(
            f"Exploitation '{farm_id}' non trouvée. "
            f"Vérifiez l'identifiant ou le SIRET."
        )


class ParcelleNotFoundError(ToolException):
    """Parcelle not found"""
    def __init__(self, parcelle_id: str):
        super().__init__(
            f"Parcelle '{parcelle_id}' non trouvée. "
            f"Vérifiez l'identifiant de la parcelle."
        )


class InterventionNotFoundError(ToolException):
    """Intervention not found"""
    def __init__(self, intervention_id: str):
        super().__init__(
            f"Intervention '{intervention_id}' non trouvée. "
            f"Vérifiez l'identifiant de l'intervention."
        )


class InvalidSIRETError(ToolException):
    """Invalid SIRET number"""
    def __init__(self, siret: str):
        super().__init__(
            f"Numéro SIRET '{siret}' invalide. "
            f"Le SIRET doit contenir 14 chiffres."
        )


class MillesimeNotFoundError(ToolException):
    """Millesime (vintage year) not found"""
    def __init__(self, millesime: str):
        super().__init__(
            f"Millésime '{millesime}' non trouvé. "
            f"Vérifiez l'année de campagne."
        )


# ============================================================================
# EPPO Code Exceptions
# ============================================================================

class EPPOCodeNotFoundError(ToolException):
    """EPPO code not found in database"""
    def __init__(self, eppo_code: str):
        super().__init__(
            f"Code EPPO '{eppo_code}' non trouvé dans la base de données. "
            f"Vérifiez le code ou utilisez le nom commun de la culture."
        )


class InvalidEPPOCodeError(ToolException):
    """Invalid EPPO code format"""
    def __init__(self, eppo_code: str):
        super().__init__(
            f"Code EPPO '{eppo_code}' invalide. "
            f"Les codes EPPO doivent contenir 5 lettres (ex: TRZAX pour blé)."
        )


class EPPODatabaseError(ToolException):
    """EPPO database access error"""
    def __init__(self, details: str = ""):
        message = "La base de données EPPO est temporairement indisponible."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class CropNotMappedToEPPOError(ToolException):
    """Crop name not mapped to EPPO code"""
    def __init__(self, crop_name: str):
        super().__init__(
            f"La culture '{crop_name}' n'est pas encore associée à un code EPPO. "
            f"Contactez le support pour ajouter cette culture."
        )


# ============================================================================
# BBCH Stage Exceptions
# ============================================================================

class BBCHStageNotFoundError(ToolException):
    """BBCH stage not found for crop"""
    def __init__(self, crop: str, bbch_stage: int):
        super().__init__(
            f"Stade BBCH {bbch_stage} non trouvé pour la culture '{crop}'. "
            f"Vérifiez le stade (0-99) et la culture."
        )


class InvalidBBCHStageError(ToolException):
    """Invalid BBCH stage number"""
    def __init__(self, bbch_stage: int):
        super().__init__(
            f"Stade BBCH {bbch_stage} invalide. "
            f"Les stades BBCH doivent être entre 0 et 99."
        )


class BBCHDataMissingError(ToolException):
    """BBCH data not available for crop"""
    def __init__(self, crop: str):
        super().__init__(
            f"Données BBCH non disponibles pour '{crop}'. "
            f"Cette culture n'a pas encore de stades BBCH définis."
        )


class ZadoksStageNotFoundError(ToolException):
    """Zadoks stage not found for cereal"""
    def __init__(self, crop: str, zadoks_stage: int):
        super().__init__(
            f"Stade Zadoks {zadoks_stage} non trouvé pour '{crop}'. "
            f"L'échelle Zadoks s'applique uniquement aux céréales (blé, orge, seigle)."
        )


# ============================================================================
# Crop/Field Exceptions
# ============================================================================

class InvalidCropNameError(ToolException):
    """Invalid or unknown crop name"""
    def __init__(self, crop_name: str):
        super().__init__(
            f"Culture '{crop_name}' non reconnue. "
            f"Utilisez les noms standards (blé, maïs, colza, tournesol, etc.)."
        )


class InvalidFieldSizeError(ToolException):
    """Invalid field size"""
    def __init__(self, size: float):
        super().__init__(
            f"Surface de parcelle invalide: {size} ha. "
            f"Vérifiez la surface saisie (doit être > 0)."
        )


class InvalidDoseError(ToolException):
    """Invalid product dose"""
    def __init__(self, dose: float, unit: str):
        super().__init__(
            f"Dose invalide: {dose} {unit}. "
            f"Vérifiez les recommandations du produit et les doses homologuées."
        )


class GrowthStageNotFoundError(ToolException):
    """Growth stage not found for crop"""
    def __init__(self, crop: str, stage: str):
        super().__init__(
            f"Stade de croissance '{stage}' non trouvé pour {crop}. "
            f"Utilisez un stade valide (ex: semis, tallage, montaison, épiaison, floraison, maturation)."
        )


class KcCoefficientNotFoundError(ToolException):
    """Kc coefficient not found"""
    def __init__(self, crop: str, stage: str):
        super().__init__(
            f"Coefficient Kc non trouvé pour {crop} au stade {stage}. "
            f"Données d'irrigation non disponibles pour cette combinaison."
        )


# ============================================================================
# Crop Health Tool Exceptions
# ============================================================================

class CropHealthAPIError(ToolException):
    """Crop health API unavailable"""
    def __init__(self, details: str = ""):
        message = "Le service de santé des cultures est temporairement indisponible."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class DiseaseNotFoundError(ToolException):
    """Disease not found in database"""
    def __init__(self, disease_name: str):
        super().__init__(
            f"Maladie '{disease_name}' non trouvée dans la base de données. "
            f"Vérifiez l'orthographe ou utilisez le nom scientifique."
        )


class PestNotFoundError(ToolException):
    """Pest not found in database"""
    def __init__(self, pest_name: str):
        super().__init__(
            f"Ravageur '{pest_name}' non trouvé dans la base de données. "
            f"Vérifiez l'orthographe ou utilisez le nom scientifique."
        )


class ImageAnalysisError(ToolException):
    """Error analyzing crop image"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur lors de l'analyse de l'image: {details}. "
            f"Vérifiez que l'image est claire et bien éclairée."
        )


# ============================================================================
# Planning Tool Exceptions
# ============================================================================

class PlanningAPIError(ToolException):
    """Planning API unavailable"""
    def __init__(self, details: str = ""):
        message = "Le service de planification est temporairement indisponible."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class InvalidDateRangeError(ToolException):
    """Invalid date range"""
    def __init__(self, start_date: str, end_date: str):
        super().__init__(
            f"Plage de dates invalide: {start_date} à {end_date}. "
            f"Vérifiez que la date de début est avant la date de fin."
        )


class OptimizationError(ToolException):
    """Error optimizing schedule"""
    def __init__(self, details: str):
        super().__init__(
            f"Impossible d'optimiser le planning: {details}. "
            f"Vérifiez que vous avez assez de matériel et de main-d'œuvre disponibles, "
            f"et que les dates sont réalistes."
        )


# ============================================================================
# Sustainability Tool Exceptions
# ============================================================================

class SustainabilityAPIError(ToolException):
    """Sustainability API unavailable"""
    def __init__(self, details: str = ""):
        message = "Le service de durabilité est temporairement indisponible."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class CarbonCalculationError(ToolException):
    """Error calculating carbon footprint"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur lors du calcul de l'empreinte carbone: {details}. "
            f"Vérifiez les données d'entrée."
        )


class BiodiversityAnalysisError(ToolException):
    """Error analyzing biodiversity"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur lors de l'analyse de biodiversité: {details}. "
            f"Vérifiez les données de la parcelle."
        )


# ============================================================================
# Internet/Search Tool Exceptions
# ============================================================================

class SearchAPIError(ToolException):
    """Search API unavailable"""
    def __init__(self, details: str = ""):
        message = "Le service de recherche est temporairement indisponible."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class NoSearchResultsError(ToolException):
    """No search results found"""
    def __init__(self, query: str):
        super().__init__(
            f"Aucun résultat trouvé pour '{query}'. "
            f"Essayez avec des termes de recherche différents."
        )


# ============================================================================
# Supplier Tool Exceptions
# ============================================================================

class SupplierAPIError(ToolException):
    """Supplier API unavailable"""
    def __init__(self, details: str = ""):
        message = "Le service fournisseur est temporairement indisponible."
        if details:
            message += f" (Détails: {details})"
        super().__init__(message)


class SupplierNotFoundError(ToolException):
    """Supplier not found"""
    def __init__(self, supplier_name: str):
        super().__init__(
            f"Fournisseur '{supplier_name}' non trouvé. "
            f"Vérifiez le nom ou utilisez la recherche."
        )


class PriceNotAvailableError(ToolException):
    """Price not available"""
    def __init__(self, product_name: str):
        super().__init__(
            f"Prix non disponible pour '{product_name}'. "
            f"Le produit n'est peut-être plus en stock."
        )


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseConnectionError(ToolException):
    """Database connection failed"""
    def __init__(self, db_name: str = ""):
        message = "Impossible de se connecter à la base de données."
        if db_name:
            message += f" (Base: {db_name})"
        message += " Réessayez ou contactez le support."
        super().__init__(message)


class DatabaseQueryError(ToolException):
    """Database query failed"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur lors de la requête en base de données: {details}. "
            f"Contactez le support si le problème persiste."
        )


class DataIntegrityError(ToolException):
    """Data integrity violation"""
    def __init__(self, details: str):
        super().__init__(
            f"Erreur d'intégrité des données: {details}. "
            f"Les données sont incohérentes. Contactez le support."
        )


# ============================================================================
# Validation Exceptions
# ============================================================================

class DateValidationError(ToolException):
    """Invalid date format or value"""
    def __init__(self, date_str: str):
        super().__init__(
            f"Date invalide: '{date_str}'. "
            f"Utilisez le format JJ/MM/AAAA ou AAAA-MM-JJ."
        )


class CoordinateValidationError(ToolException):
    """Invalid GPS coordinates"""
    def __init__(self, lat: float = None, lon: float = None):
        if lat is not None and lon is not None:
            super().__init__(
                f"Coordonnées GPS invalides: latitude={lat}, longitude={lon}. "
                f"Vérifiez les coordonnées (France: lat 41-51, lon -5 à 10)."
            )
        else:
            super().__init__(
                "Coordonnées GPS invalides. "
                "Vérifiez le format (latitude, longitude)."
            )


class QuantityValidationError(ToolException):
    """Invalid quantity value"""
    def __init__(self, quantity: float, unit: str, context: str = ""):
        message = f"Quantité invalide: {quantity} {unit}."
        if context:
            message += f" ({context})"
        message += " Vérifiez la valeur saisie."
        super().__init__(message)


# ============================================================================
# Generic Tool Exceptions
# ============================================================================

class ToolTimeoutError(ToolException):
    """Generic tool timeout"""
    def __init__(self, tool_name: str, timeout_seconds: int):
        super().__init__(
            f"L'outil '{tool_name}' a dépassé le délai d'attente ({timeout_seconds}s). "
            f"Réessayez ou contactez le support."
        )


class ToolConfigurationError(ToolException):
    """Tool configuration error"""
    def __init__(self, tool_name: str, details: str):
        super().__init__(
            f"Erreur de configuration de l'outil '{tool_name}': {details}. "
            f"Contactez l'administrateur."
        )


class InsufficientDataError(ToolException):
    """Insufficient data to perform operation"""
    def __init__(self, required_data: str):
        super().__init__(
            f"Données insuffisantes pour effectuer l'opération. "
            f"Données requises: {required_data}."
        )


# ============================================================================
# Exception Categories (for better error handling)
# ============================================================================

# Network/API related exceptions
API_EXCEPTIONS = (
    WeatherAPIError,
    RegulatoryAPIError,
    FarmDataAPIError,
    CropHealthAPIError,
    PlanningAPIError,
    SustainabilityAPIError,
    SearchAPIError,
    SupplierAPIError,
    EPPODatabaseError,
)

# Data validation related exceptions
VALIDATION_EXCEPTIONS = (
    WeatherValidationError,
    AMMValidationError,
    InvalidSIRETError,
    InvalidDateRangeError,
    DateValidationError,
    CoordinateValidationError,
    QuantityValidationError,
    InvalidEPPOCodeError,
    InvalidBBCHStageError,
    InvalidCropNameError,
    InvalidFieldSizeError,
    InvalidDoseError,
)

# Not found errors
NOT_FOUND_EXCEPTIONS = (
    ProductNotFoundError,
    FarmNotFoundError,
    ParcelleNotFoundError,
    InterventionNotFoundError,
    MillesimeNotFoundError,
    DiseaseNotFoundError,
    PestNotFoundError,
    SupplierNotFoundError,
    WeatherLocationNotFoundError,
    EPPOCodeNotFoundError,
    BBCHStageNotFoundError,
    BBCHDataMissingError,
    ZadoksStageNotFoundError,
    GrowthStageNotFoundError,
    KcCoefficientNotFoundError,
)

# Database related exceptions
DATABASE_EXCEPTIONS = (
    DatabaseConnectionError,
    DatabaseQueryError,
    DataIntegrityError,
    AMMDataError,
)

# Timeout related exceptions
TIMEOUT_EXCEPTIONS = (
    WeatherTimeoutError,
    ToolTimeoutError,
)

# All agricultural tool exceptions
ALL_TOOL_EXCEPTIONS = (
    API_EXCEPTIONS +
    VALIDATION_EXCEPTIONS +
    NOT_FOUND_EXCEPTIONS +
    DATABASE_EXCEPTIONS +
    TIMEOUT_EXCEPTIONS
)

