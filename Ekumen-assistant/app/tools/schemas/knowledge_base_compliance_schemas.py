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


class WebVerificationResult(BaseModel):
    """Result of web verification for a single item"""
    item_name: str = Field(description="Name of the verified item")
    item_type: str = Field(description="Type of item (product or substance)")
    verification_status: str = Field(description="Verification status (verified, not_found, error)")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in verification result")
    website_results: Dict[str, Any] = Field(default_factory=dict, description="Results from each website")
    violations: List[ComplianceViolation] = Field(default_factory=list, description="Found violations")
    warnings: List[ComplianceWarning] = Field(default_factory=list, description="Found warnings")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


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
    
    @field_validator('uncertain_products', 'uncertain_substances')
    @classmethod
    def validate_lists(cls, v):
        if not isinstance(v, list):
            return []
        return [item for item in v if item and isinstance(item, str)]


class WebComplianceVerifierOutput(BaseModel):
    """Output for web compliance verification"""
    status: str = Field(description="Overall verification status")
    verification_status: str = Field(description="Verification status (success, partial, failed)")
    verification_results: Dict[str, Any] = Field(description="Detailed verification results")
    total_products_verified: int = Field(description="Number of products verified")
    total_substances_verified: int = Field(description="Number of substances verified")
    total_violations: int = Field(description="Total violations found")
    total_warnings: int = Field(description="Total warnings found")
    document_id: str = Field(description="Document identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Verification timestamp")


class UsageLimitValidationResult(BaseModel):
    """Result of usage limit validation for a single product"""
    product_name: str = Field(description="Name of the validated product")
    dosage_compliance: str = Field(description="Dosage compliance status")
    frequency_compliance: str = Field(description="Application frequency compliance status")
    seasonal_compliance: str = Field(description="Seasonal application compliance status")
    znt_compliance: str = Field(description="Buffer zone compliance status")
    dar_compliance: str = Field(description="Pre-harvest interval compliance status")
    violations: List[ComplianceViolation] = Field(default_factory=list, description="Found violations")
    warnings: List[ComplianceWarning] = Field(default_factory=list, description="Found warnings")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class UsageLimitValidatorInput(BaseModel):
    """Input for usage limit validation"""
    extracted_entities: Dict[str, Any] = Field(description="Extracted regulatory entities from previous tool")
    document_id: str = Field(description="Document identifier for tracking")
    
    @field_validator('extracted_entities')
    @classmethod
    def validate_dicts(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Input must be a dictionary")
        return v


class UsageLimitValidatorOutput(BaseModel):
    """Output for usage limit validation"""
    status: str = Field(description="Overall validation status")
    validation_results: Dict[str, Any] = Field(description="Detailed validation results")
    total_products_validated: int = Field(description="Number of products validated")
    total_violations: int = Field(description="Total violations found")
    total_warnings: int = Field(description="Total warnings found")
    document_id: str = Field(description="Document identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Validation timestamp")




class RegulatoryEntityExtractorInput(BaseModel):
    """Input for regulatory entity extraction"""
    document_content: str = Field(description="Full text content of the agricultural document")
    document_type: str = Field(description="Type of document (manual, product_spec, technical_sheet, etc.)")
    max_content_length: Optional[int] = Field(default=8000, description="Maximum content length to process")
    
    @field_validator('document_content')
    @classmethod
    def validate_content(cls, v):
        if not v or len(v.strip()) < 50:
            raise ValueError("Document content too short (minimum 50 characters)")
        return v


class RegulatoryEntityExtractorOutput(BaseModel):
    """Output for regulatory entity extraction"""
    status: str = Field(description="Overall extraction status")
    extraction_results: Dict[str, Any] = Field(description="Detailed extraction results")
    total_entities_extracted: int = Field(description="Total number of entities extracted")
    extraction_confidence: float = Field(ge=0.0, le=1.0, description="Overall extraction confidence")
    document_type: str = Field(description="Type of document processed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Extraction timestamp")
