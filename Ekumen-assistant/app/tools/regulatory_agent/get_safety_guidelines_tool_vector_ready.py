"""
Get Safety Guidelines Tool - Vector Database Ready Tool

Job: Get safety guidelines for agricultural products and practices.
Input: product_type, practice_type, safety_level
Output: JSON string with safety guidelines

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
from ...config.safety_guidelines_config import get_safety_guidelines_config

logger = logging.getLogger(__name__)

@dataclass
class SafetyGuideline:
    """Structured safety guideline."""
    guideline_type: str
    description: str
    safety_level: str
    required_equipment: List[str]
    safety_measures: List[str]
    emergency_procedures: List[str]

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class GetSafetyGuidelinesTool(BaseTool):
    """
    Vector Database Ready Tool: Get safety guidelines for agricultural products and practices.
    
    Job: Take product and practice information to return safety guidelines.
    Input: product_type, practice_type, safety_level
    Output: JSON string with safety guidelines
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "get_safety_guidelines_tool"
    description: str = "Récupère les consignes de sécurité avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "safety_guidelines_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_safety_guidelines_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading safety guidelines knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        product_type: Optional[str] = None,
        practice_type: Optional[str] = None,
        safety_level: Optional[str] = None
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate that at least one type is provided
        if config.require_product_or_practice:
            if not product_type and not practice_type:
                errors.append(ValidationError("input", "Either product_type or practice_type must be provided", "error"))
        
        # Validate safety level if provided
        if config.validate_safety_level and safety_level:
            valid_levels = ["low", "medium", "high", "critical"]
            if safety_level.lower() not in valid_levels:
                errors.append(ValidationError("safety_level", f"Invalid safety level. Must be one of: {valid_levels}", "error"))
        
        return errors
    
    def _get_product_safety_guidelines(
        self, 
        product_type: str, 
        knowledge_base: Dict[str, Any]
    ) -> Optional[SafetyGuideline]:
        """Get safety guidelines for a specific product type."""
        product_guidelines = knowledge_base.get("product_safety_guidelines", {})
        
        # Find matching product type
        product_key = None
        for key in product_guidelines.keys():
            if product_type.lower() in key.lower() or key.lower() in product_type.lower():
                product_key = key
                break
        
        if not product_key:
            return None
        
        product_info = product_guidelines[product_key]
        
        return SafetyGuideline(
            guideline_type="product",
            description=f"Consignes de sécurité pour {product_type}",
            safety_level=product_info.get("safety_level", "medium"),
            required_equipment=product_info.get("required_equipment", []),
            safety_measures=product_info.get("guidelines", []),
            emergency_procedures=product_info.get("emergency_procedures", [])
        )
    
    def _get_practice_safety_guidelines(
        self, 
        practice_type: str, 
        knowledge_base: Dict[str, Any]
    ) -> Optional[SafetyGuideline]:
        """Get safety guidelines for a specific practice type."""
        practice_guidelines = knowledge_base.get("practice_safety_guidelines", {})
        
        # Find matching practice type
        practice_key = None
        for key in practice_guidelines.keys():
            if practice_type.lower() in key.lower() or key.lower() in practice_type.lower():
                practice_key = key
                break
        
        if not practice_key:
            return None
        
        practice_info = practice_guidelines[practice_key]
        
        return SafetyGuideline(
            guideline_type="practice",
            description=f"Consignes de sécurité pour {practice_type}",
            safety_level=practice_info.get("safety_level", "medium"),
            required_equipment=practice_info.get("required_equipment", []),
            safety_measures=practice_info.get("guidelines", []),
            emergency_procedures=practice_info.get("emergency_procedures", [])
        )
    
    def _get_safety_level_info(
        self, 
        safety_level: str, 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get information about a specific safety level."""
        safety_levels = knowledge_base.get("safety_levels", {})
        return safety_levels.get(safety_level.lower(), {})
    
    def _generate_comprehensive_guidelines(
        self, 
        product_guideline: Optional[SafetyGuideline], 
        practice_guideline: Optional[SafetyGuideline], 
        safety_level: Optional[str], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive safety guidelines combining all sources."""
        guidelines = {
            "safety_measures": [],
            "required_equipment": [],
            "emergency_procedures": [],
            "safety_levels": {}
        }
        
        # Add product guidelines
        if product_guideline:
            guidelines["safety_measures"].extend(product_guideline.safety_measures)
            guidelines["required_equipment"].extend(product_guideline.required_equipment)
            guidelines["emergency_procedures"].extend(product_guideline.emergency_procedures)
            guidelines["safety_levels"]["product"] = product_guideline.safety_level
        
        # Add practice guidelines
        if practice_guideline:
            guidelines["safety_measures"].extend(practice_guideline.safety_measures)
            guidelines["required_equipment"].extend(practice_guideline.required_equipment)
            guidelines["emergency_procedures"].extend(practice_guideline.emergency_procedures)
            guidelines["safety_levels"]["practice"] = practice_guideline.safety_level
        
        # Add safety level specific equipment if provided
        if safety_level:
            safety_level_info = self._get_safety_level_info(safety_level, knowledge_base)
            if safety_level_info:
                level_equipment = safety_level_info.get("equipment_required", [])
                guidelines["required_equipment"].extend(level_equipment)
                guidelines["safety_levels"]["requested"] = safety_level
        
        # Remove duplicates while preserving order
        guidelines["safety_measures"] = list(dict.fromkeys(guidelines["safety_measures"]))
        guidelines["required_equipment"] = list(dict.fromkeys(guidelines["required_equipment"]))
        guidelines["emergency_procedures"] = list(dict.fromkeys(guidelines["emergency_procedures"]))
        
        return guidelines
    
    def _run(
        self,
        product_type: Optional[str] = None,
        practice_type: Optional[str] = None,
        safety_level: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Get safety guidelines for agricultural products and practices.
        
        Args:
            product_type: Type of agricultural product (pesticide, herbicide, etc.)
            practice_type: Type of agricultural practice (spraying, seed_treatment, etc.)
            safety_level: Safety level (low, medium, high, critical)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(product_type, practice_type, safety_level)
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
            
            # Get safety guidelines
            product_guideline = None
            practice_guideline = None
            
            if product_type:
                product_guideline = self._get_product_safety_guidelines(product_type, knowledge_base)
            
            if practice_type:
                practice_guideline = self._get_practice_safety_guidelines(practice_type, knowledge_base)
            
            # Generate comprehensive guidelines
            comprehensive_guidelines = self._generate_comprehensive_guidelines(
                product_guideline, practice_guideline, safety_level, knowledge_base
            )
            
            # Determine overall safety level
            safety_levels = comprehensive_guidelines["safety_levels"]
            overall_safety_level = "medium"  # Default
            
            if safety_levels:
                # Use the highest safety level found
                level_priority = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                max_priority = 0
                for level in safety_levels.values():
                    if level_priority.get(level, 0) > max_priority:
                        max_priority = level_priority.get(level, 0)
                        overall_safety_level = level
            
            # Get safety level information
            safety_level_info = self._get_safety_level_info(overall_safety_level, knowledge_base)
            
            result = {
                "safety_guidelines": {
                    "product_type": product_type,
                    "practice_type": practice_type,
                    "requested_safety_level": safety_level,
                    "overall_safety_level": overall_safety_level,
                    "safety_level_info": safety_level_info,
                    "comprehensive_guidelines": comprehensive_guidelines
                },
                "detailed_guidelines": {
                    "product_guideline": asdict(product_guideline) if product_guideline else None,
                    "practice_guideline": asdict(practice_guideline) if practice_guideline else None
                },
                "summary": {
                    "total_safety_measures": len(comprehensive_guidelines["safety_measures"]),
                    "total_equipment_required": len(comprehensive_guidelines["required_equipment"]),
                    "total_emergency_procedures": len(comprehensive_guidelines["emergency_procedures"]),
                    "safety_level": overall_safety_level,
                    "guidelines_found": bool(product_guideline or practice_guideline)
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
            logger.error(f"Get safety guidelines error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la récupération des consignes de sécurité: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        product_type: Optional[str] = None,
        practice_type: Optional[str] = None,
        safety_level: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of safety guidelines retrieval.
        """
        # For now, just call the sync version
        return self._run(product_type, practice_type, safety_level, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
