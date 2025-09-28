"""
Check Regulatory Compliance Tool - Single Purpose Tool

Job: Check regulatory compliance for agricultural practices and products.
Input: practice_type, products_used, location, timing
Output: JSON string with compliance analysis

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
import os
from dataclasses import dataclass, asdict

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

class CheckRegulatoryComplianceTool(BaseTool):
    """
    Tool: Check regulatory compliance for agricultural practices and products.
    
    Job: Take agricultural practices and check regulatory compliance.
    Input: practice_type, products_used, location, timing
    Output: JSON string with compliance analysis
    """
    
    name: str = "check_regulatory_compliance_tool"
    description: str = "Vérifie la conformité réglementaire des pratiques agricoles à partir de la configuration"

    @property
    def config(self):
        """Load compliance rules configuration."""
        if not hasattr(self, '_config'):
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'compliance_rules_config.json')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load compliance rules config: {e}")
                self._config = self._get_fallback_config()
        return self._config
    
    def _run(
        self,
        practice_type: str,
        products_used: List[str] = None,
        location: str = None,
        timing: str = None,
        **kwargs
    ) -> str:
        """
        Check regulatory compliance for agricultural practices and products.
        
        Args:
            practice_type: Type of agricultural practice (spraying, fertilization, etc.)
            products_used: List of products used
            location: Location of the practice
            timing: Timing of the practice
        """
        try:
            # Get regulatory database
            regulatory_database = self._get_regulatory_database()
            
            # Check compliance
            compliance_checks = self._check_compliance(practice_type, products_used or [], location, timing, regulatory_database)
            
            # Calculate overall compliance score
            overall_compliance = self._calculate_overall_compliance(compliance_checks)
            
            # Generate compliance recommendations
            compliance_recommendations = self._generate_compliance_recommendations(compliance_checks)
            
            result = {
                "practice_type": practice_type,
                "products_used": products_used or [],
                "location": location,
                "timing": timing,
                "compliance_checks": [asdict(check) for check in compliance_checks],
                "overall_compliance": overall_compliance,
                "compliance_recommendations": compliance_recommendations,
                "total_checks": len(compliance_checks)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Check regulatory compliance error: {e}")
            return json.dumps({"error": f"Erreur lors de la vérification de conformité: {str(e)}"})
    
    def _get_regulatory_database(self) -> Dict[str, Any]:
        """Get regulatory database with compliance rules from configuration."""
        # Get practice rules from configuration
        practice_rules = self.config.get("practice_rules", {})

        # Convert configuration format to legacy format for compatibility
        regulatory_database = {}

        for practice_type, rules in practice_rules.items():
            converted_rules = {}

            # Convert environmental limits
            env_limits = rules.get("environmental_limits", {})
            for limit_name, limit_data in env_limits.items():
                if isinstance(limit_data, dict) and "value" in limit_data:
                    converted_rules[limit_name] = limit_data["value"]
                else:
                    converted_rules[limit_name] = limit_data

            # Copy other rule types directly
            for rule_type in ["required_equipment", "restricted_products", "timing_restrictions"]:
                if rule_type in rules:
                    converted_rules[rule_type] = rules[rule_type]

            # Handle application_timing (for fertilization)
            if "application_timing" in rules:
                converted_rules["application_timing"] = rules["application_timing"]

            regulatory_database[practice_type] = converted_rules

        return regulatory_database if regulatory_database else self._get_fallback_regulatory_database()

    def _get_fallback_config(self) -> Dict[str, Any]:
        """Fallback configuration if config file cannot be loaded."""
        return {
            "practice_rules": {
                "spraying": {
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
            }
        }

    def _get_fallback_regulatory_database(self) -> Dict[str, Any]:
        """Fallback regulatory database when configuration is not available."""
        return {
            "spraying": {
                "wind_speed_limit": 20,
                "temperature_limit": 25,
                "humidity_limit": 80,
                "znt_distance": 5,
                "required_equipment": ["EPI", "pulvérisateur_contrôlé"],
                "restricted_products": ["glyphosate", "néonicotinoïdes"],
                "timing_restrictions": ["interdiction_nuit", "interdiction_weekend"]
            }
        }
    
    def _check_compliance(self, practice_type: str, products_used: List[str], location: str, timing: str, regulatory_database: Dict[str, Any]) -> List[ComplianceCheck]:
        """Check compliance for specific practice."""
        compliance_checks = []
        
        if practice_type not in regulatory_database:
            return compliance_checks
        
        practice_rules = regulatory_database[practice_type]
        
        # Check product compliance
        product_compliance = self._check_product_compliance(products_used, practice_rules)
        compliance_checks.append(product_compliance)
        
        # Check timing compliance
        timing_compliance = self._check_timing_compliance(timing, practice_rules)
        compliance_checks.append(timing_compliance)
        
        # Check equipment compliance
        equipment_compliance = self._check_equipment_compliance(practice_type, practice_rules)
        compliance_checks.append(equipment_compliance)
        
        # Check environmental compliance
        environmental_compliance = self._check_environmental_compliance(practice_type, practice_rules)
        compliance_checks.append(environmental_compliance)
        
        return compliance_checks
    
    def _check_product_compliance(self, products_used: List[str], practice_rules: Dict[str, Any]) -> ComplianceCheck:
        """Check product compliance."""
        violations = []
        recommendations = []
        penalties = []
        
        restricted_products = practice_rules.get("restricted_products", [])
        
        for product in products_used:
            if product.lower() in [p.lower() for p in restricted_products]:
                violations.append(f"Produit restreint utilisé: {product}")
                penalties.append("Amende: 1500€")
                recommendations.append(f"Remplacer {product} par un produit autorisé")
        
        compliance_score = 1.0 - (len(violations) / max(len(products_used), 1))
        
        return ComplianceCheck(
            regulation_type="product_compliance",
            compliance_status="compliant" if compliance_score > 0.8 else "non_compliant",
            compliance_score=round(compliance_score, 2),
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )
    
    def _check_timing_compliance(self, timing: str, practice_rules: Dict[str, Any]) -> ComplianceCheck:
        """Check timing compliance."""
        violations = []
        recommendations = []
        penalties = []
        
        timing_restrictions = practice_rules.get("timing_restrictions", [])
        
        if timing:
            timing_lower = timing.lower()
            for restriction in timing_restrictions:
                if restriction.lower() in timing_lower:
                    violations.append(f"Pratique interdite: {restriction}")
                    penalties.append("Amende: 1000€")
                    recommendations.append(f"Reporter la pratique à un moment autorisé")
        
        compliance_score = 1.0 - (len(violations) / max(len(timing_restrictions), 1))
        
        return ComplianceCheck(
            regulation_type="timing_compliance",
            compliance_status="compliant" if compliance_score > 0.8 else "non_compliant",
            compliance_score=round(compliance_score, 2),
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )
    
    def _check_equipment_compliance(self, practice_type: str, practice_rules: Dict[str, Any]) -> ComplianceCheck:
        """Check equipment compliance."""
        violations = []
        recommendations = []
        penalties = []
        
        required_equipment = practice_rules.get("required_equipment", [])
        
        # Simulate equipment check (in real implementation, would check actual equipment)
        missing_equipment = ["EPI"]  # Example missing equipment
        
        for equipment in missing_equipment:
            if equipment in required_equipment:
                violations.append(f"Équipement manquant: {equipment}")
                penalties.append("Amende: 500€")
                recommendations.append(f"Acquérir l'équipement requis: {equipment}")
        
        compliance_score = 1.0 - (len(violations) / max(len(required_equipment), 1))
        
        return ComplianceCheck(
            regulation_type="equipment_compliance",
            compliance_status="compliant" if compliance_score > 0.8 else "non_compliant",
            compliance_score=round(compliance_score, 2),
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )
    
    def _check_environmental_compliance(self, practice_type: str, practice_rules: Dict[str, Any]) -> ComplianceCheck:
        """Check environmental compliance."""
        violations = []
        recommendations = []
        penalties = []
        
        # Simulate environmental conditions check
        environmental_conditions = {
            "wind_speed": 25,  # km/h
            "temperature": 30,  # °C
            "humidity": 85  # %
        }
        
        if practice_type == "spraying":
            if environmental_conditions["wind_speed"] > practice_rules.get("wind_speed_limit", 20):
                violations.append("Vitesse du vent excessive")
                penalties.append("Amende: 800€")
                recommendations.append("Reporter l'application à des conditions favorables")
            
            if environmental_conditions["temperature"] > practice_rules.get("temperature_limit", 25):
                violations.append("Température excessive")
                penalties.append("Amende: 600€")
                recommendations.append("Reporter l'application à des températures plus basses")
        
        compliance_score = 1.0 - (len(violations) / 3)  # 3 environmental factors
        
        return ComplianceCheck(
            regulation_type="environmental_compliance",
            compliance_status="compliant" if compliance_score > 0.8 else "non_compliant",
            compliance_score=round(compliance_score, 2),
            violations=violations,
            recommendations=recommendations,
            penalties=penalties
        )
    
    def _calculate_overall_compliance(self, compliance_checks: List[ComplianceCheck]) -> Dict[str, Any]:
        """Calculate overall compliance score."""
        if not compliance_checks:
            return {"score": 0.0, "status": "unknown"}
        
        total_score = sum(check.compliance_score for check in compliance_checks)
        average_score = total_score / len(compliance_checks)
        
        if average_score > 0.8:
            status = "compliant"
        elif average_score > 0.6:
            status = "partially_compliant"
        else:
            status = "non_compliant"
        
        return {
            "score": round(average_score, 2),
            "status": status
        }
    
    def _generate_compliance_recommendations(self, compliance_checks: List[ComplianceCheck]) -> List[str]:
        """Generate overall compliance recommendations."""
        recommendations = []
        
        for check in compliance_checks:
            if check.compliance_status == "non_compliant":
                recommendations.extend(check.recommendations)
        
        if not recommendations:
            recommendations.append("Pratique conforme aux réglementations")
        
        return recommendations
