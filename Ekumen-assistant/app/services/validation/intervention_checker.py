"""
Intervention Validation Checker Service
Validates interventions against guidelines and provides interactive confirmation
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import date, datetime
import asyncio

from app.services.validation.intervention_guidelines import (
    InterventionGuidelines, 
    ValidationResult, 
    ValidationLevel
)
from app.services.infrastructure.ephy_service import EphyService
from app.services.infrastructure.weather_service import WeatherService

logger = logging.getLogger(__name__)


class InterventionChecker:
    """Comprehensive intervention validation and confirmation service"""
    
    def __init__(self):
        self.guidelines = InterventionGuidelines()
        self.ephy_service = EphyService()
        self.weather_service = WeatherService()
    
    async def validate_and_confirm_intervention(
        self, 
        intervention_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate intervention and generate confirmation data
        
        Args:
            intervention_data: Raw intervention data from voice input
            user_context: User and farm context information
            
        Returns:
            Validation and confirmation results
        """
        try:
            # Step 1: Basic validation against guidelines
            validation_results = self.guidelines.validate_intervention(intervention_data)
            
            # Step 2: Enhanced validation with external services
            enhanced_results = await self._enhanced_validation(intervention_data, user_context)
            validation_results.extend(enhanced_results)
            
            # Step 3: Generate confirmation summary
            confirmation_summary = self.guidelines.generate_confirmation_summary(
                intervention_data, validation_results
            )
            
            # Step 4: Generate confirmation questions
            confirmation_questions = self._generate_confirmation_questions(
                intervention_data, validation_results
            )
            
            # Step 5: Generate voice confirmation text
            voice_confirmation = self._generate_voice_confirmation(
                confirmation_summary, validation_results
            )
            
            return {
                "validation_results": validation_results,
                "confirmation_summary": confirmation_summary,
                "confirmation_questions": confirmation_questions,
                "voice_confirmation": voice_confirmation,
                "requires_confirmation": confirmation_summary["requires_confirmation"],
                "can_proceed": len([r for r in validation_results if r.level == ValidationLevel.ERROR]) == 0
            }
            
        except Exception as e:
            logger.error(f"Error validating intervention: {e}")
            return {
                "validation_results": [ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Erreur de validation: {str(e)}",
                    field="system"
                )],
                "confirmation_summary": {},
                "confirmation_questions": [],
                "voice_confirmation": "Désolé, une erreur s'est produite lors de la validation.",
                "requires_confirmation": True,
                "can_proceed": False
            }
    
    async def _enhanced_validation(
        self, 
        intervention_data: Dict[str, Any], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[ValidationResult]:
        """Enhanced validation using external services"""
        results = []
        
        # Validate phytosanitary products against EPHY database
        if intervention_data.get("type_intervention") == "traitement_phytosanitaire":
            ephy_results = await self._validate_phytosanitary_products(intervention_data)
            results.extend(ephy_results)
        
        # Validate weather conditions
        weather_results = await self._validate_weather_conditions(intervention_data, user_context)
        results.extend(weather_results)
        
        # Validate crop-specific rules
        crop_results = await self._validate_crop_specific_rules(intervention_data)
        results.extend(crop_results)
        
        return results
    
    async def _validate_phytosanitary_products(self, intervention_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate phytosanitary products against EPHY database"""
        results = []
        
        intrants = intervention_data.get("intrants", [])
        for intrant in intrants:
            if intrant.get("type_intrant") == "Phytosanitaire":
                amm_code = intrant.get("code_amm")
                if amm_code:
                    try:
                        # Check if AMM code is valid and active
                        product_info = await self.ephy_service.get_product_by_amm(amm_code)
                        
                        if not product_info:
                            results.append(ValidationResult(
                                is_valid=False,
                                level=ValidationLevel.ERROR,
                                message=f"Code AMM {amm_code} non trouvé dans la base EPHY",
                                field="intrants"
                            ))
                        else:
                            # Check if product is still authorized
                            if not product_info.get("is_active", False):
                                results.append(ValidationResult(
                                    is_valid=False,
                                    level=ValidationLevel.ERROR,
                                    message=f"Produit {intrant.get('libelle')} n'est plus autorisé",
                                    field="intrants"
                                ))
                            
                            # Check dose limits
                            dose_validation = self._validate_dose_limits(intrant, product_info)
                            if dose_validation:
                                results.append(dose_validation)
                            
                            # Check authorized targets
                            target_validation = self._validate_authorized_targets(intrant, product_info)
                            if target_validation:
                                results.append(target_validation)
                    
                    except Exception as e:
                        logger.error(f"Error validating AMM code {amm_code}: {e}")
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.WARNING,
                            message=f"Impossible de valider le code AMM {amm_code}",
                            field="intrants"
                        ))
        
        return results
    
    def _validate_dose_limits(self, intrant: Dict[str, Any], product_info: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate dose limits for phytosanitary product"""
        try:
            applied_dose = float(intrant.get("quantite_totale", 0))
            surface = float(intrant.get("surface_ha", 1))
            dose_per_ha = applied_dose / surface if surface > 0 else applied_dose
            
            max_dose = product_info.get("max_dose_per_ha")
            if max_dose and dose_per_ha > max_dose:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message=f"Dose appliquée ({dose_per_ha:.2f} L/ha) dépasse la dose maximale autorisée ({max_dose} L/ha)",
                    field="intrants"
                )
            
            min_dose = product_info.get("min_dose_per_ha")
            if min_dose and dose_per_ha < min_dose:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message=f"Dose appliquée ({dose_per_ha:.2f} L/ha) est inférieure à la dose minimale recommandée ({min_dose} L/ha)",
                    field="intrants"
                )
        
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Impossible de calculer la dose par hectare",
                field="intrants"
            )
        
        return None
    
    def _validate_authorized_targets(self, intrant: Dict[str, Any], product_info: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate that the target is authorized for the product"""
        target = intrant.get("cible", "").lower()
        authorized_targets = product_info.get("authorized_targets", [])
        
        if authorized_targets and target:
            if not any(auth_target.lower() in target for auth_target in authorized_targets):
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message=f"Cible '{target}' non autorisée pour ce produit",
                    field="intrants"
                )
        
        return None
    
    async def _validate_weather_conditions(
        self, 
        intervention_data: Dict[str, Any], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[ValidationResult]:
        """Validate weather conditions for intervention"""
        results = []
        
        intervention_date = intervention_data.get("date_intervention")
        if not intervention_date:
            return results
        
        try:
            # Get weather data for intervention date
            weather_data = await self.weather_service.get_weather_for_date(
                date=intervention_date,
                location=user_context.get("location") if user_context else None
            )
            
            if weather_data:
                # Check wind speed for phytosanitary treatments
                if intervention_data.get("type_intervention") == "traitement_phytosanitaire":
                    wind_speed = weather_data.get("wind_speed_kmh", 0)
                    if wind_speed > 19:
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.CRITICAL,
                            message=f"Traitement interdit: vent trop fort ({wind_speed} km/h > 19 km/h)",
                            field="conditions_meteo"
                        ))
                
                # Check temperature
                temperature = weather_data.get("temperature_celsius", 0)
                if temperature < 5:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"Traitement déconseillé: température trop basse ({temperature}°C)",
                        field="conditions_meteo"
                    ))
                
                # Check precipitation
                precipitation = weather_data.get("precipitation_mm", 0)
                if precipitation > 0:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"Traitement déconseillé: précipitations prévues ({precipitation} mm)",
                        field="conditions_meteo"
                    ))
        
        except Exception as e:
            logger.error(f"Error validating weather conditions: {e}")
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.INFO,
                message="Impossible de valider les conditions météo",
                field="conditions_meteo"
            ))
        
        return results
    
    async def _validate_crop_specific_rules(self, intervention_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate crop-specific intervention rules"""
        results = []
        
        culture = intervention_data.get("culture", "").lower()
        intervention_type = intervention_data.get("type_intervention")
        
        # Crop-specific validation rules
        if culture == "blé" and intervention_type == "traitement_phytosanitaire":
            # Check for specific wheat treatment rules
            intrants = intervention_data.get("intrants", [])
            for intrant in intrants:
                if "herbicide" in intrant.get("categorie", "").lower():
                    # Check if it's the right growth stage for herbicide application
                    pass
        
        return results
    
    def _generate_confirmation_questions(
        self, 
        intervention_data: Dict[str, Any], 
        validation_results: List[ValidationResult]
    ) -> List[Dict[str, Any]]:
        """Generate confirmation questions for farmer"""
        questions = []
        
        # Critical issues that need confirmation
        critical_issues = [r for r in validation_results if r.level == ValidationLevel.CRITICAL]
        for issue in critical_issues:
            questions.append({
                "type": "confirmation",
                "question": f"Confirmez-vous cette intervention malgré: {issue.message}?",
                "field": issue.field,
                "level": "critical",
                "requires_explicit_confirmation": True
            })
        
        # Missing required information
        missing_fields = [r for r in validation_results if r.level == ValidationLevel.ERROR and "requis" in r.message]
        for issue in missing_fields:
            questions.append({
                "type": "clarification",
                "question": f"Pouvez-vous préciser: {issue.field}?",
                "field": issue.field,
                "level": "error",
                "suggested_prompt": self._get_field_prompt(issue.field)
            })
        
        # Warnings that need acknowledgment
        warnings = [r for r in validation_results if r.level == ValidationLevel.WARNING]
        if warnings:
            questions.append({
                "type": "acknowledgment",
                "question": f"Attention: {len(warnings)} avertissement(s) détecté(s). Voulez-vous continuer?",
                "level": "warning",
                "details": [{"field": r.field, "message": r.message} for r in warnings]
            })
        
        return questions
    
    def _get_field_prompt(self, field: str) -> str:
        """Get voice prompt for missing field"""
        prompts = {
            "parcelle": "Quelle parcelle avez-vous travaillée?",
            "date_intervention": "Quelle est la date de l'intervention?",
            "surface_travaillee_ha": "Quelle surface avez-vous travaillée en hectares?",
            "intrants": "Quels produits avez-vous utilisés?",
            "conditions_meteo": "Quelles étaient les conditions météo?",
            "materiels": "Quel équipement avez-vous utilisé?"
        }
        return prompts.get(field, f"Pouvez-vous préciser {field}?")
    
    def _generate_voice_confirmation(
        self, 
        confirmation_summary: Dict[str, Any], 
        validation_results: List[ValidationResult]
    ) -> str:
        """Generate voice confirmation text"""
        
        summary = confirmation_summary.get("intervention_summary", {})
        
        # Start with basic confirmation
        confirmation = f"J'ai enregistré votre intervention: {summary.get('type', 'intervention')} "
        confirmation += f"sur la parcelle {summary.get('parcelle', 'non spécifiée')} "
        confirmation += f"le {summary.get('date', 'date non spécifiée')}. "
        
        # Add surface information
        if summary.get('surface'):
            confirmation += f"Surface travaillée: {summary['surface']} hectares. "
        
        # Add products information
        products = confirmation_summary.get("products_used", [])
        if products:
            product_names = [p.get("libelle", "produit") for p in products]
            confirmation += f"Produits utilisés: {', '.join(product_names)}. "
        
        # Add validation results
        errors = [r for r in validation_results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in validation_results if r.level == ValidationLevel.WARNING]
        
        if errors:
            confirmation += f"Attention: {len(errors)} erreur(s) détectée(s). "
            for error in errors[:2]:  # Limit to first 2 errors
                confirmation += f"{error.message}. "
        
        if warnings:
            confirmation += f"{len(warnings)} avertissement(s). "
        
        # Add compliance status
        compliance_status = confirmation_summary.get("compliance_status", "conforme")
        if compliance_status == "conforme":
            confirmation += "L'intervention est conforme aux réglementations. "
        else:
            confirmation += "L'intervention nécessite votre attention. "
        
        # Add confirmation request
        if confirmation_summary.get("requires_confirmation"):
            confirmation += "Confirmez-vous ces informations?"
        else:
            confirmation += "L'intervention a été enregistrée avec succès."
        
        return confirmation
    
    async def process_farmer_confirmation(
        self, 
        intervention_data: Dict[str, Any],
        confirmation_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process farmer's confirmation responses"""
        
        # Update intervention data based on confirmations
        updated_data = intervention_data.copy()
        
        # Process clarifications
        clarifications = confirmation_responses.get("clarifications", {})
        for field, value in clarifications.items():
            updated_data[field] = value
        
        # Process confirmations
        confirmations = confirmation_responses.get("confirmations", {})
        
        # Re-validate with updated data
        final_validation = await self.validate_and_confirm_intervention(updated_data)
        
        return {
            "updated_intervention_data": updated_data,
            "final_validation": final_validation,
            "can_save": final_validation.get("can_proceed", False),
            "confirmation_summary": final_validation.get("confirmation_summary", {})
        }
