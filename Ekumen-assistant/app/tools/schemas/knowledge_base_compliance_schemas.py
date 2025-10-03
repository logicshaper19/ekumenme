"""
Pydantic schemas for Knowledge Base Compliance Agent
Structured input/output for document compliance validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ComplianceDecision(str, Enum):
    """Final compliance decision for documents"""
    AUTO_APPROVE = "auto_approve"
    FLAG_FOR_REVIEW = "flag_for_review"
    UNCERTAIN = "uncertain"


class DocumentType(str, Enum):
    """Types of agricultural documents"""
    PRODUCT_MANUAL = "product_manual"
    TECHNICAL_SHEET = "technical_sheet"
    SAFETY_DATA_SHEET = "safety_data_sheet"
    APPLICATION_GUIDE = "application_guide"
    REGULATORY_NOTICE = "regulatory_notice"


class ExtractedEntity(BaseModel):
    """Extracted regulatory entity from document"""
    entity_type: str = Field(description="Type of entity (product, substance, dosage, etc.)")
    name: str = Field(description="Name or identifier of the entity")
    value: Optional[str] = Field(default=None, description="Value or details of the entity")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score")


class ComplianceViolation(BaseModel):
    """Regulatory compliance violation"""
    violation_type: str = Field(description="Type of violation")
    description: str = Field(description="Description of the violation")
    severity: str = Field(description="Severity level (critical, major, minor)")
    regulation_reference: Optional[str] = Field(default=None, description="Reference to regulation")
    recommendation: Optional[str] = Field(default=None, description="Recommended action")


class ComplianceWarning(BaseModel):
    """Compliance warning (non-blocking issue)"""
    warning_type: str = Field(description="Type of warning")
    description: str = Field(description="Description of the warning")
    recommendation: Optional[str] = Field(default=None, description="Recommended action")


class DocumentComplianceInput(BaseModel):
    """Input for document compliance validation"""
    document_content: str = Field(description="Full text content of the document")
    document_type: DocumentType = Field(description="Type of document")
    document_id: str = Field(description="Unique document identifier")
    organization_id: Optional[str] = Field(default=None, description="Organization submitting the document")


class DocumentComplianceOutput(BaseModel):
    """Output for document compliance validation"""
    document_id: str = Field(description="Document identifier")
    decision: ComplianceDecision = Field(description="Final compliance decision")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence in the decision")
    
    # Extracted entities
    extracted_entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted regulatory entities")
    
    # Compliance results
    violations: List[ComplianceViolation] = Field(default_factory=list, description="Compliance violations found")
    warnings: List[ComplianceWarning] = Field(default_factory=list, description="Compliance warnings")
    
    # Detailed results
    product_validations: List[Dict[str, Any]] = Field(default_factory=list, description="Product validation results")
    substance_validations: List[Dict[str, Any]] = Field(default_factory=list, description="Substance validation results")
    usage_validations: List[Dict[str, Any]] = Field(default_factory=list, description="Usage validation results")
    
    # Metadata
    processing_time: float = Field(description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")
    tool_results: Dict[str, Any] = Field(default_factory=dict, description="Raw tool execution results")
    
    @field_validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class EntityExtractionInput(BaseModel):
    """Input for entity extraction"""
    document_content: str = Field(description="Document content to extract entities from")
    document_type: DocumentType = Field(description="Type of document")


class EntityExtractionOutput(BaseModel):
    """Output for entity extraction"""
    entities: List[ExtractedEntity] = Field(description="Extracted entities")
    extraction_confidence: float = Field(ge=0.0, le=1.0, description="Overall extraction confidence")
    processing_time: float = Field(description="Extraction time in seconds")


class ProductValidationInput(BaseModel):
    """Input for product validation"""
    product_name: str = Field(description="Name of the product to validate")
    active_substances: List[str] = Field(default_factory=list, description="Active substances in the product")
    document_id: str = Field(description="Document identifier for tracking")


class ProductValidationOutput(BaseModel):
    """Output for product validation"""
    product_name: str = Field(description="Product name")
    is_authorized: bool = Field(description="Whether product is authorized in EPHY")
    authorization_status: Optional[str] = Field(default=None, description="Authorization status")
    violations: List[ComplianceViolation] = Field(default_factory=list, description="Product-specific violations")
    warnings: List[ComplianceWarning] = Field(default_factory=list, description="Product-specific warnings")
    ephy_data: Optional[Dict[str, Any]] = Field(default=None, description="EPHY database information")
