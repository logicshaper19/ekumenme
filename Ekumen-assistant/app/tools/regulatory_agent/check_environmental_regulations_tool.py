"""
Environmental Regulations LangChain Tool - Lightweight Wrapper
Extracted service logic to app/services/environmental_regulations_service.py
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import date
from langchain.tools import StructuredTool

from app.services.regulatory.environmental_regulations_service import EnvironmentalRegulationsService

logger = logging.getLogger(__name__)


async def check_environmental_regulations_async(
    practice_type: str,
    location: Optional[str] = None,
    environmental_impact: Optional[Dict[str, Any]] = None,
    amm_codes: Optional[List[str]] = None,
    crop_eppo_code: Optional[str] = None,
    field_size_ha: Optional[float] = None,
    application_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Check environmental regulations for agricultural practices with database integration.
    
    This tool provides comprehensive environmental compliance checking including:
    - ZNT (Zone de Non-Traitement) requirements from EPHY database
    - Water protection regulations
    - Biodiversity protection (Natura 2000, pollinators)
    - Air quality regulations
    - Nitrate directive compliance
    - Seasonal restrictions
    - Legal references and penalties
    
    Args:
        practice_type: Type of agricultural practice (spraying, fertilization, irrigation)
        location: Location (department, region) for regional regulations
        environmental_impact: Environmental impact assessment data including:
            - water_proximity_m: Distance to nearest water body in meters
            - water_body_type: Type of water body (stream, lake, etc.)
            - water_body_width_m: Width of water body in meters
            - drift_reduction_equipment: Equipment class for drift reduction
            - has_vegetation_buffer: Whether vegetation buffer is present
        amm_codes: List of AMM (Autorisation de Mise sur le Marché) codes to check
        crop_eppo_code: EPPO code of the crop being treated
        field_size_ha: Field size in hectares
        application_date: Planned application date
        
    Returns:
        Dict containing comprehensive environmental compliance analysis including:
        - regulations: List of applicable environmental regulations
        - znt_compliance: ZNT compliance analysis from EPHY database
        - product_environmental_data: Environmental fate data for products
        - water_body_classification: Water body classification and requirements
        - overall_compliance: Overall compliance status
        - environmental_risk: Environmental risk assessment
        - recommendations: Specific recommendations for compliance
        - critical_warnings: Critical warnings requiring immediate attention
        - seasonal_restrictions: Seasonal restrictions applicable
    """
    try:
        # Initialize service
        service = EnvironmentalRegulationsService()
        
        # Call service method
        result = await service.check_environmental_regulations(
            practice_type=practice_type,
            location=location,
            environmental_impact=environmental_impact,
            amm_codes=amm_codes,
            crop_eppo_code=crop_eppo_code,
            field_size_ha=field_size_ha,
            application_date=application_date
        )
        
        # Convert Pydantic model to dict for LangChain compatibility
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Error in environmental regulations tool: {e}")
        return {
            "error": str(e),
            "practice_type": practice_type,
            "location": location,
            "regulations": [],
            "znt_compliance": None,
            "product_environmental_data": None,
            "water_body_classification": None,
            "overall_compliance": "error",
            "environmental_risk": {
                "risk_level": "unknown",
                "risk_score": 1.0,
                "risk_factors": [f"Tool error: {str(e)}"]
            },
            "recommendations": ["Contact support for assistance"],
            "critical_warnings": [f"Tool error: {str(e)}"],
            "seasonal_restrictions": [],
            "generated_at": None
        }


# LangChain StructuredTool definition
check_environmental_regulations_tool = StructuredTool.from_function(
    func=check_environmental_regulations_async,
    name="check_environmental_regulations",
    description="""
    Check environmental regulations for agricultural practices with comprehensive database integration.
    
    Provides detailed environmental compliance analysis including ZNT requirements from EPHY database,
    water protection regulations, biodiversity protection, air quality regulations, nitrate directive
    compliance, seasonal restrictions, and legal references.
    
    Use this tool when you need to:
    - Check if agricultural practices comply with environmental regulations
    - Get ZNT (Zone de Non-Traitement) requirements for specific products
    - Assess environmental risks of planned agricultural activities
    - Get recommendations for environmental compliance
    - Check seasonal restrictions for specific practices
    
    The tool integrates with the EPHY database to provide real-time, accurate regulatory information
    and uses advanced caching for optimal performance.
    """,
    return_direct=False
)