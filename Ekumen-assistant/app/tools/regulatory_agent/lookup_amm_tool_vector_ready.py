"""
Lookup AMM Tool - Vector Database Ready Tool

Job: Look up AMM (Autorisation de Mise sur le Marché) information for agricultural products.
Input: product_name, active_ingredient, product_type
Output: JSON string with AMM information

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

Enhanced Features:
- External knowledge base (JSON file)
- Configurable analysis parameters
- Asynchronous support
- Comprehensive input validation
- Vector database ready architecture
- Semantic search capabilities

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional, Union
from langchain.tools import BaseTool
import logging
import json
import asyncio
import aiofiles
from dataclasses import dataclass, asdict
from pathlib import Path
import os

# Import configuration system
from ...config.amm_analysis_config import (
    get_amm_analysis_config, 
    get_amm_validation_config,
    AMMAnalysisConfig,
    AMMValidationConfig
)

# Import vector database interface
from ...data.amm_vector_db_interface import (
    get_amm_knowledge_base,
    set_amm_knowledge_base,
    AMMKnowledgeBaseInterface,
    AMMKnowledge,
    AMMSearchResult
)

logger = logging.getLogger(__name__)

@dataclass
class AMMInfo:
    """Structured AMM information."""
    product_name: str
    amm_number: str
    active_ingredient: str
    product_type: str
    manufacturer: str
    authorized_uses: List[str]
    restrictions: List[str]
    safety_measures: List[str]
    validity_period: str
    registration_date: str
    expiry_date: str
    target_crops: List[str]
    target_pests: List[str]
    target_diseases: List[str]
    target_weeds: List[str]
    application_methods: List[str]
    dosage_range: Dict[str, str]
    phytotoxicity_risk: str
    environmental_impact: str
    resistance_risk: str
    search_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str  # "error", "warning", "info"

class LookupAMMTool(BaseTool):
    """
    Vector Database Ready Tool: Look up AMM information for agricultural products.
    
    Job: Take product information and return AMM details.
    Input: product_name, active_ingredient, product_type
    Output: JSON string with AMM information
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    - Semantic search capabilities
    """
    
    name: str = "lookup_amm_tool"
    description: str = "Consulte les informations AMM pour les produits agricoles avec recherche sémantique"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        use_vector_search: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self.use_vector_search = use_vector_search
        self._config_cache: Optional[AMMAnalysisConfig] = None
        self._validation_cache: Optional[AMMValidationConfig] = None
        self._knowledge_base: Optional[AMMKnowledgeBaseInterface] = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "amm_lookup_knowledge.json")
    
    def _get_knowledge_base(self) -> AMMKnowledgeBaseInterface:
        """Get knowledge base instance."""
        if self._knowledge_base is None:
            if self.use_vector_search:
                # Use vector database (when implemented)
                self._knowledge_base = get_amm_knowledge_base()
            else:
                # Use JSON knowledge base
                from ...data.amm_vector_db_interface import JSONAMMKnowledgeBase
                self._knowledge_base = JSONAMMKnowledgeBase(self.knowledge_base_path)
        return self._knowledge_base
    
    def _get_config(self) -> AMMAnalysisConfig:
        """Get current analysis configuration."""
        if self._config_cache is None:
            self._config_cache = get_amm_analysis_config()
        return self._config_cache
    
    def _get_validation_config(self) -> AMMValidationConfig:
        """Get current validation configuration."""
        if self._validation_cache is None:
            self._validation_cache = get_amm_validation_config()
        return self._validation_cache
    
    def _validate_inputs(
        self, 
        product_name: Optional[str], 
        active_ingredient: Optional[str], 
        product_type: Optional[str]
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        validation_config = self._get_validation_config()
        
        # Check if at least one criteria is provided
        criteria_provided = any([product_name, active_ingredient, product_type])
        if validation_config.require_at_least_one_criteria and not criteria_provided:
            errors.append(ValidationError("search_criteria", "At least one search criteria is required", "error"))
        
        # Validate product name
        if product_name:
            if len(product_name.strip()) < validation_config.min_product_name_length:
                errors.append(ValidationError("product_name", f"Product name too short (minimum {validation_config.min_product_name_length} characters)", "error"))
            elif len(product_name.strip()) > validation_config.max_product_name_length:
                errors.append(ValidationError("product_name", f"Product name too long (maximum {validation_config.max_product_name_length} characters)", "warning"))
        
        # Validate active ingredient
        if active_ingredient:
            if len(active_ingredient.strip()) < validation_config.min_active_ingredient_length:
                errors.append(ValidationError("active_ingredient", f"Active ingredient too short (minimum {validation_config.min_active_ingredient_length} characters)", "error"))
            elif len(active_ingredient.strip()) > validation_config.max_active_ingredient_length:
                errors.append(ValidationError("active_ingredient", f"Active ingredient too long (maximum {validation_config.max_active_ingredient_length} characters)", "warning"))
        
        # Validate product type
        if product_type and validation_config.validate_product_type:
            config = self._get_config()
            if product_type.lower() not in [pt.lower() for pt in config.supported_product_types]:
                errors.append(ValidationError("product_type", f"Product type '{product_type}' not supported", "warning"))
        
        # Check total criteria count
        total_criteria = sum([1 for x in [product_name, active_ingredient, product_type] if x])
        if total_criteria > validation_config.max_total_criteria:
            errors.append(ValidationError("search_criteria", f"Too many search criteria (maximum {validation_config.max_total_criteria})", "warning"))
        
        return errors
    
    async def _search_amm_knowledge(
        self,
        product_name: Optional[str],
        active_ingredient: Optional[str],
        product_type: Optional[str]
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge using vector database or JSON fallback."""
        knowledge_base = self._get_knowledge_base()
        
        if self.use_vector_search:
            # Use vector-based semantic search
            return await knowledge_base.search_by_criteria(
                product_name=product_name,
                active_ingredient=active_ingredient,
                product_type=product_type,
                limit=self._get_config().max_results
            )
        else:
            # Use traditional JSON-based search
            return await knowledge_base.search_by_criteria(
                product_name=product_name,
                active_ingredient=active_ingredient,
                product_type=product_type,
                limit=self._get_config().max_results
            )
    
    def _analyze_amm_results(
        self, 
        search_results: List[AMMSearchResult],
        product_name: Optional[str],
        active_ingredient: Optional[str],
        product_type: Optional[str]
    ) -> List[AMMInfo]:
        """Analyze AMM search results and convert to AMMInfo objects."""
        amm_infos = []
        config = self._get_config()
        
        for result in search_results:
            amm_knowledge = result.amm_knowledge
            
            # Calculate confidence based on search criteria
            confidence = result.similarity_score
            
            # Add bonuses for exact matches
            if product_name and product_name.lower() == amm_knowledge.product_name.lower():
                confidence += config.exact_match_bonus
            elif product_name and product_name.lower() in amm_knowledge.product_name.lower():
                confidence += config.partial_match_bonus
            
            if active_ingredient and active_ingredient.lower() == amm_knowledge.active_ingredient.lower():
                confidence += config.exact_match_bonus
            elif active_ingredient and active_ingredient.lower() in amm_knowledge.active_ingredient.lower():
                confidence += config.partial_match_bonus
            
            if product_type and product_type.lower() == amm_knowledge.product_type.lower():
                confidence += config.exact_match_bonus
            elif product_type and product_type.lower() in amm_knowledge.product_type.lower():
                confidence += config.partial_match_bonus
            
            # Cap confidence at 1.0
            confidence = min(confidence, 1.0)
            
            if confidence > config.minimum_confidence:
                amm_info = AMMInfo(
                    product_name=amm_knowledge.product_name,
                    amm_number=amm_knowledge.amm_number,
                    active_ingredient=amm_knowledge.active_ingredient,
                    product_type=amm_knowledge.product_type,
                    manufacturer=amm_knowledge.manufacturer,
                    authorized_uses=amm_knowledge.authorized_uses,
                    restrictions=amm_knowledge.restrictions if config.include_restrictions else [],
                    safety_measures=amm_knowledge.safety_measures if config.include_safety_measures else [],
                    validity_period=amm_knowledge.validity_period,
                    registration_date=amm_knowledge.registration_date,
                    expiry_date=amm_knowledge.expiry_date,
                    target_crops=amm_knowledge.target_crops,
                    target_pests=amm_knowledge.target_pests,
                    target_diseases=amm_knowledge.target_diseases,
                    target_weeds=amm_knowledge.target_weeds,
                    application_methods=amm_knowledge.application_methods,
                    dosage_range=amm_knowledge.dosage_range if config.include_dosage_info else {},
                    phytotoxicity_risk=amm_knowledge.phytotoxicity_risk,
                    environmental_impact=amm_knowledge.environmental_impact if config.include_environmental_info else "",
                    resistance_risk=amm_knowledge.resistance_risk,
                    search_metadata={
                        "search_method": "vector" if self.use_vector_search else "json",
                        "similarity_score": result.similarity_score,
                        "match_type": result.match_type,
                        "confidence": confidence
                    }
                )
                amm_infos.append(amm_info)
        
        # Sort by confidence and limit results
        amm_infos.sort(key=lambda x: x.search_metadata["confidence"], reverse=True)
        return amm_infos[:config.max_results]
    
    def _calculate_search_confidence(self, amm_infos: List[AMMInfo]) -> str:
        """Calculate overall search confidence."""
        config = self._get_config()
        
        if not amm_infos:
            return "low"
        
        max_confidence = max(amm_info.search_metadata["confidence"] for amm_info in amm_infos)
        
        if max_confidence > config.high_confidence:
            return "high"
        elif max_confidence > config.moderate_confidence:
            return "moderate"
        else:
            return "low"
    
    def _generate_search_summary(self, amm_infos: List[AMMInfo]) -> List[str]:
        """Generate search summary based on AMM results."""
        summary = []
        config = self._get_config()
        
        if not amm_infos:
            summary.append("Aucun produit AMM trouvé - Vérifiez les critères de recherche")
            return summary
        
        # Get top result
        top_result = amm_infos[0]
        confidence = top_result.search_metadata["confidence"]
        
        if confidence > config.moderate_confidence:
            summary.append(f"Produit principal: {top_result.product_name} - Confiance: {confidence:.1%}")
            summary.append(f"AMM: {top_result.amm_number} - Validité: {top_result.validity_period}")
            summary.append(f"Principe actif: {top_result.active_ingredient}")
            summary.append(f"Type: {top_result.product_type}")
            summary.append(f"Fabricant: {top_result.manufacturer}")
            
            if config.include_restrictions and top_result.restrictions:
                summary.append("Restrictions importantes:")
                summary.extend([f"  • {restriction}" for restriction in top_result.restrictions[:3]])
            
            if config.include_safety_measures and top_result.safety_measures:
                summary.append("Mesures de sécurité:")
                summary.extend([f"  • {measure}" for measure in top_result.safety_measures[:3]])
            
            if config.include_dosage_info and top_result.dosage_range:
                summary.append("Dosage recommandé:")
                summary.append(f"  • {top_result.dosage_range.get('recommended', 'Non spécifié')}")
            
            if config.include_environmental_info:
                summary.append(f"Impact environnemental: {top_result.environmental_impact}")
                summary.append(f"Risque de résistance: {top_result.resistance_risk}")
        else:
            summary.append("Recherche incertaine - Vérifiez les critères de recherche")
            summary.append("Consultez un expert pour validation")
        
        return summary
    
    def _run(
        self,
        product_name: Optional[str] = None,
        active_ingredient: Optional[str] = None,
        product_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Look up AMM information for agricultural products.
        
        Args:
            product_name: Name of the agricultural product
            active_ingredient: Active ingredient of the product
            product_type: Type of product (herbicide, insecticide, fungicide, etc.)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(product_name, active_ingredient, product_type)
            validation_config = self._get_validation_config()
            
            if validation_errors and validation_config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Search AMM knowledge
            search_results = asyncio.run(self._search_amm_knowledge(
                product_name, 
                active_ingredient, 
                product_type
            ))
            
            if not search_results:
                return json.dumps({
                    "error": "No AMM products found",
                    "suggestions": ["Check product name spelling", "Try different search criteria", "Verify product type"]
                })
            
            # Analyze AMM results
            amm_infos = self._analyze_amm_results(
                search_results,
                product_name, 
                active_ingredient, 
                product_type
            )
            
            # Calculate search confidence
            search_confidence = self._calculate_search_confidence(amm_infos)
            
            # Generate search summary
            search_summary = self._generate_search_summary(amm_infos)
            
            result = {
                "search_criteria": {
                    "product_name": product_name,
                    "active_ingredient": active_ingredient,
                    "product_type": product_type
                },
                "amm_results": [asdict(amm_info) for amm_info in amm_infos],
                "search_confidence": search_confidence,
                "search_summary": search_summary,
                "total_results": len(amm_infos),
                "analysis_metadata": {
                    "search_method": "vector" if self.use_vector_search else "json",
                    "config_used": asdict(self._get_config()),
                    "search_results_count": len(search_results)
                }
            }
            
            # Add validation warnings if any
            if validation_errors and validation_config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Lookup AMM error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la consultation AMM: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        product_name: Optional[str] = None,
        active_ingredient: Optional[str] = None,
        product_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of AMM lookup.
        
        Args:
            product_name: Name of the agricultural product
            active_ingredient: Active ingredient of the product
            product_type: Type of product (herbicide, insecticide, fungicide, etc.)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(product_name, active_ingredient, product_type)
            validation_config = self._get_validation_config()
            
            if validation_errors and validation_config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Search AMM knowledge asynchronously
            search_results = await self._search_amm_knowledge(
                product_name, 
                active_ingredient, 
                product_type
            )
            
            if not search_results:
                return json.dumps({
                    "error": "No AMM products found",
                    "suggestions": ["Check product name spelling", "Try different search criteria", "Verify product type"]
                })
            
            # Analyze AMM results
            amm_infos = self._analyze_amm_results(
                search_results,
                product_name, 
                active_ingredient, 
                product_type
            )
            
            # Calculate search confidence
            search_confidence = self._calculate_search_confidence(amm_infos)
            
            # Generate search summary
            search_summary = self._generate_search_summary(amm_infos)
            
            result = {
                "search_criteria": {
                    "product_name": product_name,
                    "active_ingredient": active_ingredient,
                    "product_type": product_type
                },
                "amm_results": [asdict(amm_info) for amm_info in amm_infos],
                "search_confidence": search_confidence,
                "search_summary": search_summary,
                "total_results": len(amm_infos),
                "analysis_metadata": {
                    "search_method": "vector" if self.use_vector_search else "json",
                    "config_used": asdict(self._get_config()),
                    "search_results_count": len(search_results),
                    "execution_mode": "async"
                }
            }
            
            # Add validation warnings if any
            if validation_errors and validation_config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Async lookup AMM error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la consultation asynchrone AMM: {str(e)}",
                "error_type": type(e).__name__
            })
    
    def clear_cache(self):
        """Clear internal caches (useful for testing or config updates)."""
        self._config_cache = None
        self._validation_cache = None
        self._knowledge_base = None
        logger.info("Cleared tool caches")
    
    def enable_vector_search(self, enable: bool = True):
        """Enable or disable vector search."""
        self.use_vector_search = enable
        self._knowledge_base = None  # Reset knowledge base
        logger.info(f"Vector search {'enabled' if enable else 'disabled'}")
