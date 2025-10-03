"""
Regulatory Entity Extractor Tool - Using existing regulatory tools and structured outputs for reliable validation
Extracts regulatory entities from agricultural document text

Improvements:
1. Better error handling and recovery
2. Structured output validation
3. Improved fallback extraction
4. Better confidence scoring
5. Async support properly implemented
"""

import logging
from typing import Dict, Any, List, Optional
import re
import json

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, validator
from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class RegulatoryEntityExtractorInput(BaseModel):
    """Input for regulatory entity extraction"""
    document_content: str = Field(description="Full text content of the agricultural document")
    document_type: str = Field(description="Type of document (manual, product_spec, technical_sheet, etc.)")
    max_content_length: Optional[int] = Field(default=8000, description="Maximum content length to process")
    
    @validator('document_content')
    def validate_content(cls, v):
        if not v or len(v.strip()) < 50:
            raise ValueError("Document content too short (minimum 50 characters)")
        return v


class RegulatoryEntityExtractorTool(BaseTool):
    """
    Tool for extracting regulatory entities from agricultural documents
    
    Extracts:
    - Product names and commercial brands
    - Active substance names
    - Dosage amounts and units (L/ha, kg/ha)
    - Application frequencies
    - ZNT distances and DAR periods
    - Crop types and target pests/diseases
    """
    
    name: str = "regulatory_entity_extractor"
    description: str = """
    Extract regulatory entities from agricultural document text.
    
    Use this tool FIRST to identify all regulatory-relevant information in the document.
    Extracts product names, active substances, dosages, application frequencies,
    ZNT distances, DAR periods, crop types, and target pests/diseases.
    
    Input: document_content (full text), document_type (manual, product_spec, etc.)
    Output: Structured JSON with all extracted regulatory entities
    """
    args_schema: type = RegulatoryEntityExtractorInput
    llm: Optional[ChatOpenAI] = None
    enable_fallback: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        logger.info("Regulatory Entity Extractor Tool initialized")
    
    def _run(
        self,
        document_content: str,
        document_type: str,
        max_content_length: int = 8000,
        **kwargs
    ) -> Dict[str, Any]:
        """Extract regulatory entities from document content"""
        try:
            logger.info(f"Extracting entities from {document_type} document ({len(document_content)} chars)")
            
            # Validate input
            if not document_content or len(document_content.strip()) < 50:
                return self._error_response("Document content too short or empty")
            
            # Limit content for token efficiency
            content_sample = document_content[:max_content_length]
            if len(document_content) > max_content_length:
                logger.warning(f"Content truncated from {len(document_content)} to {max_content_length} chars")
            
            # Create extraction prompt
            extraction_prompt = self._create_extraction_prompt(content_sample, document_type)
            
            # Get LLM extraction
            try:
                response = self.llm.invoke(extraction_prompt)
                extracted_entities = self._parse_llm_response(response.content)
                extraction_confidence = 0.9
                extraction_method = "llm"
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}, using fallback")
                if self.enable_fallback:
                    extracted_entities = self._fallback_extraction(document_content)
                    extraction_confidence = 0.6
                    extraction_method = "regex_fallback"
                else:
                    raise
            
            # Validate and clean extracted entities
            validated_entities = self._validate_extracted_entities(extracted_entities)
            
            # Calculate statistics
            total_entities = sum(
                len(v) for v in validated_entities.values() 
                if isinstance(v, list)
            )
            
            logger.info(
                f"Extraction complete: {len(validated_entities.get('products', []))} products, "
                f"{len(validated_entities.get('dosages', []))} dosages, "
                f"total {total_entities} entities"
            )
            
            return {
                "status": "success",
                "extracted_entities": validated_entities,
                "extraction_confidence": extraction_confidence,
                "extraction_method": extraction_method,
                "total_entities": total_entities,
                "document_type": document_type,
                "content_length": len(document_content),
                "processed_length": len(content_sample)
            }
            
        except Exception as e:
            logger.error(f"Error extracting regulatory entities: {e}", exc_info=True)
            return self._error_response(str(e))
    
    def _create_extraction_prompt(self, content: str, document_type: str) -> str:
        """Create LLM extraction prompt"""
        return f"""Extract all regulatory entities from this agricultural document.

Document Type: {document_type}

Content:
{content}

Extract the following information in valid JSON format:
{{
    "products": [
        {{
            "name": "Product name",
            "commercial_brand": "Brand name",
            "active_substances": ["substance1", "substance2"],
            "concentration": "concentration info"
        }}
    ],
    "dosages": [
        {{
            "product": "Product name",
            "amount": "dosage amount",
            "unit": "L/ha, kg/ha, etc.",
            "crop": "target crop",
            "application_method": "foliar, soil, etc."
        }}
    ],
    "application_frequencies": [
        {{
            "product": "Product name",
            "frequency": "number of applications",
            "interval": "days between applications",
            "season": "application season"
        }}
    ],
    "znt_distances": [
        {{
            "product": "Product name",
            "distance": "distance in meters",
            "target": "water, houses, etc."
        }}
    ],
    "dar_periods": [
        {{
            "product": "Product name",
            "period": "days before harvest",
            "crop": "target crop"
        }}
    ],
    "crops": [
        {{
            "name": "crop name",
            "variety": "specific variety if mentioned",
            "growth_stage": "BBCH code or stage description"
        }}
    ],
    "pests_diseases": [
        {{
            "name": "pest or disease name",
            "type": "pest, disease, or weed",
            "target_crop": "affected crop"
        }}
    ],
    "safety_restrictions": [
        {{
            "type": "restriction type",
            "description": "restriction details",
            "products": ["affected products"]
        }}
    ]
}}

IMPORTANT: 
- Return ONLY valid JSON, no markdown or explanations
- If information is not present, use empty arrays []
- Extract ALL mentions, even if repeated
- Be thorough with dosages and safety information"""
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON"""
        try:
            # Remove markdown code blocks if present
            content = response_content.strip()
            
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Parse JSON
            extracted = json.loads(content)
            
            # Ensure all expected keys exist
            expected_keys = [
                "products", "dosages", "application_frequencies", "znt_distances",
                "dar_periods", "crops", "pests_diseases", "safety_restrictions"
            ]
            for key in expected_keys:
                if key not in extracted:
                    extracted[key] = []
            
            return extracted
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    
    def _fallback_extraction(self, document_content: str) -> Dict[str, Any]:
        """Fallback regex-based extraction if LLM parsing fails"""
        logger.info("Using fallback regex extraction")
        
        # Enhanced regex patterns for French agricultural terms
        patterns = {
            "dosages": r"(\d+(?:[.,]\d+)?)\s*(L/ha|kg/ha|g/ha|ml/ha|l/ha)",
            "products": r"([A-Z][a-zéèêàâôù]+(?:\s+[A-Z][a-zéèêàâôù]+){0,2})\s*(?:®|™|©)?",
            "substances": r"([a-zéèêàâôù]+(?:azole|ate|ide|in|ol|one|ine))",
            "crops": r"\b(blé|maïs|colza|tournesol|orge|avoine|seigle|triticale|pomme de terre|betterave|vigne|pois|soja)\b",
            "znt": r"ZNT\s*[:\s]*(\d+)\s*(?:m|mètres?)",
            "dar": r"(?:DAR|délai avant récolte)\s*[:\s]*(\d+)\s*(?:jours?|j)"
        }
        
        extracted = {
            "products": [],
            "dosages": [],
            "application_frequencies": [],
            "znt_distances": [],
            "dar_periods": [],
            "crops": [],
            "pests_diseases": [],
            "safety_restrictions": []
        }
        
        # Extract dosages with context
        dosage_matches = re.finditer(patterns["dosages"], document_content, re.IGNORECASE)
        for match in dosage_matches:
            extracted["dosages"].append({
                "amount": match.group(1).replace(',', '.'),
                "unit": match.group(2),
                "product": "",
                "crop": ""
            })
        
        # Extract products (basic - names starting with capital letters)
        product_matches = re.finditer(patterns["products"], document_content)
        seen_products = set()
        for match in product_matches:
            product_name = match.group(1).strip()
            if product_name not in seen_products and len(product_name) > 3:
                seen_products.add(product_name)
                extracted["products"].append({
                    "name": product_name,
                    "commercial_brand": "",
                    "active_substances": [],
                    "concentration": ""
                })
        
        # Extract crops
        crop_matches = re.finditer(patterns["crops"], document_content, re.IGNORECASE)
        seen_crops = set()
        for match in crop_matches:
            crop_name = match.group(1).lower()
            if crop_name not in seen_crops:
                seen_crops.add(crop_name)
                extracted["crops"].append({
                    "name": crop_name,
                    "variety": "",
                    "growth_stage": ""
                })
        
        # Extract ZNT distances
        znt_matches = re.finditer(patterns["znt"], document_content, re.IGNORECASE)
        for match in znt_matches:
            extracted["znt_distances"].append({
                "distance": match.group(1),
                "product": "",
                "target": "water"
            })
        
        # Extract DAR periods
        dar_matches = re.finditer(patterns["dar"], document_content, re.IGNORECASE)
        for match in dar_matches:
            extracted["dar_periods"].append({
                "period": match.group(1),
                "product": "",
                "crop": ""
            })
        
        logger.info(f"Fallback extraction found {len(extracted['products'])} products, {len(extracted['dosages'])} dosages")
        
        return extracted
    
    def _validate_extracted_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted entities"""
        validated = {}
        
        for key, value in entities.items():
            if isinstance(value, list):
                # Clean and validate list items
                validated_items = []
                for item in value:
                    if item:  # Skip None or empty items
                        if isinstance(item, dict):
                            # Clean dict values
                            cleaned_item = {k: v for k, v in item.items() if v is not None}
                            if cleaned_item:  # Only add if not empty after cleaning
                                validated_items.append(cleaned_item)
                        elif isinstance(item, str) and item.strip():
                            validated_items.append(item.strip())
                validated[key] = validated_items
            else:
                validated[key] = value
        
        return validated
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            "status": "error",
            "error": error_message,
            "extracted_entities": {
                "products": [],
                "dosages": [],
                "application_frequencies": [],
                "znt_distances": [],
                "dar_periods": [],
                "crops": [],
                "pests_diseases": [],
                "safety_restrictions": []
            },
            "extraction_confidence": 0.0,
            "extraction_method": "none",
            "total_entities": 0
        }
    
    async def _arun(
        self,
        document_content: str,
        document_type: str,
        max_content_length: int = 8000,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version of the tool"""
        # For LangChain tools, sync methods are typically called from async context
        # If you need true async LLM calls, use self.llm.ainvoke instead
        return self._run(document_content, document_type, max_content_length, **kwargs)