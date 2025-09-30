"""
Enhanced Check Regulatory Compliance Tool with Pydantic schemas and caching.

Improvements:
- Type-safe Pydantic schemas
- Redis + memory caching (2h TTL for regulatory data)
- Structured error handling
- Configuration-based compliance rules
- Detailed compliance scoring
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import ValidationError
from langchain.tools import StructuredTool

from app.tools.schemas.compliance_schemas import (
    ComplianceInput,
    ComplianceOutput,
    ComplianceCheckDetail,
    OverallCompliance,
    ComplianceStatus,
    RegulationType,
    PracticeType
)
# Exceptions are handled via Pydantic ValidationError and generic Exception
from app.core.cache import redis_cache
from app.services.configuration_service import ConfigurationService

logger = logging.getLogger(__name__)


class EnhancedComplianceService:
    """Service for checking regulatory compliance with caching"""
    
    def __init__(self):
        self.config_service = ConfigurationService()
    
    @redis_cache(ttl=7200, model_class=ComplianceOutput, category="regulatory")
    async def check_compliance(
        self,
        practice_type: str,
        products_used: Optional[List[str]] = None,
        location: Optional[str] = None,
        timing: Optional[str] = None,
        weather_conditions: Optional[Dict[str, Any]] = None,
        equipment_available: Optional[List[str]] = None,
        crop_type: Optional[str] = None,
        field_size_ha: Optional[float] = None
    ) -> ComplianceOutput:
        """
        Check regulatory compliance for agricultural practices.
        
        Args:
            practice_type: Type of practice (spraying, fertilization, etc.)
            products_used: List of products used
            location: Location of the practice
            timing: Timing of the practice
            weather_conditions: Current weather conditions
            equipment_available: Available equipment
            crop_type: Type of crop
            field_size_ha: Field size in hectares
            
        Returns:
            ComplianceOutput with detailed compliance analysis
        """
        try:
            # Validate input
            input_data = ComplianceInput(
                practice_type=PracticeType(practice_type),
                products_used=products_used,
                location=location,
                timing=timing,
                weather_conditions=weather_conditions,
                equipment_available=equipment_available,
                crop_type=crop_type,
                field_size_ha=field_size_ha
            )
            
            # Get compliance rules from configuration
            compliance_rules = self._get_compliance_rules(practice_type)
            
            if not compliance_rules:
                return ComplianceOutput(
                    success=True,
                    practice_type=practice_type,
                    products_used=products_used or [],
                    location=location,
                    timing=timing,
                    compliance_checks=[],
                    overall_compliance=OverallCompliance(
                        score=1.0,
                        status=ComplianceStatus.UNKNOWN,
                        total_checks=0,
                        passed_checks=0,
                        failed_checks=0,
                        warning_checks=0
                    ),
                    compliance_recommendations=["Aucune règle de conformité trouvée pour cette pratique"],
                    total_checks=0
                )
            
            # Perform compliance checks
            compliance_checks = []
            
            # Check product compliance
            if products_used:
                product_check = self._check_product_compliance(
                    products_used, compliance_rules
                )
                compliance_checks.append(product_check)
            
            # Check timing compliance
            if timing:
                timing_check = self._check_timing_compliance(
                    timing, compliance_rules
                )
                compliance_checks.append(timing_check)
            
            # Check equipment compliance
            if equipment_available is not None:
                equipment_check = self._check_equipment_compliance(
                    equipment_available, compliance_rules
                )
                compliance_checks.append(equipment_check)
            
            # Check environmental compliance
            if weather_conditions:
                env_check = self._check_environmental_compliance(
                    weather_conditions, practice_type, compliance_rules
                )
                compliance_checks.append(env_check)
            
            # Calculate overall compliance
            overall_compliance = self._calculate_overall_compliance(compliance_checks)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(compliance_checks)
            
            # Extract critical violations and warnings
            critical_violations = []
            warnings = []
            total_penalties = 0.0
            
            for check in compliance_checks:
                if check.compliance_status == ComplianceStatus.NON_COMPLIANT:
                    critical_violations.extend(check.violations)
                    # Extract penalty amounts
                    for penalty in check.penalties:
                        if "€" in penalty:
                            try:
                                amount = float(penalty.split(":")[1].strip().replace("€", "").replace(",", ""))
                                total_penalties += amount
                            except:
                                pass
                elif check.compliance_status == ComplianceStatus.WARNING:
                    warnings.extend(check.violations)
            
            return ComplianceOutput(
                success=True,
                practice_type=practice_type,
                products_used=products_used or [],
                location=location,
                timing=timing,
                compliance_checks=compliance_checks,
                overall_compliance=overall_compliance,
                compliance_recommendations=recommendations,
                critical_violations=critical_violations,
                warnings=warnings,
                total_checks=len(compliance_checks),
                total_penalties_eur=total_penalties if total_penalties > 0 else None
            )
            
        except ValidationError as e:
            logger.error(f"Validation error in compliance check: {e}")
            return ComplianceOutput(
                success=False,
                practice_type=practice_type,
                products_used=products_used or [],
                location=location,
                timing=timing,
                compliance_checks=[],
                total_checks=0,
                error=f"Erreur de validation: {str(e)}",
                error_type="validation"
            )
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return ComplianceOutput(
                success=False,
                practice_type=practice_type,
                products_used=products_used or [],
                location=location,
                timing=timing,
                compliance_checks=[],
                total_checks=0,
                error=f"Erreur lors de la vérification de conformité: {str(e)}",
                error_type="unknown"
            )
    
    def _get_compliance_rules(self, practice_type: str) -> Dict[str, Any]:
        """Get compliance rules from configuration"""
        try:
            config = self.config_service.get_config("compliance_rules_config")
            practice_rules = config.get("practice_rules", {})
            return practice_rules.get(practice_type, {})
        except Exception as e:
            logger.warning(f"Failed to load compliance rules: {e}")
            return self._get_fallback_rules(practice_type)
    
    def _get_fallback_rules(self, practice_type: str) -> Dict[str, Any]:
        """Fallback compliance rules"""
        if practice_type == "spraying":
            return {
                "environmental_limits": {
                    "wind_speed_limit": {"value": 20, "unit": "km/h"},
                    "temperature_limit": {"value": 25, "unit": "°C"},
                    "humidity_limit": {"value": 80, "unit": "%"},
                    "znt_distance": {"value": 5, "unit": "meters"}
                },
                "required_equipment": ["EPI", "pulvérisateur_contrôlé"],
                "restricted_products": ["glyphosate", "néonicotinoïdes"],
                "timing_restrictions": ["interdiction_nuit", "interdiction_weekend"]
            }
        return {}
    
    def _check_product_compliance(
        self, products_used: List[str], rules: Dict[str, Any]
    ) -> ComplianceCheckDetail:
        """Check product compliance"""
        violations = []
        recommendations = []
        penalties = []
        
        restricted_products = rules.get("restricted_products", [])
        
        for product in products_used:
            if product.lower() in [p.lower() for p in restricted_products]:
                violations.append(f"Produit restreint utilisé: {product}")
                penalties.append("Amende: 1500€")
                recommendations.append(f"Remplacer {product} par un produit autorisé")
        
        compliance_score = 1.0 - (len(violations) / max(len(products_used), 1))
        
        return ComplianceCheckDetail(
            regulation_type=RegulationType.PRODUCT_COMPLIANCE,
            compliance_status=ComplianceStatus.COMPLIANT if compliance_score > 0.8 else ComplianceStatus.NON_COMPLIANT,
            compliance_score=round(compliance_score, 2),
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )

    def _check_timing_compliance(
        self, timing: str, rules: Dict[str, Any]
    ) -> ComplianceCheckDetail:
        """Check timing compliance"""
        violations = []
        recommendations = []
        penalties = []

        timing_restrictions = rules.get("timing_restrictions", [])

        timing_lower = timing.lower()
        for restriction in timing_restrictions:
            if restriction.lower() in timing_lower:
                violations.append(f"Pratique interdite: {restriction}")
                penalties.append("Amende: 1000€")
                recommendations.append("Reporter la pratique à un moment autorisé")

        compliance_score = 1.0 - (len(violations) / max(len(timing_restrictions), 1))

        return ComplianceCheckDetail(
            regulation_type=RegulationType.TIMING_COMPLIANCE,
            compliance_status=ComplianceStatus.COMPLIANT if compliance_score > 0.8 else ComplianceStatus.NON_COMPLIANT,
            compliance_score=round(compliance_score, 2),
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )

    def _check_equipment_compliance(
        self, equipment_available: List[str], rules: Dict[str, Any]
    ) -> ComplianceCheckDetail:
        """Check equipment compliance"""
        violations = []
        recommendations = []
        penalties = []

        required_equipment = rules.get("required_equipment", [])

        # Check for missing equipment
        equipment_lower = [e.lower() for e in equipment_available]
        for required in required_equipment:
            if required.lower() not in equipment_lower:
                violations.append(f"Équipement manquant: {required}")
                penalties.append("Amende: 500€")
                recommendations.append(f"Acquérir l'équipement requis: {required}")

        compliance_score = 1.0 - (len(violations) / max(len(required_equipment), 1))

        return ComplianceCheckDetail(
            regulation_type=RegulationType.EQUIPMENT_COMPLIANCE,
            compliance_status=ComplianceStatus.COMPLIANT if compliance_score > 0.8 else ComplianceStatus.NON_COMPLIANT,
            compliance_score=round(compliance_score, 2),
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )

    def _check_environmental_compliance(
        self, weather_conditions: Dict[str, Any], practice_type: str, rules: Dict[str, Any]
    ) -> ComplianceCheckDetail:
        """Check environmental compliance"""
        violations = []
        recommendations = []
        penalties = []

        env_limits = rules.get("environmental_limits", {})

        # Check wind speed
        if "wind_speed" in weather_conditions:
            wind_limit_data = env_limits.get("wind_speed_limit", {})
            wind_limit = wind_limit_data.get("value", 20) if isinstance(wind_limit_data, dict) else wind_limit_data

            if weather_conditions["wind_speed"] > wind_limit:
                violations.append(f"Vitesse du vent excessive: {weather_conditions['wind_speed']} km/h (limite: {wind_limit} km/h)")
                penalties.append("Amende: 800€")
                recommendations.append("Reporter l'application à des conditions favorables")
            elif weather_conditions["wind_speed"] > wind_limit * 0.9:
                violations.append(f"Vitesse du vent proche de la limite: {weather_conditions['wind_speed']} km/h")
                recommendations.append("Surveiller les conditions météo")

        # Check temperature
        if "temperature" in weather_conditions:
            temp_limit_data = env_limits.get("temperature_limit", {})
            temp_limit = temp_limit_data.get("value", 25) if isinstance(temp_limit_data, dict) else temp_limit_data

            if weather_conditions["temperature"] > temp_limit:
                violations.append(f"Température excessive: {weather_conditions['temperature']}°C (limite: {temp_limit}°C)")
                penalties.append("Amende: 600€")
                recommendations.append("Reporter l'application à des températures plus basses")

        # Check humidity
        if "humidity" in weather_conditions:
            humidity_limit_data = env_limits.get("humidity_limit", {})
            humidity_limit = humidity_limit_data.get("value", 80) if isinstance(humidity_limit_data, dict) else humidity_limit_data

            if weather_conditions["humidity"] > humidity_limit:
                violations.append(f"Humidité excessive: {weather_conditions['humidity']}% (limite: {humidity_limit}%)")
                recommendations.append("Attendre des conditions moins humides")

        # Calculate score based on number of environmental factors
        total_factors = 3  # wind, temp, humidity
        compliance_score = 1.0 - (len([v for v in violations if "Amende" in str(penalties)]) / total_factors)

        # Determine status
        if len([p for p in penalties if "Amende" in p]) > 0:
            status = ComplianceStatus.NON_COMPLIANT
        elif len(violations) > 0:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.COMPLIANT

        return ComplianceCheckDetail(
            regulation_type=RegulationType.ENVIRONMENTAL_COMPLIANCE,
            compliance_status=status,
            compliance_score=round(compliance_score, 2),
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )

    def _calculate_overall_compliance(
        self, compliance_checks: List[ComplianceCheckDetail]
    ) -> OverallCompliance:
        """Calculate overall compliance score"""
        if not compliance_checks:
            return OverallCompliance(
                score=0.0,
                status=ComplianceStatus.UNKNOWN,
                total_checks=0,
                passed_checks=0,
                failed_checks=0,
                warning_checks=0
            )

        total_score = sum(check.compliance_score for check in compliance_checks)
        average_score = total_score / len(compliance_checks)

        # Count check results
        passed = sum(1 for c in compliance_checks if c.compliance_status == ComplianceStatus.COMPLIANT)
        failed = sum(1 for c in compliance_checks if c.compliance_status == ComplianceStatus.NON_COMPLIANT)
        warnings = sum(1 for c in compliance_checks if c.compliance_status == ComplianceStatus.WARNING)

        # Determine overall status
        if average_score > 0.8 and failed == 0:
            status = ComplianceStatus.COMPLIANT
        elif average_score > 0.6 or failed <= 1:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT

        return OverallCompliance(
            score=round(average_score, 2),
            status=status,
            total_checks=len(compliance_checks),
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings
        )

    def _generate_recommendations(
        self, compliance_checks: List[ComplianceCheckDetail]
    ) -> List[str]:
        """Generate overall compliance recommendations"""
        recommendations = []

        for check in compliance_checks:
            if check.compliance_status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.WARNING]:
                recommendations.extend(check.recommendations)

        if not recommendations:
            recommendations.append("Pratique conforme aux réglementations")

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations


# Create service instance
_compliance_service = EnhancedComplianceService()


# Async wrapper function
async def check_regulatory_compliance_async(
    practice_type: str,
    products_used: Optional[List[str]] = None,
    location: Optional[str] = None,
    timing: Optional[str] = None,
    weather_conditions: Optional[Dict[str, Any]] = None,
    equipment_available: Optional[List[str]] = None,
    crop_type: Optional[str] = None,
    field_size_ha: Optional[float] = None
) -> str:
    """
    Check regulatory compliance for agricultural practices.

    Args:
        practice_type: Type of practice (spraying, fertilization, irrigation, etc.)
        products_used: List of products used (names or AMM codes)
        location: Location of the practice
        timing: Timing of the practice (date/time)
        weather_conditions: Current weather conditions (wind, temp, humidity)
        equipment_available: List of available equipment
        crop_type: Type of crop being treated
        field_size_ha: Field size in hectares

    Returns:
        JSON string with compliance analysis
    """
    result = await _compliance_service.check_compliance(
        practice_type=practice_type,
        products_used=products_used,
        location=location,
        timing=timing,
        weather_conditions=weather_conditions,
        equipment_available=equipment_available,
        crop_type=crop_type,
        field_size_ha=field_size_ha
    )
    return result.model_dump_json()


# Create LangChain tool
check_regulatory_compliance_tool = StructuredTool.from_function(
    coroutine=check_regulatory_compliance_async,
    name="check_regulatory_compliance",
    description=(
        "Vérifie la conformité réglementaire des pratiques agricoles. "
        "Analyse les produits utilisés, les conditions météo, l'équipement, "
        "et les restrictions temporelles. Retourne un score de conformité "
        "avec violations, recommandations et pénalités potentielles."
    ),
    handle_validation_error=False
)

