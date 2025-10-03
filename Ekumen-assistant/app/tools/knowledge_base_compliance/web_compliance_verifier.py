"""
Web Compliance Verifier Tool - Enhanced Version
Verifies uncertain findings against official regulatory websites

Improvements:
1. Better structured verification results
2. Enhanced mock search logic for testing
3. Confidence scoring for web findings
4. Better timeout and error handling
5. Comprehensive regulatory update checking
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class WebComplianceVerifierInput(BaseModel):
    """Input for web compliance verification"""
    uncertain_products: List[str] = Field(
        default_factory=list,
        description="Products that need web verification"
    )
    uncertain_substances: List[str] = Field(
        default_factory=list,
        description="Substances that need web verification"
    )
    validation_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Previous validation results"
    )
    document_id: str = Field(description="Document identifier for tracking")
    
    @validator('uncertain_products', 'uncertain_substances')
    def validate_lists(cls, v):
        if not isinstance(v, list):
            return []
        return [item for item in v if item and isinstance(item, str)]


class WebComplianceVerifierTool(BaseTool):
    """
    Tool for verifying uncertain findings against official regulatory websites
    
    Search targets:
    - ephy.anses.fr (official EPHY database)
    - agriculture.gouv.fr (Ministry of Agriculture)
    - anses.fr (National Agency for Food Safety)
    
    Verification types:
    - Recent authorization changes
    - New product approvals not yet in local database
    - Emergency withdrawals or suspensions
    - Updated usage restrictions
    """
    
    name: str = "web_compliance_verifier"
    description: str = """
    Verify uncertain findings against official regulatory websites.
    
    Use this tool when previous validations return uncertain results or missing products.
    Searches official French regulatory websites for up-to-date information.
    
    Input: uncertain_products, uncertain_substances, validation_results, document_id
    Output: Web verification results with updated compliance status
    """
    args_schema: type = WebComplianceVerifierInput
    regulatory_sites: List[str] = Field(default_factory=list)
    enable_web_search: bool = False  # Set to True when web scraping is implemented
    timeout: float = 10.0
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.regulatory_sites = [
            "https://ephy.anses.fr",
            "https://agriculture.gouv.fr",
            "https://www.anses.fr"
        ]
        logger.info("Web Compliance Verifier Tool initialized")
    
    def _run(
        self,
        uncertain_products: List[str],
        uncertain_substances: List[str],
        validation_results: Dict[str, Any],
        document_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Verify uncertain findings against official websites"""
        try:
            logger.info(
                f"Starting web verification for document {document_id}: "
                f"{len(uncertain_products)} products, {len(uncertain_substances)} substances"
            )
            
            # Validate inputs
            if not uncertain_products and not uncertain_substances:
                logger.warning("No uncertain items to verify")
                return {
                    "status": "success",
                    "verification_status": "NO_VERIFICATION_NEEDED",
                    "verification_results": {
                        "product_verifications": [],
                        "substance_verifications": [],
                        "website_results": {},
                        "violations": [],
                        "warnings": [],
                        "recommendations": []
                    },
                    "total_products_verified": 0,
                    "total_substances_verified": 0,
                    "total_violations": 0,
                    "total_warnings": 0,
                    "document_id": document_id
                }
            
            verification_results = {
                "product_verifications": [],
                "substance_verifications": [],
                "website_results": {},
                "regulatory_updates": {},
                "violations": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Verify uncertain products
            for product in uncertain_products:
                if not product or not product.strip():
                    continue
                    
                product_result = self._verify_product_web(product.strip())
                verification_results["product_verifications"].append(product_result)
                self._collect_web_issues(product_result, verification_results)
            
            # Verify uncertain substances
            for substance in uncertain_substances:
                if not substance or not substance.strip():
                    continue
                    
                substance_result = self._verify_substance_web(substance.strip())
                verification_results["substance_verifications"].append(substance_result)
                self._collect_web_issues(substance_result, verification_results)
            
            # Check for recent regulatory updates
            all_entities = uncertain_products + uncertain_substances
            regulatory_updates = self._check_regulatory_updates(all_entities)
            verification_results["regulatory_updates"] = regulatory_updates
            
            # Add warnings for regulatory updates
            if regulatory_updates.get("recent_withdrawals"):
                for withdrawal in regulatory_updates["recent_withdrawals"]:
                    verification_results["warnings"].append(
                        f"Product '{withdrawal['entity']}' was withdrawn on {withdrawal['date']}"
                    )
            
            if regulatory_updates.get("new_restrictions"):
                for restriction in regulatory_updates["new_restrictions"]:
                    verification_results["warnings"].append(
                        f"New restriction for '{restriction['entity']}': {restriction['restriction']}"
                    )
            
            # Determine overall verification status
            verification_status = self._determine_verification_status(verification_results)
            
            logger.info(f"Web verification completed: {verification_status}")
            
            return {
                "status": "success",
                "verification_status": verification_status,
                "verification_results": verification_results,
                "total_products_verified": len([p for p in uncertain_products if p]),
                "total_substances_verified": len([s for s in uncertain_substances if s]),
                "total_violations": len(verification_results["violations"]),
                "total_warnings": len(verification_results["warnings"]),
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error in web compliance verification: {e}", exc_info=True)
            return self._error_response(str(e), document_id)
    
    def _verify_product_web(self, product: str) -> Dict[str, Any]:
        """Verify a product against official websites"""
        verification_result = {
            "product_name": product,
            "ephy_status": "unknown",
            "authorization_status": "unknown",
            "last_updated": None,
            "source": "web_verification",
            "confidence": 0.5,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Search EPHY website
            if self.enable_web_search:
                # Actual web scraping would go here
                web_results = self._search_ephy_website_real(product)
            else:
                # Use mock data for testing
                web_results = self._search_ephy_website_mock(product)
            
            if web_results.get("found"):
                verification_result["ephy_status"] = web_results.get("status", "unknown")
                verification_result["authorization_status"] = web_results.get("status", "unknown")
                verification_result["last_updated"] = web_results.get("last_updated")
                verification_result["confidence"] = web_results.get("confidence", 0.7)
                
                # Check for restrictions
                if web_results.get("restrictions"):
                    verification_result["warnings"].extend(web_results["restrictions"])
                
                # Check for recent changes
                if web_results.get("recent_changes"):
                    verification_result["recommendations"].extend(web_results["recent_changes"])
                
                # Check if withdrawn
                if web_results.get("status") == "withdrawn":
                    verification_result["violations"].append(
                        f"Product '{product}' found in EPHY but status is WITHDRAWN"
                    )
                    verification_result["recommendations"].append(
                        "Do not use withdrawn products - use authorized alternatives"
                    )
            else:
                verification_result["ephy_status"] = "not_found"
                verification_result["confidence"] = 0.3
                verification_result["violations"].append(
                    f"Product '{product}' not found in official EPHY database"
                )
                verification_result["recommendations"].extend([
                    "Verify product name spelling and check for typos",
                    "Check if product was recently withdrawn",
                    "Consult official EPHY website at https://ephy.anses.fr"
                ])
            
        except Exception as e:
            verification_result["violations"].append(
                f"Web verification failed for '{product}': {str(e)}"
            )
            verification_result["recommendations"].append(
                "Manual verification required - check EPHY website directly"
            )
            verification_result["confidence"] = 0.0
            logger.warning(f"Error verifying product '{product}': {e}")
        
        return verification_result
    
    def _verify_substance_web(self, substance: str) -> Dict[str, Any]:
        """Verify a substance against official websites"""
        verification_result = {
            "substance_name": substance,
            "approval_status": "unknown",
            "last_updated": None,
            "source": "web_verification",
            "confidence": 0.5,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Search substance databases
            if self.enable_web_search:
                web_results = self._search_substance_website_real(substance)
            else:
                web_results = self._search_substance_website_mock(substance)
            
            if web_results.get("found"):
                verification_result["approval_status"] = web_results.get("status", "unknown")
                verification_result["last_updated"] = web_results.get("last_updated")
                verification_result["confidence"] = web_results.get("confidence", 0.7)
                
                # Check for restrictions
                if web_results.get("restrictions"):
                    verification_result["warnings"].extend(web_results["restrictions"])
                
                # Check if not approved
                if web_results.get("status") == "not_approved":
                    verification_result["violations"].append(
                        f"Substance '{substance}' is NOT APPROVED in official database"
                    )
            else:
                verification_result["approval_status"] = "not_found"
                verification_result["confidence"] = 0.3
                verification_result["violations"].append(
                    f"Substance '{substance}' not found in official databases"
                )
                verification_result["recommendations"].append(
                    "Verify substance name and check ANSES website"
                )
        
        except Exception as e:
            verification_result["violations"].append(
                f"Web verification failed for '{substance}': {str(e)}"
            )
            verification_result["confidence"] = 0.0
            logger.warning(f"Error verifying substance '{substance}': {e}")
        
        return verification_result
    
    def _search_ephy_website_real(self, product: str) -> Dict[str, Any]:
        """Actual web scraping implementation (placeholder)"""
        # TODO: Implement actual web scraping with requests/beautifulsoup
        logger.info(f"Real web search not implemented yet for: {product}")
        return {"found": False}
    
    def _search_ephy_website_mock(self, product: str) -> Dict[str, Any]:
        """Mock EPHY database lookup for testing"""
        # Expanded mock database with more products
        ephy_products = {
            "roundup": {
                "found": True,
                "status": "authorized",
                "last_updated": "2024-01-15",
                "confidence": 0.9
            },
            "opus": {
                "found": True,
                "status": "authorized",
                "last_updated": "2024-02-01",
                "confidence": 0.9
            },
            "amistar": {
                "found": True,
                "status": "authorized",
                "last_updated": "2024-01-20",
                "confidence": 0.9
            },
            "tilt": {
                "found": True,
                "status": "withdrawn",
                "last_updated": "2023-12-01",
                "confidence": 0.9,
                "restrictions": ["Product withdrawn from market in December 2023"]
            },
            "score": {
                "found": True,
                "status": "authorized",
                "last_updated": "2024-01-10",
                "confidence": 0.9
            },
            "folicur": {
                "found": True,
                "status": "authorized",
                "last_updated": "2024-01-05",
                "confidence": 0.9
            },
            "glyphosate": {
                "found": True,
                "status": "authorized",
                "last_updated": "2024-01-15",
                "confidence": 0.9,
                "restrictions": ["Maximum dosage reduced to 3.0 L/ha"]
            }
        }
        
        product_lower = product.lower()
        
        for ephy_product, info in ephy_products.items():
            if ephy_product in product_lower:
                return info
        
        return {"found": False, "confidence": 0.0}
    
    def _search_substance_website_real(self, substance: str) -> Dict[str, Any]:
        """Actual substance web search implementation (placeholder)"""
        # TODO: Implement actual web scraping
        logger.info(f"Real substance search not implemented yet for: {substance}")
        return {"found": False}
    
    def _search_substance_website_mock(self, substance: str) -> Dict[str, Any]:
        """Mock substance approval lookup for testing"""
        # Expanded approved substances list
        approved_substances = {
            "glyphosate": {
                "found": True,
                "status": "approved",
                "last_updated": "2024-01-15",
                "confidence": 0.9,
                "restrictions": ["Use restrictions in certain zones"]
            },
            "epoxiconazole": {
                "found": True,
                "status": "approved",
                "last_updated": "2024-02-01",
                "confidence": 0.9
            },
            "azoxystrobine": {
                "found": True,
                "status": "approved",
                "last_updated": "2024-01-20",
                "confidence": 0.9
            },
            "propiconazole": {
                "found": True,
                "status": "approved",
                "last_updated": "2024-01-10",
                "confidence": 0.9
            },
            "tebuconazole": {
                "found": True,
                "status": "approved",
                "last_updated": "2024-01-05",
                "confidence": 0.9
            },
            "difenoconazole": {
                "found": True,
                "status": "approved",
                "last_updated": "2024-01-12",
                "confidence": 0.9
            }
        }
        
        substance_lower = substance.lower()
        
        for approved_sub, info in approved_substances.items():
            if approved_sub in substance_lower:
                return info
        
        return {"found": False, "confidence": 0.0}
    
    def _check_regulatory_updates(self, entities: List[str]) -> Dict[str, Any]:
        """Check for recent regulatory updates affecting the entities"""
        updates = {
            "recent_withdrawals": [],
            "new_restrictions": [],
            "updated_limits": [],
            "emergency_suspensions": []
        }
        
        if not entities:
            return updates
        
        # Mock recent updates
        for entity in entities:
            if not entity:
                continue
                
            entity_lower = entity.lower()
            
            # Check for withdrawals
            if "tilt" in entity_lower:
                updates["recent_withdrawals"].append({
                    "entity": entity,
                    "action": "withdrawn",
                    "date": "2023-12-01",
                    "reason": "Market withdrawal by manufacturer"
                })
            
            # Check for new restrictions
            if "glyphosate" in entity_lower:
                updates["new_restrictions"].append({
                    "entity": entity,
                    "restriction": "Reduced maximum dosage",
                    "date": "2024-01-15",
                    "details": "Maximum dosage reduced to 3.0 L/ha"
                })
            
            # Check for updated limits
            if "epoxiconazole" in entity_lower:
                updates["updated_limits"].append({
                    "entity": entity,
                    "update": "DAR period extended",
                    "date": "2024-02-01",
                    "details": "Pre-harvest delay extended to 42 days for wheat"
                })
        
        return updates
    
    def _collect_web_issues(self, result: Dict[str, Any], verification_results: Dict[str, Any]):
        """Collect violations, warnings, and recommendations from web verification result"""
        if result.get("violations"):
            verification_results["violations"].extend(result["violations"])
        if result.get("warnings"):
            verification_results["warnings"].extend(result["warnings"])
        if result.get("recommendations"):
            verification_results["recommendations"].extend(result["recommendations"])
    
    def _determine_verification_status(self, verification_results: Dict[str, Any]) -> str:
        """Determine overall web verification status"""
        violations = verification_results.get("violations", [])
        warnings = verification_results.get("warnings", [])
        
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
            "verification_status": "UNCERTAIN",
            "verification_results": {
                "product_verifications": [],
                "substance_verifications": [],
                "website_results": {},
                "regulatory_updates": {},
                "violations": [f"Web verification failed: {error_message}"],
                "warnings": [],
                "recommendations": ["Manual review required due to verification error"]
            },
            "total_products_verified": 0,
            "total_substances_verified": 0,
            "total_violations": 1,
            "total_warnings": 0,
            "document_id": document_id
        }
    
    async def _arun(
        self,
        uncertain_products: List[str],
        uncertain_substances: List[str],
        validation_results: Dict[str, Any],
        document_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version of the tool"""
        # For true async web scraping, implement here with aiohttp
        return self._run(uncertain_products, uncertain_substances, validation_results, document_id, **kwargs)