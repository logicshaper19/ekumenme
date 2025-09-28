"""
Check Regulatory Compliance Tool - Vector Database Ready Tool

Job: Check regulatory compliance for agricultural practices and products.
Input: practice_type, products_used, location, timing
Output: JSON string with compliance analysis

Enhanced Features:
- External knowledge base (JSON file)
- Configurable analysis parameters
- Asynchronous support
- Comprehensive input validation
- Vector database ready architecture

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

# Import configuration system
from ...config.regulatory_compliance_config import get_regulatory_compliance_config

logger = logging.getLogger(__name__)

@dataclass
class ComplianceCheck:
    """Structured compliance check result."""
    regulation_type: str
    compliance_status: str
    compliance_score: float
    violations: List[str]
    recommendations: List[str]
    penalties: List[str]

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class CheckRegulatoryComplianceTool(BaseTool):
    """
    Vector Database Ready Tool: Check regulatory compliance for agricultural practices and products.
    
    Job: Take agricultural practices and check regulatory compliance.
    Input: practice_type, products_used, location, timing
    Output: JSON string with compliance analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "check_regulatory_compliance_tool"
    description: str = "Vérifie la conformité réglementaire avec analyse avancée"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self._config_cache = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "regulatory_compliance_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_regulatory_compliance_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading regulatory compliance knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        practice_type: str,
        products_used: Optional[List[str]] = None,
        location: Optional[str] = None,
        timing: Optional[str] = None
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate practice type
        if config.require_practice_type and not practice_type:
            errors.append(ValidationError("practice_type", "Practice type is required", "error"))
        
        # Validate products if provided
        if config.validate_products and products_used:
            if not isinstance(products_used, list):
                errors.append(ValidationError("products_used", "Products must be a list", "error"))
            elif len(products_used) == 0:
                errors.append(ValidationError("products_used", "Products list cannot be empty", "warning"))
        
        # Validate location if provided
        if config.validate_location and location:
            if len(location.strip()) < 2:
                errors.append(ValidationError("location", "Location must be at least 2 characters", "warning"))
        
        # Validate timing if provided
        if config.validate_timing and timing:
            if len(timing.strip()) < 2:
                errors.append(ValidationError("timing", "Timing must be at least 2 characters", "warning"))
        
        return errors
    
    def _check_amm_compliance(
        self, 
        products_used: List[str], 
        knowledge_base: Dict[str, Any]
    ) -> ComplianceCheck:
        """Check AMM compliance for products used."""
        regulations = knowledge_base.get("regulations", {})
        amm_regulation = regulations.get("amm_compliance", {})
        
        violations = []
        recommendations = []
        penalties = []
        
        # Check each product
        for product in products_used:
            # Simulate AMM check (in real implementation, would query AMM database)
            if "amm" not in product.lower() and "authorized" not in product.lower():
                violations.append(f"Produit {product} sans numéro AMM valide")
                recommendations.append(f"Vérifier l'autorisation AMM pour {product}")
                penalties.extend(amm_regulation.get("penalties", []))
        
        # Calculate compliance score
        total_checks = len(products_used) if products_used else 1
        violation_count = len(violations)
        compliance_score = max(0, ((total_checks - violation_count) / total_checks) * 100)
        
        return ComplianceCheck(
            regulation_type="AMM",
            compliance_status="compliant" if compliance_score >= 80 else "non_compliant",
            compliance_score=compliance_score,
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )
    
    def _check_znt_compliance(
        self, 
        location: str, 
        practice_type: str, 
        knowledge_base: Dict[str, Any]
    ) -> ComplianceCheck:
        """Check ZNT compliance for location and practice."""
        regulations = knowledge_base.get("regulations", {})
        znt_regulation = regulations.get("znt_compliance", {})
        
        violations = []
        recommendations = []
        penalties = []
        
        # Check ZNT requirements based on practice type
        if practice_type.lower() in ["pesticide", "herbicide", "fungicide"]:
            if "river" in location.lower() or "stream" in location.lower():
                violations.append("Traitement trop proche d'un cours d'eau")
                recommendations.append("Respecter la distance minimale de 5m des cours d'eau")
                penalties.extend(znt_regulation.get("penalties", []))
            
            if "house" in location.lower() or "residential" in location.lower():
                violations.append("Traitement trop proche d'habitations")
                recommendations.append("Respecter la distance minimale de 20m des habitations")
                penalties.extend(znt_regulation.get("penalties", []))
        
        # Calculate compliance score
        compliance_score = 100 if not violations else max(0, 100 - (len(violations) * 25))
        
        return ComplianceCheck(
            regulation_type="ZNT",
            compliance_status="compliant" if compliance_score >= 80 else "non_compliant",
            compliance_score=compliance_score,
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )
    
    def _check_timing_compliance(
        self, 
        timing: str, 
        practice_type: str, 
        knowledge_base: Dict[str, Any]
    ) -> ComplianceCheck:
        """Check timing compliance for practice."""
        regulations = knowledge_base.get("regulations", {})
        timing_regulation = regulations.get("timing_compliance", {})
        
        violations = []
        recommendations = []
        penalties = []
        
        # Check timing requirements
        if practice_type.lower() in ["pesticide", "herbicide"]:
            if "harvest" in timing.lower() and "immediate" in timing.lower():
                violations.append("Délai avant récolte non respecté")
                recommendations.append("Respecter le délai minimum de 7 jours avant récolte")
                penalties.extend(timing_regulation.get("penalties", []))
            
            if "rain" in timing.lower() or "windy" in timing.lower():
                violations.append("Conditions météo défavorables")
                recommendations.append("Reporter l'application en cas de pluie ou vent fort")
                penalties.extend(timing_regulation.get("penalties", []))
        
        # Calculate compliance score
        compliance_score = 100 if not violations else max(0, 100 - (len(violations) * 30))
        
        return ComplianceCheck(
            regulation_type="Timing",
            compliance_status="compliant" if compliance_score >= 80 else "non_compliant",
            compliance_score=compliance_score,
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )
    
    def _check_equipment_compliance(
        self, 
        practice_type: str, 
        knowledge_base: Dict[str, Any]
    ) -> ComplianceCheck:
        """Check equipment compliance for practice."""
        regulations = knowledge_base.get("regulations", {})
        equipment_regulation = regulations.get("equipment_compliance", {})
        
        violations = []
        recommendations = []
        penalties = []
        
        # Check equipment requirements
        if practice_type.lower() in ["pesticide", "herbicide", "fungicide"]:
            violations.append("Vérification de l'équipement de protection requis")
            recommendations.append("Utiliser des équipements de protection individuelle homologués")
            recommendations.append("Vérifier le bon état du matériel d'application")
            penalties.extend(equipment_regulation.get("penalties", []))
        
        # Calculate compliance score (assume compliant if no specific violations)
        compliance_score = 85  # Default score for equipment compliance
        
        return ComplianceCheck(
            regulation_type="Equipment",
            compliance_status="compliant" if compliance_score >= 80 else "non_compliant",
            compliance_score=compliance_score,
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )
    
    def _calculate_overall_compliance(
        self, 
        compliance_checks: List[ComplianceCheck], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall compliance score and status."""
        if not compliance_checks:
            return {"overall_score": 0, "overall_status": "unknown", "compliance_level": "non_compliant"}
        
        # Calculate weighted average
        total_score = sum(check.compliance_score for check in compliance_checks)
        overall_score = total_score / len(compliance_checks)
        
        # Determine compliance level
        compliance_levels = knowledge_base.get("compliance_levels", {})
        compliance_level = "non_compliant"
        
        for level, info in compliance_levels.items():
            score_range = info.get("score_range", [0, 100])
            if score_range[0] <= overall_score <= score_range[1]:
                compliance_level = level
                break
        
        # Determine overall status
        overall_status = "compliant" if overall_score >= 80 else "non_compliant"
        
        return {
            "overall_score": round(overall_score, 2),
            "overall_status": overall_status,
            "compliance_level": compliance_level,
            "compliance_description": compliance_levels.get(compliance_level, {}).get("description", "")
        }
    
    def _run(
        self,
        practice_type: str,
        products_used: Optional[List[str]] = None,
        location: Optional[str] = None,
        timing: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Check regulatory compliance for agricultural practices and products.
        
        Args:
            practice_type: Type of agricultural practice (pesticide, herbicide, etc.)
            products_used: List of products used (optional)
            location: Location of practice (optional)
            timing: Timing of practice (optional)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(practice_type, products_used, location, timing)
            config = self._get_config()
            
            if validation_errors and config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Load knowledge base
            knowledge_base = self._load_knowledge_base()
            
            # Perform compliance checks
            compliance_checks = []
            
            if config.include_amm_check and products_used:
                amm_check = self._check_amm_compliance(products_used, knowledge_base)
                compliance_checks.append(amm_check)
            
            if config.include_znt_check and location:
                znt_check = self._check_znt_compliance(location, practice_type, knowledge_base)
                compliance_checks.append(znt_check)
            
            if config.include_timing_check and timing:
                timing_check = self._check_timing_compliance(timing, practice_type, knowledge_base)
                compliance_checks.append(timing_check)
            
            if config.include_equipment_check:
                equipment_check = self._check_equipment_compliance(practice_type, knowledge_base)
                compliance_checks.append(equipment_check)
            
            # Calculate overall compliance
            overall_compliance = self._calculate_overall_compliance(compliance_checks, knowledge_base)
            
            # Aggregate all violations and recommendations
            all_violations = []
            all_recommendations = []
            all_penalties = []
            
            for check in compliance_checks:
                all_violations.extend(check.violations)
                all_recommendations.extend(check.recommendations)
                all_penalties.extend(check.penalties)
            
            result = {
                "compliance_analysis": {
                    "practice_type": practice_type,
                    "products_used": products_used or [],
                    "location": location,
                    "timing": timing,
                    "overall_compliance": overall_compliance,
                    "detailed_checks": [asdict(check) for check in compliance_checks]
                },
                "violations_summary": {
                    "total_violations": len(all_violations),
                    "violations": all_violations,
                    "recommendations": all_recommendations,
                    "potential_penalties": list(set(all_penalties))
                },
                "summary": {
                    "compliance_score": overall_compliance["overall_score"],
                    "compliance_status": overall_compliance["overall_status"],
                    "compliance_level": overall_compliance["compliance_level"],
                    "checks_performed": len(compliance_checks)
                },
                "analysis_metadata": {
                    "config_used": asdict(config),
                    "knowledge_base_version": knowledge_base.get("metadata", {}).get("version", "unknown")
                }
            }
            
            # Add validation warnings if any
            if validation_errors and config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Check regulatory compliance error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la vérification de conformité réglementaire: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        practice_type: str,
        products_used: Optional[List[str]] = None,
        location: Optional[str] = None,
        timing: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of regulatory compliance checking.
        """
        # For now, just call the sync version
        return self._run(practice_type, products_used, location, timing, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
