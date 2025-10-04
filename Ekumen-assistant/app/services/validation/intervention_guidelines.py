"""
Intervention Guidelines and Validation Rules
Defines comprehensive guidelines for agricultural interventions and validation logic
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


class InterventionType(str, Enum):
    """Standard intervention types"""
    SEMIS = "semis"
    TRAITEMENT_PHYTOSANITAIRE = "traitement_phytosanitaire"
    FERTILISATION = "fertilisation"
    RECOLTE = "recolte"
    IRRIGATION = "irrigation"
    TRAVAIL_SOL = "travail_sol"
    OBSERVATION = "observation"
    AUTRE = "autre"


class ValidationLevel(str, Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """Individual validation rule"""
    field: str
    rule_type: str
    message: str
    level: ValidationLevel
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None
    custom_validator: Optional[callable] = None


@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    level: ValidationLevel
    message: str
    field: str
    suggested_value: Optional[Any] = None
    compliance_issues: List[str] = None


class InterventionGuidelines:
    """Comprehensive intervention guidelines and validation rules"""
    
    def __init__(self):
        self.guidelines = self._initialize_guidelines()
        self.compliance_rules = self._initialize_compliance_rules()
    
    def _initialize_guidelines(self) -> Dict[str, List[ValidationRule]]:
        """Initialize intervention guidelines by type"""
        return {
            InterventionType.SEMIS: [
                ValidationRule(
                    field="date_intervention",
                    rule_type="date_range",
                    message="Date de semis doit être dans la période recommandée pour cette culture",
                    level=ValidationLevel.WARNING,
                    required=True
                ),
                ValidationRule(
                    field="surface_travaillee_ha",
                    rule_type="positive_number",
                    message="Surface travaillée doit être positive",
                    level=ValidationLevel.ERROR,
                    required=True,
                    min_value=0.01
                ),
                ValidationRule(
                    field="culture",
                    rule_type="required",
                    message="Culture doit être spécifiée",
                    level=ValidationLevel.ERROR,
                    required=True
                ),
                ValidationRule(
                    field="intrants",
                    rule_type="semis_products",
                    message="Vérifier que les semences sont appropriées pour la culture",
                    level=ValidationLevel.WARNING
                )
            ],
            
            InterventionType.TRAITEMENT_PHYTOSANITAIRE: [
                ValidationRule(
                    field="date_intervention",
                    rule_type="date_range",
                    message="Date de traitement doit respecter les délais avant récolte",
                    level=ValidationLevel.CRITICAL,
                    required=True
                ),
                ValidationRule(
                    field="intrants",
                    rule_type="phytosanitary_required",
                    message="Produit phytosanitaire doit être spécifié avec code AMM",
                    level=ValidationLevel.ERROR,
                    required=True
                ),
                ValidationRule(
                    field="intrants",
                    rule_type="amm_code_validation",
                    message="Code AMM doit être valide et actif",
                    level=ValidationLevel.ERROR
                ),
                ValidationRule(
                    field="intrants",
                    rule_type="dose_validation",
                    message="Dose appliquée doit respecter les limites autorisées",
                    level=ValidationLevel.CRITICAL
                ),
                ValidationRule(
                    field="conditions_meteo",
                    rule_type="weather_conditions",
                    message="Conditions météo doivent être favorables (vent < 19 km/h, pas de pluie)",
                    level=ValidationLevel.WARNING
                ),
                ValidationRule(
                    field="surface_travaillee_ha",
                    rule_type="positive_number",
                    message="Surface travaillée doit être positive",
                    level=ValidationLevel.ERROR,
                    required=True,
                    min_value=0.01
                )
            ],
            
            InterventionType.FERTILISATION: [
                ValidationRule(
                    field="date_intervention",
                    rule_type="date_range",
                    message="Date de fertilisation doit respecter les périodes d'épandage autorisées",
                    level=ValidationLevel.WARNING,
                    required=True
                ),
                ValidationRule(
                    field="intrants",
                    rule_type="fertilizer_required",
                    message="Type et quantité de fertilisant doivent être spécifiés",
                    level=ValidationLevel.ERROR,
                    required=True
                ),
                ValidationRule(
                    field="intrants",
                    rule_type="nitrogen_limits",
                    message="Quantité d'azote doit respecter les plafonds réglementaires",
                    level=ValidationLevel.CRITICAL
                ),
                ValidationRule(
                    field="surface_travaillee_ha",
                    rule_type="positive_number",
                    message="Surface travaillée doit être positive",
                    level=ValidationLevel.ERROR,
                    required=True,
                    min_value=0.01
                )
            ],
            
            InterventionType.RECOLTE: [
                ValidationRule(
                    field="date_intervention",
                    rule_type="harvest_timing",
                    message="Date de récolte doit correspondre à la maturité de la culture",
                    level=ValidationLevel.WARNING,
                    required=True
                ),
                ValidationRule(
                    field="extrants",
                    rule_type="harvest_data",
                    message="Rendement et qualité doivent être enregistrés",
                    level=ValidationLevel.INFO
                ),
                ValidationRule(
                    field="surface_travaillee_ha",
                    rule_type="positive_number",
                    message="Surface récoltée doit être positive",
                    level=ValidationLevel.ERROR,
                    required=True,
                    min_value=0.01
                )
            ],
            
            InterventionType.IRRIGATION: [
                ValidationRule(
                    field="date_intervention",
                    rule_type="irrigation_timing",
                    message="Irrigation doit respecter les restrictions d'eau",
                    level=ValidationLevel.WARNING,
                    required=True
                ),
                ValidationRule(
                    field="intrants",
                    rule_type="water_quantity",
                    message="Quantité d'eau utilisée doit être enregistrée",
                    level=ValidationLevel.INFO
                ),
                ValidationRule(
                    field="surface_travaillee_ha",
                    rule_type="positive_number",
                    message="Surface irriguée doit être positive",
                    level=ValidationLevel.ERROR,
                    required=True,
                    min_value=0.01
                )
            ]
        }
    
    def _initialize_compliance_rules(self) -> Dict[str, Any]:
        """Initialize compliance rules for regulatory validation"""
        return {
            "phytosanitary": {
                "max_wind_speed": 19,  # km/h
                "min_temperature": 5,  # °C
                "max_temperature": 30,  # °C
                "required_amm": True,
                "required_target": True,
                "max_dose_deviation": 0.1  # 10% tolerance
            },
            "fertilization": {
                "nitrogen_limits": {
                    "wheat": 200,  # kg N/ha/year
                    "corn": 250,
                    "rapeseed": 180
                },
                "spreading_periods": {
                    "autumn": {"start": "09-01", "end": "11-30"},
                    "spring": {"start": "02-01", "end": "07-31"}
                }
            },
            "harvest": {
                "min_moisture": 14,  # % for storage
                "max_moisture": 25   # % for immediate use
            }
        }
    
    def validate_intervention(self, intervention_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate intervention against guidelines"""
        results = []
        
        # Get intervention type
        intervention_type = intervention_data.get("type_intervention")
        if not intervention_type:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Type d'intervention requis",
                field="type_intervention"
            ))
            return results
        
        # Get rules for this intervention type
        rules = self.guidelines.get(intervention_type, [])
        
        # Apply validation rules
        for rule in rules:
            result = self._apply_validation_rule(rule, intervention_data)
            if result:
                results.append(result)
        
        # Apply compliance checks
        compliance_results = self._check_compliance(intervention_type, intervention_data)
        results.extend(compliance_results)
        
        return results
    
    def _apply_validation_rule(self, rule: ValidationRule, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Apply individual validation rule"""
        field_value = data.get(rule.field)
        
        # Check required fields
        if rule.required and (field_value is None or field_value == ""):
            return ValidationResult(
                is_valid=False,
                level=rule.level,
                message=rule.message,
                field=rule.field
            )
        
        # Skip if field is empty and not required
        if field_value is None or field_value == "":
            return None
        
        # Apply rule-specific validation
        if rule.rule_type == "positive_number":
            try:
                value = float(field_value)
                if rule.min_value and value < rule.min_value:
                    return ValidationResult(
                        is_valid=False,
                        level=rule.level,
                        message=f"{rule.message} (minimum: {rule.min_value})",
                        field=rule.field
                    )
                if rule.max_value and value > rule.max_value:
                    return ValidationResult(
                        is_valid=False,
                        level=rule.level,
                        message=f"{rule.message} (maximum: {rule.max_value})",
                        field=rule.field
                    )
            except (ValueError, TypeError):
                return ValidationResult(
                    is_valid=False,
                    level=rule.level,
                    message=f"{rule.message} (valeur numérique requise)",
                    field=rule.field
                )
        
        elif rule.rule_type == "phytosanitary_required":
            intrants = data.get("intrants", [])
            has_phytosanitary = any(
                intrant.get("type_intrant") == "Phytosanitaire" 
                for intrant in intrants
            )
            if not has_phytosanitary:
                return ValidationResult(
                    is_valid=False,
                    level=rule.level,
                    message=rule.message,
                    field=rule.field
                )
        
        elif rule.rule_type == "amm_code_validation":
            intrants = data.get("intrants", [])
            for intrant in intrants:
                if intrant.get("type_intrant") == "Phytosanitaire":
                    amm_code = intrant.get("code_amm")
                    if not amm_code:
                        return ValidationResult(
                            is_valid=False,
                            level=rule.level,
                            message="Code AMM requis pour les produits phytosanitaires",
                            field=rule.field
                        )
                    # TODO: Validate AMM code against EPHY database
        
        elif rule.rule_type == "weather_conditions":
            weather = data.get("conditions_meteo", "")
            if "vent" in weather.lower():
                # Extract wind speed (simplified)
                if "vent faible" in weather.lower() or "vent" in weather.lower():
                    # This is a simplified check - in reality, you'd parse the actual wind speed
                    pass
                else:
                    return ValidationResult(
                        is_valid=False,
                        level=rule.level,
                        message=rule.message,
                        field=rule.field
                    )
        
        return None
    
    def _check_compliance(self, intervention_type: str, data: Dict[str, Any]) -> List[ValidationResult]:
        """Check regulatory compliance"""
        results = []
        
        if intervention_type == InterventionType.TRAITEMENT_PHYTOSANITAIRE:
            results.extend(self._check_phytosanitary_compliance(data))
        elif intervention_type == InterventionType.FERTILISATION:
            results.extend(self._check_fertilization_compliance(data))
        
        return results
    
    def _check_phytosanitary_compliance(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Check phytosanitary treatment compliance"""
        results = []
        
        # Check wind conditions
        weather = data.get("conditions_meteo", "")
        if "vent" in weather.lower() and "fort" in weather.lower():
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message="Traitement interdit par vent fort (>19 km/h)",
                field="conditions_meteo"
            ))
        
        # Check temperature
        if "température" in weather.lower():
            # Extract temperature (simplified)
            if "froid" in weather.lower() or "gel" in weather.lower():
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message="Traitement déconseillé par température trop basse",
                    field="conditions_meteo"
                ))
        
        return results
    
    def _check_fertilization_compliance(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Check fertilization compliance"""
        results = []
        
        # Check nitrogen limits
        culture = data.get("culture", "").lower()
        intrants = data.get("intrants", [])
        
        for intrant in intrants:
            if "azote" in intrant.get("libelle", "").lower() or "N" in intrant.get("libelle", ""):
                # Check against nitrogen limits
                limit = self.compliance_rules["fertilization"]["nitrogen_limits"].get(culture)
                if limit:
                    # This would need actual nitrogen content calculation
                    pass
        
        return results
    
    def generate_confirmation_summary(self, intervention_data: Dict[str, Any], validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate confirmation summary for farmer review"""
        
        # Categorize validation results
        errors = [r for r in validation_results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in validation_results if r.level == ValidationLevel.WARNING]
        infos = [r for r in validation_results if r.level == ValidationLevel.INFO]
        
        # Generate summary
        summary = {
            "intervention_summary": {
                "type": intervention_data.get("type_intervention"),
                "parcelle": intervention_data.get("parcelle"),
                "date": intervention_data.get("date_intervention"),
                "surface": intervention_data.get("surface_travaillee_ha"),
                "culture": intervention_data.get("culture")
            },
            "products_used": intervention_data.get("intrants", []),
            "equipment": intervention_data.get("materiels", []),
            "conditions": intervention_data.get("conditions_meteo"),
            "validation": {
                "is_valid": len(errors) == 0,
                "errors": [{"field": r.field, "message": r.message} for r in errors],
                "warnings": [{"field": r.field, "message": r.message} for r in warnings],
                "infos": [{"field": r.field, "message": r.message} for r in infos]
            },
            "compliance_status": "conforme" if len(errors) == 0 else "non_conforme",
            "requires_confirmation": len(errors) > 0 or len(warnings) > 0
        }
        
        return summary
    
    def get_intervention_guidelines(self, intervention_type: str) -> Dict[str, Any]:
        """Get guidelines for specific intervention type"""
        guidelines = {
            InterventionType.SEMIS: {
                "description": "Enregistrement d'un semis",
                "required_fields": ["parcelle", "date_intervention", "surface_travaillee_ha", "culture", "intrants"],
                "tips": [
                    "Vérifiez la date de semis selon les recommandations pour votre culture",
                    "Enregistrez le type et la quantité de semences utilisées",
                    "Notez les conditions de sol et météo"
                ]
            },
            InterventionType.TRAITEMENT_PHYTOSANITAIRE: {
                "description": "Enregistrement d'un traitement phytosanitaire",
                "required_fields": ["parcelle", "date_intervention", "surface_travaillee_ha", "intrants", "conditions_meteo"],
                "tips": [
                    "Code AMM obligatoire pour tous les produits phytosanitaires",
                    "Vérifiez les conditions météo (vent < 19 km/h, pas de pluie)",
                    "Respectez les délais avant récolte",
                    "Enregistrez la cible du traitement (mauvaises herbes, maladies, ravageurs)"
                ],
                "compliance_checks": [
                    "Code AMM valide et actif",
                    "Dose conforme à l'étiquette",
                    "Conditions météo favorables",
                    "Délais avant récolte respectés"
                ]
            },
            InterventionType.FERTILISATION: {
                "description": "Enregistrement d'une fertilisation",
                "required_fields": ["parcelle", "date_intervention", "surface_travaillee_ha", "intrants"],
                "tips": [
                    "Respectez les plafonds d'azote par culture",
                    "Vérifiez les périodes d'épandage autorisées",
                    "Enregistrez le type et la quantité de fertilisant"
                ],
                "compliance_checks": [
                    "Plafonds d'azote respectés",
                    "Périodes d'épandage autorisées",
                    "Distances aux cours d'eau respectées"
                ]
            }
        }
        
        return guidelines.get(intervention_type, {})
