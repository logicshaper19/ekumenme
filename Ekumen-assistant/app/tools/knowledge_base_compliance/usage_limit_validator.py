"""
Usage Limit Validator Tool - Enhanced Version
Checks dosages and applications against regulatory limits

Improvements:
1. Better numeric parsing and validation
2. Structured validation results with confidence scores
3. Enhanced limit checking logic
4. Better error handling and recovery
5. More comprehensive compliance checking
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import re

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class UsageLimitValidatorInput(BaseModel):
    """Input for usage limit validation"""
    extracted_entities: Dict[str, Any] = Field(description="Extracted regulatory entities from previous tool")
    ephy_validation_results: Dict[str, Any] = Field(description="Results from EPHY compliance validation")
    document_id: str = Field(description="Document identifier for tracking")
    
    @validator('extracted_entities', 'ephy_validation_results')
    def validate_dicts(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Input must be a dictionary")
        return v


class UsageLimitValidatorTool(BaseTool):
    """
    Tool for checking dosages and applications against regulatory limits
    
    Validation checks:
    - Dosage within EPHY-approved limits
    - Application frequency compliance
    - Seasonal application restrictions
    - Buffer zone requirements (ZNT)
    - Pre-harvest interval compliance (DAR)
    """
    
    name: str = "usage_limit_validator"
    description: str = """
    Validate usage patterns against regulatory limits.
    
    Use this tool AFTER ephy_compliance_validator to check if dosages, frequencies,
    and application patterns comply with regulatory limits and restrictions.
    
    Input: extracted_entities, ephy_validation_results, document_id
    Output: Usage compliance validation results with detailed checks
    """
    args_schema: type = UsageLimitValidatorInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("Usage Limit Validator Tool initialized")
    
    def _run(
        self,
        extracted_entities: Dict[str, Any],
        ephy_validation_results: Dict[str, Any],
        document_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Validate usage patterns against regulatory limits"""
        try:
            logger.info(f"Validating usage limits for document {document_id}")
            
            # Extract usage data
            dosages = extracted_entities.get("dosages", [])
            application_frequencies = extracted_entities.get("application_frequencies", [])
            znt_distances = extracted_entities.get("znt_distances", [])
            dar_periods = extracted_entities.get("dar_periods", [])
            
            logger.info(
                f"Found {len(dosages)} dosages, {len(application_frequencies)} frequencies, "
                f"{len(znt_distances)} ZNT, {len(dar_periods)} DAR"
            )
            
            validation_results = {
                "dosage_validations": [],
                "frequency_validations": [],
                "znt_validations": [],
                "dar_validations": [],
                "violations": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Validate dosages
            for dosage in dosages:
                dosage_result = self._validate_dosage(dosage, ephy_validation_results)
                validation_results["dosage_validations"].append(dosage_result)
                self._collect_issues(dosage_result, validation_results)
            
            # Validate application frequencies
            for frequency in application_frequencies:
                freq_result = self._validate_frequency(frequency, ephy_validation_results)
                validation_results["frequency_validations"].append(freq_result)
                self._collect_issues(freq_result, validation_results)
            
            # Validate ZNT distances
            for znt in znt_distances:
                znt_result = self._validate_znt(znt, ephy_validation_results)
                validation_results["znt_validations"].append(znt_result)
                self._collect_issues(znt_result, validation_results)
            
            # Validate DAR periods
            for dar in dar_periods:
                dar_result = self._validate_dar(dar, ephy_validation_results)
                validation_results["dar_validations"].append(dar_result)
                self._collect_issues(dar_result, validation_results)
            
            # Determine overall compliance status
            compliance_status = self._determine_usage_compliance(validation_results)
            
            logger.info(f"Usage limit validation completed: {compliance_status}")
            
            return {
                "status": "success",
                "compliance_status": compliance_status,
                "validation_results": validation_results,
                "total_dosages_checked": len(dosages),
                "total_frequencies_checked": len(application_frequencies),
                "total_znt_checked": len(znt_distances),
                "total_dar_checked": len(dar_periods),
                "total_violations": len(validation_results["violations"]),
                "total_warnings": len(validation_results["warnings"]),
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error in usage limit validation: {e}", exc_info=True)
            return self._error_response(str(e), document_id)
    
    def _validate_dosage(self, dosage: Dict[str, Any], ephy_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single dosage against regulatory limits"""
        product = dosage.get("product", "")
        amount_str = dosage.get("amount", "")
        unit = dosage.get("unit", "")
        crop = dosage.get("crop", "")
        
        validation_result = {
            "product": product,
            "amount": amount_str,
            "unit": unit,
            "crop": crop,
            "status": "unknown",
            "confidence": 0.5,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check if we have required data
        if not product or not amount_str or not unit:
            validation_result["status"] = "error"
            validation_result["confidence"] = 0.0
            validation_result["violations"].append("Missing required dosage information")
            return validation_result
        
        try:
            # Parse dosage amount (handle various formats)
            amount = self._parse_numeric_value(amount_str)
            
            if amount <= 0:
                validation_result["status"] = "error"
                validation_result["violations"].append(f"Invalid dosage amount: {amount_str}")
                return validation_result
            
            # Check against EPHY limits
            limit_check = self._check_ephy_limit(product, amount, unit, crop)
            
            if limit_check["exceeds"]:
                validation_result["status"] = "non_compliant"
                validation_result["confidence"] = 0.8
                validation_result["violations"].append(
                    f"Dosage {amount} {unit} for '{product}' exceeds EPHY limit "
                    f"of {limit_check['limit']} {unit} for {crop or 'general use'}"
                )
            elif limit_check["approaches"]:
                validation_result["status"] = "compliant_with_warning"
                validation_result["confidence"] = 0.7
                validation_result["warnings"].append(
                    f"Dosage {amount} {unit} for '{product}' approaches EPHY limit "
                    f"of {limit_check['limit']} {unit} (within 10%)"
                )
            else:
                validation_result["status"] = "compliant"
                validation_result["confidence"] = 0.9
            
            # Check for unusual patterns
            if self._has_dosage_issues(amount, unit):
                validation_result["warnings"].append(
                    f"Unusual dosage pattern detected: {amount} {unit}"
                )
                validation_result["recommendations"].append(
                    "Verify dosage calculation and application method"
                )
                validation_result["confidence"] = max(0.5, validation_result["confidence"] - 0.2)
            
        except (ValueError, TypeError) as e:
            validation_result["status"] = "error"
            validation_result["confidence"] = 0.0
            validation_result["violations"].append(f"Invalid dosage amount: {amount_str}")
            validation_result["recommendations"].append("Check dosage format and units")
            logger.warning(f"Failed to parse dosage amount '{amount_str}': {e}")
        
        return validation_result
    
    def _validate_frequency(self, frequency: Dict[str, Any], ephy_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate application frequency against regulatory limits"""
        product = frequency.get("product", "")
        freq_count_str = frequency.get("frequency", "")
        interval = frequency.get("interval", "")
        season = frequency.get("season", "")
        
        validation_result = {
            "product": product,
            "frequency": freq_count_str,
            "interval": interval,
            "season": season,
            "status": "unknown",
            "confidence": 0.5,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        if not product or not freq_count_str:
            validation_result["status"] = "error"
            validation_result["violations"].append("Missing frequency information")
            return validation_result
        
        try:
            # Parse frequency
            freq_value = self._parse_frequency_value(freq_count_str)
            
            if freq_value <= 0:
                validation_result["status"] = "error"
                validation_result["violations"].append(f"Invalid frequency value: {freq_count_str}")
                return validation_result
            
            # Check against EPHY frequency limits
            limit_info = self._get_frequency_limit(product, season)
            
            if limit_info["limit"] and freq_value > limit_info["limit"]:
                validation_result["status"] = "non_compliant"
                validation_result["confidence"] = 0.8
                validation_result["violations"].append(
                    f"Application frequency {freq_value} for '{product}' exceeds "
                    f"EPHY limit of {limit_info['limit']} applications per {season or 'season'}"
                )
            else:
                validation_result["status"] = "compliant"
                validation_result["confidence"] = 0.9
            
            # Check interval compliance
            if interval:
                interval_check = self._check_interval_compliance(product, interval)
                if not interval_check["compliant"]:
                    validation_result["warnings"].append(
                        f"Application interval '{interval}' may not comply with EPHY requirements"
                    )
                    validation_result["recommendations"].append(interval_check["recommendation"])
                    validation_result["confidence"] = max(0.6, validation_result["confidence"] - 0.2)
            
        except (ValueError, TypeError) as e:
            validation_result["status"] = "error"
            validation_result["confidence"] = 0.0
            validation_result["violations"].append(f"Invalid frequency value: {freq_count_str}")
            logger.warning(f"Failed to parse frequency '{freq_count_str}': {e}")
        
        return validation_result
    
    def _validate_znt(self, znt: Dict[str, Any], ephy_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ZNT (Zone de Non Traitement) distances"""
        product = znt.get("product", "")
        distance_str = znt.get("distance", "")
        target = znt.get("target", "")
        
        validation_result = {
            "product": product,
            "distance": distance_str,
            "target": target,
            "status": "unknown",
            "confidence": 0.5,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        if not distance_str:
            validation_result["status"] = "error"
            validation_result["violations"].append("Missing ZNT distance")
            return validation_result
        
        try:
            # Parse distance
            distance = self._parse_numeric_value(distance_str)
            
            if distance < 0:
                validation_result["status"] = "error"
                validation_result["violations"].append(f"Invalid ZNT distance: {distance_str}")
                return validation_result
            
            # Get required ZNT for product and target
            required_znt = self._get_required_znt(product, target)
            
            if required_znt is not None:
                if distance < required_znt:
                    validation_result["status"] = "non_compliant"
                    validation_result["confidence"] = 0.9
                    validation_result["violations"].append(
                        f"ZNT distance {distance}m for '{product}' is less than "
                        f"required {required_znt}m for {target or 'sensitive areas'}"
                    )
                else:
                    validation_result["status"] = "compliant"
                    validation_result["confidence"] = 0.9
            else:
                validation_result["status"] = "unknown"
                validation_result["confidence"] = 0.4
                validation_result["warnings"].append(
                    f"No specific ZNT requirement found for '{product}' and {target}"
                )
                validation_result["recommendations"].append(
                    "Verify ZNT requirements with official EPHY documentation"
                )
            
        except (ValueError, TypeError) as e:
            validation_result["status"] = "error"
            validation_result["confidence"] = 0.0
            validation_result["violations"].append(f"Invalid ZNT distance: {distance_str}")
            logger.warning(f"Failed to parse ZNT distance '{distance_str}': {e}")
        
        return validation_result
    
    def _validate_dar(self, dar: Dict[str, Any], ephy_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DAR (Délai Avant Récolte) periods"""
        product = dar.get("product", "")
        period_str = dar.get("period", "")
        crop = dar.get("crop", "")
        
        validation_result = {
            "product": product,
            "period": period_str,
            "crop": crop,
            "status": "unknown",
            "confidence": 0.5,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        if not period_str:
            validation_result["status"] = "error"
            validation_result["violations"].append("Missing DAR period")
            return validation_result
        
        try:
            # Parse period
            period = self._parse_period_value(period_str)
            
            if period < 0:
                validation_result["status"] = "error"
                validation_result["violations"].append(f"Invalid DAR period: {period_str}")
                return validation_result
            
            # Get required DAR for product and crop
            required_dar = self._get_required_dar(product, crop)
            
            if required_dar is not None:
                if period < required_dar:
                    validation_result["status"] = "non_compliant"
                    validation_result["confidence"] = 0.9
                    validation_result["violations"].append(
                        f"DAR period {period} days for '{product}' is less than "
                        f"required {required_dar} days for {crop or 'this crop'}"
                    )
                else:
                    validation_result["status"] = "compliant"
                    validation_result["confidence"] = 0.9
            else:
                validation_result["status"] = "unknown"
                validation_result["confidence"] = 0.4
                validation_result["warnings"].append(
                    f"No specific DAR requirement found for '{product}' and {crop}"
                )
                validation_result["recommendations"].append(
                    "Verify DAR requirements with official EPHY documentation"
                )
            
        except (ValueError, TypeError) as e:
            validation_result["status"] = "error"
            validation_result["confidence"] = 0.0
            validation_result["violations"].append(f"Invalid DAR period: {period_str}")
            logger.warning(f"Failed to parse DAR period '{period_str}': {e}")
        
        return validation_result
    
    def _parse_numeric_value(self, value_str: str) -> float:
        """Parse numeric value from string (handles comma/dot)"""
        if not value_str:
            raise ValueError("Empty value string")
        
        # Remove whitespace
        cleaned = value_str.strip()
        
        # Replace comma with dot
        cleaned = cleaned.replace(',', '.')
        
        # Extract first numeric value
        match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
        if match:
            return float(match.group(1))
        
        raise ValueError(f"No numeric value found in '{value_str}'")
    
    def _parse_frequency_value(self, freq_str: str) -> int:
        """Parse frequency value from string"""
        if not freq_str:
            raise ValueError("Empty frequency string")
        
        # Try direct integer conversion
        if freq_str.isdigit():
            return int(freq_str)
        
        # Extract first number
        match = re.search(r'(\d+)', freq_str)
        if match:
            return int(match.group(1))
        
        raise ValueError(f"No numeric frequency found in '{freq_str}'")
    
    def _parse_period_value(self, period_str: str) -> int:
        """Parse period value (days) from string"""
        # Same as frequency parsing for now
        return self._parse_frequency_value(period_str)
    
    def _check_ephy_limit(self, product: str, amount: float, unit: str, crop: str) -> Dict[str, Any]:
        """Check dosage against EPHY limits"""
        # Mock limits - in production this would query EPHY database
        limits = {
            "glyphosate": {"L/ha": 3.0, "kg/ha": 4.0},
            "epoxiconazole": {"L/ha": 1.5, "kg/ha": 2.0},
            "azoxystrobine": {"L/ha": 1.0, "kg/ha": 1.5},
            "tebuconazole": {"L/ha": 1.5, "kg/ha": 2.0},
            "propiconazole": {"L/ha": 1.2, "kg/ha": 1.8}
        }
        
        product_lower = product.lower()
        
        for product_key, unit_limits in limits.items():
            if product_key in product_lower:
                limit = unit_limits.get(unit)
                if limit:
                    return {
                        "limit": limit,
                        "exceeds": amount > limit,
                        "approaches": amount > (limit * 0.9),  # Within 10% of limit
                        "found": True
                    }
        
        return {"limit": None, "exceeds": False, "approaches": False, "found": False}
    
    def _get_frequency_limit(self, product: str, season: str) -> Dict[str, Any]:
        """Get frequency limit for product"""
        # Mock limits
        limits = {
            "glyphosate": 2,
            "epoxiconazole": 3,
            "azoxystrobine": 3,
            "tebuconazole": 3,
            "propiconazole": 2
        }
        
        product_lower = product.lower()
        for product_key, limit in limits.items():
            if product_key in product_lower:
                return {"limit": limit, "found": True}
        
        return {"limit": None, "found": False}
    
    def _check_interval_compliance(self, product: str, interval: str) -> Dict[str, Any]:
        """Check if interval complies with requirements"""
        try:
            # Extract days from interval string
            days = self._parse_period_value(interval)
            
            # Flag very short intervals (< 7 days)
            if days < 7:
                return {
                    "compliant": False,
                    "recommendation": f"Minimum 7 days between applications recommended (found {days} days)"
                }
            
            return {"compliant": True, "recommendation": ""}
            
        except (ValueError, TypeError):
            return {
                "compliant": False,
                "recommendation": "Could not parse interval value"
            }
    
    def _get_required_znt(self, product: str, target: str) -> Optional[float]:
        """Get required ZNT distance for product and target"""
        # Mock requirements
        znt_requirements = {
            "glyphosate": {"eau": 5.0, "water": 5.0, "habitation": 5.0, "houses": 5.0},
            "epoxiconazole": {"eau": 5.0, "water": 5.0, "habitation": 5.0, "houses": 5.0},
            "azoxystrobine": {"eau": 5.0, "water": 5.0, "habitation": 5.0, "houses": 5.0}
        }
        
        product_lower = product.lower()
        target_lower = target.lower()
        
        for product_key, target_reqs in znt_requirements.items():
            if product_key in product_lower:
                for target_key, distance in target_reqs.items():
                    if target_key in target_lower:
                        return distance
        
        return None
    
    def _get_required_dar(self, product: str, crop: str) -> Optional[int]:
        """Get required DAR period for product and crop"""
        # Mock requirements
        dar_requirements = {
            "glyphosate": {"blé": 7, "wheat": 7, "maïs": 7, "corn": 7},
            "epoxiconazole": {"blé": 35, "wheat": 35, "orge": 35, "barley": 35},
            "tebuconazole": {"blé": 35, "wheat": 35, "orge": 35, "barley": 35}
        }
        
        product_lower = product.lower()
        crop_lower = crop.lower()
        
        for product_key, crop_reqs in dar_requirements.items():
            if product_key in product_lower:
                for crop_key, period in crop_reqs.items():
                    if crop_key in crop_lower:
                        return period
        
        return None
    
    def _has_dosage_issues(self, amount: float, unit: str) -> bool:
        """Check for unusual dosage patterns"""
        # Flag unusually high or low dosages
        if unit in ["L/ha", "l/ha"]:
            return amount > 5.0 or amount < 0.1
        elif unit in ["kg/ha", "Kg/ha"]:
            return amount > 10.0 or amount < 0.01
        elif unit in ["g/ha", "ml/ha"]:
            return amount > 5000 or amount < 1
        
        return False
    
    def _collect_issues(self, result: Dict[str, Any], validation_results: Dict[str, Any]):
        """Collect violations, warnings, and recommendations from validation result"""
        if result.get("violations"):
            validation_results["violations"].extend(result["violations"])
        if result.get("warnings"):
            validation_results["warnings"].extend(result["warnings"])
        if result.get("recommendations"):
            validation_results["recommendations"].extend(result["recommendations"])
    
    def _determine_usage_compliance(self, validation_results: Dict[str, Any]) -> str:
        """Determine overall usage compliance status"""
        violations = validation_results.get("violations", [])
        warnings = validation_results.get("warnings", [])
        
        if violations:
            return "NON_COMPLIANT"
        elif warnings:
            return "COMPLIANT_WITH_WARNINGS"
        else:
            return "COMPLIANT"
    
    def _error_response(self, error_message: str, document_id: str) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            "status": "error",
            "error": error_message,
            "compliance_status": "UNCERTAIN",
            "validation_results": {
                "dosage_validations": [],
                "frequency_validations": [],
                "znt_validations": [],
                "dar_validations": [],
                "violations": [f"Usage validation failed: {error_message}"],
                "warnings": [],
                "recommendations": ["Manual review required due to validation error"]
            },
            "total_dosages_checked": 0,
            "total_frequencies_checked": 0,
            "total_znt_checked": 0,
            "total_dar_checked": 0,
            "total_violations": 1,
            "total_warnings": 0,
            "document_id": document_id
        }
    
    async def _arun(
        self,
        extracted_entities: Dict[str, Any],
        ephy_validation_results: Dict[str, Any],
        document_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version of the tool"""
        return self._run(extracted_entities, ephy_validation_results, document_id, **kwargs)