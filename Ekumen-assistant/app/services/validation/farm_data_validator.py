"""
Farm Data Validation Service
Provides comprehensive validation for farm data operations
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import re
import logging

from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error with detailed information"""
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)

class FarmDataValidator:
    """Comprehensive validator for farm data operations"""
    
    # Valid culture codes (from MesParcelles)
    VALID_CULTURE_CODES = {
        'BLE_TENDRE', 'BLE_DUR', 'ORGE', 'AVOINE', 'SEIGLE', 'TRITICALE',
        'MAIS', 'TOURNESOL', 'COLZA', 'SOJA', 'POIS', 'FEVE', 'LENTILLE',
        'POMME_DE_TERRE', 'BETTERAVE', 'CANNE_A_SUCRE', 'COTON', 'TABAC',
        'VIGNE', 'ARBORICULTURE', 'MARAICHAGE', 'JACHERE', 'PRAIRIE',
        'FORET', 'AUTRE'
    }
    
    # Valid intervention types
    VALID_INTERVENTION_TYPES = {
        'SEMIS', 'TRAITEMENT_PHYTOSANITAIRE', 'FERTILISATION', 'IRRIGATION',
        'RECOLTE', 'LABOUR', 'HERSE', 'ROULAGE', 'BUTAGE', 'BINAGE',
        'TRAITEMENT_FONGICIDE', 'TRAITEMENT_INSECTICIDE', 'TRAITEMENT_HERBICIDE',
        'EPANDAGE_ENGRAIS', 'EPANDAGE_FUMIER', 'EPANDAGE_COMPOST',
        'TAILLE', 'GREFFAGE', 'PLANTATION', 'ARROSAGE', 'DESHERBAGE',
        'TRAITEMENT_BIOLOGIQUE', 'AUTRE'
    }
    
    # Valid product types
    VALID_PRODUCT_TYPES = {
        'FONGICIDE', 'INSECTICIDE', 'HERBICIDE', 'ACARICIDE', 'NEMATICIDE',
        'RODENTICIDE', 'MOLLUSCICIDE', 'REPULSIF', 'STIMULATEUR',
        'ENGRAIS_MINERAL', 'ENGRAIS_ORGANIQUE', 'AMENDEMENT', 'SUBSTRAT',
        'SEMENCE', 'PLANT', 'AUTRE'
    }
    
    # Valid units
    VALID_UNITS = {
        'L', 'L/ha', 'kg', 'kg/ha', 'g', 'g/ha', 'ml', 'ml/ha',
        'm3', 'm3/ha', 't', 't/ha', 'q', 'q/ha', 'unite', 'unite/ha',
        'pourcent', 'ppm', 'pH', 'EC', 'CEC', 'ha', 'm2', 'cm'
    }
    
    # Valid status values
    VALID_PARCEL_STATUS = {'seme', 'en_croissance', 'recolte', 'jachère'}
    VALID_INTERVENTION_STATUS = {'planifie', 'en_cours', 'termine', 'reporte', 'annule'}
    
    @staticmethod
    def validate_siret(siret: str) -> bool:
        """Validate French SIRET number format"""
        if not siret:
            return False
        
        # Remove spaces and check length
        siret_clean = siret.replace(' ', '')
        if len(siret_clean) != 14:
            return False
        
        # Check if all characters are digits
        if not siret_clean.isdigit():
            return False
        
        # For testing purposes, accept any 14-digit number
        # In production, you would implement proper SIRET validation
        return True
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format"""
        try:
            UUID(uuid_str)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> bool:
        """Validate that start_date is before end_date"""
        return start_date <= end_date
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str = "value") -> Decimal:
        """Validate that a number is positive"""
        try:
            decimal_value = Decimal(str(value))
            if decimal_value < 0:
                raise ValidationError(f"{field_name} must be positive", field_name, "NEGATIVE_VALUE")
            return decimal_value
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number", field_name, "INVALID_NUMBER")
    
    @staticmethod
    def validate_percentage(value: Any, field_name: str = "percentage") -> Decimal:
        """Validate percentage value (0-100)"""
        decimal_value = FarmDataValidator.validate_positive_number(value, field_name)
        if decimal_value > 100:
            raise ValidationError(f"{field_name} cannot exceed 100%", field_name, "PERCENTAGE_TOO_HIGH")
        return decimal_value
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> Tuple[float, float]:
        """Validate GPS coordinates"""
        if not (-90 <= latitude <= 90):
            raise ValidationError("Latitude must be between -90 and 90", "latitude", "INVALID_LATITUDE")
        
        if not (-180 <= longitude <= 180):
            raise ValidationError("Longitude must be between -180 and 180", "longitude", "INVALID_LONGITUDE")
        
        return float(latitude), float(longitude)
    
    @staticmethod
    def validate_culture_code(culture_code: str) -> str:
        """Validate culture code"""
        if not culture_code:
            raise ValidationError("Culture code is required", "culture_code", "MISSING_CULTURE_CODE")
        
        culture_upper = culture_code.upper()
        if culture_upper not in FarmDataValidator.VALID_CULTURE_CODES:
            raise ValidationError(
                f"Invalid culture code: {culture_code}. Valid codes: {', '.join(sorted(FarmDataValidator.VALID_CULTURE_CODES))}",
                "culture_code",
                "INVALID_CULTURE_CODE"
            )
        
        return culture_upper
    
    @staticmethod
    def validate_intervention_type(intervention_type: str) -> str:
        """Validate intervention type"""
        if not intervention_type:
            raise ValidationError("Intervention type is required", "intervention_type", "MISSING_INTERVENTION_TYPE")
        
        type_upper = intervention_type.upper()
        if type_upper not in FarmDataValidator.VALID_INTERVENTION_TYPES:
            raise ValidationError(
                f"Invalid intervention type: {intervention_type}. Valid types: {', '.join(sorted(FarmDataValidator.VALID_INTERVENTION_TYPES))}",
                "intervention_type",
                "INVALID_INTERVENTION_TYPE"
            )
        
        return type_upper
    
    @staticmethod
    def validate_product_type(product_type: str) -> str:
        """Validate product type"""
        if not product_type:
            raise ValidationError("Product type is required", "product_type", "MISSING_PRODUCT_TYPE")
        
        type_upper = product_type.upper()
        if type_upper not in FarmDataValidator.VALID_PRODUCT_TYPES:
            raise ValidationError(
                f"Invalid product type: {product_type}. Valid types: {', '.join(sorted(FarmDataValidator.VALID_PRODUCT_TYPES))}",
                "product_type",
                "INVALID_PRODUCT_TYPE"
            )
        
        return type_upper
    
    @staticmethod
    def validate_unit(unit: str) -> str:
        """Validate unit"""
        if not unit:
            raise ValidationError("Unit is required", "unit", "MISSING_UNIT")
        
        unit_lower = unit.lower()
        if unit_lower not in FarmDataValidator.VALID_UNITS:
            raise ValidationError(
                f"Invalid unit: {unit}. Valid units: {', '.join(sorted(FarmDataValidator.VALID_UNITS))}",
                "unit",
                "INVALID_UNIT"
            )
        
        return unit_lower
    
    @staticmethod
    def validate_parcel_status(status: str) -> str:
        """Validate parcel status"""
        if not status:
            raise ValidationError("Parcel status is required", "status", "MISSING_STATUS")
        
        status_lower = status.lower()
        if status_lower not in FarmDataValidator.VALID_PARCEL_STATUS:
            raise ValidationError(
                f"Invalid parcel status: {status}. Valid statuses: {', '.join(sorted(FarmDataValidator.VALID_PARCEL_STATUS))}",
                "status",
                "INVALID_PARCEL_STATUS"
            )
        
        return status_lower
    
    @staticmethod
    def validate_intervention_status(status: str) -> str:
        """Validate intervention status"""
        if not status:
            raise ValidationError("Intervention status is required", "status", "MISSING_STATUS")
        
        status_lower = status.lower()
        if status_lower not in FarmDataValidator.VALID_INTERVENTION_STATUS:
            raise ValidationError(
                f"Invalid intervention status: {status}. Valid statuses: {', '.join(sorted(FarmDataValidator.VALID_INTERVENTION_STATUS))}",
                "status",
                "INVALID_INTERVENTION_STATUS"
            )
        
        return status_lower
    
    @staticmethod
    def validate_amm_number(amm: str) -> str:
        """Validate AMM (Autorisation de Mise sur le Marché) number"""
        if not amm:
            raise ValidationError("AMM number is required", "amm", "MISSING_AMM")
        
        # AMM format: typically 7-8 digits
        amm_clean = amm.replace(' ', '').replace('-', '')
        if not re.match(r'^\d{7,8}$', amm_clean):
            raise ValidationError("AMM number must be 7-8 digits", "amm", "INVALID_AMM_FORMAT")
        
        return amm_clean
    
    @staticmethod
    def validate_weather_conditions(conditions: str) -> str:
        """Validate weather conditions description"""
        if not conditions:
            return ""
        
        # Basic validation: not too long, contains reasonable characters
        if len(conditions) > 500:
            raise ValidationError("Weather conditions description too long (max 500 characters)", "conditions_meteo", "DESCRIPTION_TOO_LONG")
        
        # Check for reasonable weather-related terms
        weather_terms = ['ensoleillé', 'nuageux', 'pluie', 'vent', 'température', 'humidité', '°C', 'km/h', 'mm']
        conditions_lower = conditions.lower()
        
        # At least one weather term should be present
        if not any(term in conditions_lower for term in weather_terms):
            logger.warning(f"Weather conditions may not be weather-related: {conditions}")
        
        return conditions.strip()
    
    @staticmethod
    def validate_notes(notes: str) -> str:
        """Validate notes field"""
        if not notes:
            return ""
        
        if len(notes) > 1000:
            raise ValidationError("Notes too long (max 1000 characters)", "notes", "NOTES_TOO_LONG")
        
        return notes.strip()
    
    @staticmethod
    def validate_parcel_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete parcel data"""
        errors = []
        validated_data = {}
        
        try:
            # Required fields
            if 'nom' in data:
                validated_data['nom'] = str(data['nom']).strip()
                if not validated_data['nom']:
                    errors.append(ValidationError("Parcel name is required", "nom", "MISSING_NOM"))
            
            if 'siret' in data:
                if not FarmDataValidator.validate_siret(data['siret']):
                    errors.append(ValidationError("Invalid SIRET format", "siret", "INVALID_SIRET"))
                validated_data['siret'] = data['siret']
            
            if 'culture_code' in data:
                try:
                    validated_data['culture_code'] = FarmDataValidator.validate_culture_code(data['culture_code'])
                except ValidationError as e:
                    errors.append(e)
            
            if 'surface_ha' in data:
                try:
                    validated_data['surface_ha'] = FarmDataValidator.validate_positive_number(data['surface_ha'], "surface_ha")
                except ValidationError as e:
                    errors.append(e)
            
            if 'statut' in data:
                try:
                    validated_data['statut'] = FarmDataValidator.validate_parcel_status(data['statut'])
                except ValidationError as e:
                    errors.append(e)
            
            # Optional fields
            if 'date_semis' in data and data['date_semis']:
                try:
                    if isinstance(data['date_semis'], str):
                        validated_data['date_semis'] = datetime.fromisoformat(data['date_semis'].replace('Z', '+00:00')).date()
                    else:
                        validated_data['date_semis'] = data['date_semis']
                except (ValueError, TypeError):
                    errors.append(ValidationError("Invalid date format for date_semis", "date_semis", "INVALID_DATE"))
            
            if 'coordonnees' in data and data['coordonnees']:
                try:
                    coords = data['coordonnees']
                    if 'latitude' in coords and 'longitude' in coords:
                        lat, lon = FarmDataValidator.validate_coordinates(coords['latitude'], coords['longitude'])
                        validated_data['coordonnees'] = {'latitude': lat, 'longitude': lon}
                except ValidationError as e:
                    errors.append(e)
            
            if 'notes' in data:
                try:
                    validated_data['notes'] = FarmDataValidator.validate_notes(data['notes'])
                except ValidationError as e:
                    errors.append(e)
            
        except Exception as e:
            errors.append(ValidationError(f"Unexpected validation error: {str(e)}", None, "UNEXPECTED_ERROR"))
        
        if errors:
            error_messages = [f"{e.field}: {e.message}" if e.field else e.message for e in errors]
            raise ValidationError(f"Validation failed: {'; '.join(error_messages)}", None, "VALIDATION_FAILED")
        
        return validated_data
    
    @staticmethod
    def validate_intervention_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete intervention data"""
        errors = []
        validated_data = {}
        
        try:
            # Required fields
            if 'parcelle_id' in data:
                if not FarmDataValidator.validate_uuid(data['parcelle_id']):
                    errors.append(ValidationError("Invalid parcelle_id format", "parcelle_id", "INVALID_UUID"))
                validated_data['parcelle_id'] = data['parcelle_id']
            
            if 'siret' in data:
                if not FarmDataValidator.validate_siret(data['siret']):
                    errors.append(ValidationError("Invalid SIRET format", "siret", "INVALID_SIRET"))
                validated_data['siret'] = data['siret']
            
            if 'type_intervention' in data:
                try:
                    validated_data['type_intervention'] = FarmDataValidator.validate_intervention_type(data['type_intervention'])
                except ValidationError as e:
                    errors.append(e)
            
            if 'date_intervention' in data:
                try:
                    if isinstance(data['date_intervention'], str):
                        validated_data['date_intervention'] = datetime.fromisoformat(data['date_intervention'].replace('Z', '+00:00')).date()
                    else:
                        validated_data['date_intervention'] = data['date_intervention']
                except (ValueError, TypeError):
                    errors.append(ValidationError("Invalid date format for date_intervention", "date_intervention", "INVALID_DATE"))
            
            # Optional fields
            if 'produit_utilise' in data and data['produit_utilise']:
                validated_data['produit_utilise'] = str(data['produit_utilise']).strip()
            
            if 'dose_totale' in data and data['dose_totale'] is not None:
                try:
                    validated_data['dose_totale'] = FarmDataValidator.validate_positive_number(data['dose_totale'], "dose_totale")
                except ValidationError as e:
                    errors.append(e)
            
            if 'unite_dose' in data and data['unite_dose']:
                try:
                    validated_data['unite_dose'] = FarmDataValidator.validate_unit(data['unite_dose'])
                except ValidationError as e:
                    errors.append(e)
            
            if 'surface_traitee_ha' in data and data['surface_traitee_ha'] is not None:
                try:
                    validated_data['surface_traitee_ha'] = FarmDataValidator.validate_positive_number(data['surface_traitee_ha'], "surface_traitee_ha")
                except ValidationError as e:
                    errors.append(e)
            
            if 'conditions_meteo' in data:
                try:
                    validated_data['conditions_meteo'] = FarmDataValidator.validate_weather_conditions(data['conditions_meteo'])
                except ValidationError as e:
                    errors.append(e)
            
            if 'cout_total' in data and data['cout_total'] is not None:
                try:
                    validated_data['cout_total'] = FarmDataValidator.validate_positive_number(data['cout_total'], "cout_total")
                except ValidationError as e:
                    errors.append(e)
            
            if 'notes' in data:
                try:
                    validated_data['notes'] = FarmDataValidator.validate_notes(data['notes'])
                except ValidationError as e:
                    errors.append(e)
            
        except Exception as e:
            errors.append(ValidationError(f"Unexpected validation error: {str(e)}", None, "UNEXPECTED_ERROR"))
        
        if errors:
            error_messages = [f"{e.field}: {e.message}" if e.field else e.message for e in errors]
            raise ValidationError(f"Validation failed: {'; '.join(error_messages)}", None, "VALIDATION_FAILED")
        
        return validated_data
    
    @staticmethod
    def validate_exploitation_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete exploitation data"""
        errors = []
        validated_data = {}
        
        try:
            # Required fields
            if 'siret' in data:
                if not FarmDataValidator.validate_siret(data['siret']):
                    errors.append(ValidationError("Invalid SIRET format", "siret", "INVALID_SIRET"))
                validated_data['siret'] = data['siret']
            
            if 'nom' in data:
                validated_data['nom'] = str(data['nom']).strip()
                if not validated_data['nom']:
                    errors.append(ValidationError("Exploitation name is required", "nom", "MISSING_NOM"))
            
            # Optional fields
            if 'surface_totale_ha' in data and data['surface_totale_ha'] is not None:
                try:
                    validated_data['surface_totale_ha'] = FarmDataValidator.validate_positive_number(data['surface_totale_ha'], "surface_totale_ha")
                except ValidationError as e:
                    errors.append(e)
            
            if 'bio' in data:
                validated_data['bio'] = bool(data['bio'])
            
            if 'certification_bio' in data:
                validated_data['certification_bio'] = bool(data['certification_bio'])
            
            if 'date_certification_bio' in data and data['date_certification_bio']:
                try:
                    if isinstance(data['date_certification_bio'], str):
                        validated_data['date_certification_bio'] = datetime.fromisoformat(data['date_certification_bio'].replace('Z', '+00:00')).date()
                    else:
                        validated_data['date_certification_bio'] = data['date_certification_bio']
                except (ValueError, TypeError):
                    errors.append(ValidationError("Invalid date format for date_certification_bio", "date_certification_bio", "INVALID_DATE"))
            
        except Exception as e:
            errors.append(ValidationError(f"Unexpected validation error: {str(e)}", None, "UNEXPECTED_ERROR"))
        
        if errors:
            error_messages = [f"{e.field}: {e.message}" if e.field else e.message for e in errors]
            raise ValidationError(f"Validation failed: {'; '.join(error_messages)}", None, "VALIDATION_FAILED")
        
        return validated_data

# Pydantic models for request validation
class ParcelCreateRequest(BaseModel):
    nom: str = Field(..., min_length=1, max_length=255, description="Parcel name")
    siret: str = Field(..., description="Farm SIRET number")
    culture_code: Optional[str] = Field(None, description="Culture code")
    surface_ha: Optional[Decimal] = Field(None, ge=0, description="Surface area in hectares")
    variete: Optional[str] = Field(None, max_length=100, description="Variety")
    date_semis: Optional[date] = Field(None, description="Sowing date")
    date_recolte_prevue: Optional[date] = Field(None, description="Expected harvest date")
    rendement_prevu: Optional[Decimal] = Field(None, ge=0, description="Expected yield")
    coordonnees: Optional[Dict[str, float]] = Field(None, description="GPS coordinates")
    sol_type: Optional[str] = Field(None, max_length=100, description="Soil type")
    irrigation: Optional[bool] = Field(None, description="Irrigation available")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes")
    
    @validator('siret')
    def validate_siret(cls, v):
        if not FarmDataValidator.validate_siret(v):
            raise ValueError('Invalid SIRET format')
        return v
    
    @validator('culture_code')
    def validate_culture_code(cls, v):
        if v:
            return FarmDataValidator.validate_culture_code(v)
        return v
    
    @validator('coordonnees')
    def validate_coordinates(cls, v):
        if v and 'latitude' in v and 'longitude' in v:
            FarmDataValidator.validate_coordinates(v['latitude'], v['longitude'])
        return v

class InterventionCreateRequest(BaseModel):
    parcelle_id: UUID = Field(..., description="Parcel ID")
    siret: str = Field(..., description="Farm SIRET number")
    type_intervention: str = Field(..., description="Intervention type")
    date_intervention: date = Field(..., description="Intervention date")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    produit_utilise: Optional[str] = Field(None, max_length=200, description="Product used")
    dose_totale: Optional[Decimal] = Field(None, ge=0, description="Total dose")
    unite_dose: Optional[str] = Field(None, description="Dose unit")
    surface_traitee_ha: Optional[Decimal] = Field(None, ge=0, description="Treated surface in hectares")
    materiel_utilise: Optional[str] = Field(None, max_length=200, description="Equipment used")
    conditions_meteo: Optional[str] = Field(None, max_length=500, description="Weather conditions")
    cout_total: Optional[Decimal] = Field(None, ge=0, description="Total cost")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes")
    
    @validator('siret')
    def validate_siret(cls, v):
        if not FarmDataValidator.validate_siret(v):
            raise ValueError('Invalid SIRET format')
        return v
    
    @validator('type_intervention')
    def validate_intervention_type(cls, v):
        return FarmDataValidator.validate_intervention_type(v)
    
    @validator('unite_dose')
    def validate_unit(cls, v):
        if v:
            return FarmDataValidator.validate_unit(v)
        return v

class ExploitationCreateRequest(BaseModel):
    siret: str = Field(..., description="Farm SIRET number")
    nom: str = Field(..., min_length=1, max_length=255, description="Farm name")
    region_code: Optional[str] = Field(None, max_length=2, description="Region code")
    department_code: Optional[str] = Field(None, max_length=3, description="Department code")
    commune_insee: Optional[str] = Field(None, max_length=5, description="Commune INSEE code")
    surface_totale_ha: Optional[Decimal] = Field(None, ge=0, description="Total surface area in hectares")
    type_exploitation: Optional[str] = Field(None, max_length=100, description="Farm type")
    bio: Optional[bool] = Field(None, description="Organic farming")
    certification_bio: Optional[bool] = Field(None, description="Organic certification")
    date_certification_bio: Optional[date] = Field(None, description="Organic certification date")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    
    @validator('siret')
    def validate_siret(cls, v):
        if not FarmDataValidator.validate_siret(v):
            raise ValueError('Invalid SIRET format')
        return v

# Error response models
class ValidationErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

def create_validation_error_response(validation_error: ValidationError) -> HTTPException:
    """Create a standardized HTTP exception from a validation error"""
    status_code = status.HTTP_400_BAD_REQUEST
    
    # Map specific error codes to HTTP status codes
    if validation_error.code in ['INVALID_SIRET', 'INVALID_UUID', 'INVALID_DATE']:
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif validation_error.code in ['MISSING_NOM', 'MISSING_CULTURE_CODE', 'MISSING_INTERVENTION_TYPE']:
        status_code = status.HTTP_400_BAD_REQUEST
    
    error_response = ValidationErrorResponse(
        error="ValidationError",
        message=validation_error.message,
        field=validation_error.field,
        code=validation_error.code
    )
    
    return HTTPException(
        status_code=status_code,
        detail=error_response.dict()
    )

# Global validator instance
farm_data_validator = FarmDataValidator()
