"""
Pydantic models and response classes for the Knowledge Base API
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from app.models.knowledge_base import DocumentType

# Standardized error response format
class StandardErrorResponse:
    """Standardized error response format for consistent API responses"""
    
    @staticmethod
    def create_error_response(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a standardized error response"""
        response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message
            }
        }
        if details:
            response["error"]["details"] = details
        return response
    
    @staticmethod
    def create_success_response(
        data: Any = None,
        message: str = "Operation completed successfully"
    ) -> Dict[str, Any]:
        """Create a standardized success response"""
        response = {
            "success": True,
            "message": message
        }
        if data is not None:
            response["data"] = data
        return response

# Pydantic request validation models
class DocumentSubmissionRequest(BaseModel):
    """Request model for document submission"""
    document_type: str = Field(..., description="Type of document")
    description: Optional[str] = Field(None, max_length=1000, description="Document description")
    tags: Optional[List[str]] = Field(None, max_items=10, description="Document tags")
    expiration_months: Optional[int] = Field(None, ge=1, le=60, description="Expiration in months")
    visibility: str = Field("internal", description="Document visibility")
    shared_with_organizations: Optional[List[str]] = Field(None, description="Shared organizations")
    shared_with_users: Optional[List[str]] = Field(None, description="Shared users")
    
    @validator('document_type')
    def validate_document_type(cls, v):
        valid_types = [t.value for t in DocumentType]
        if v not in valid_types:
            raise ValueError(f"Document type must be one of: {valid_types}")
        return v
    
    @validator('visibility')
    def validate_visibility(cls, v):
        valid_visibilities = ["internal", "shared", "public"]
        if v not in valid_visibilities:
            raise ValueError(f"Visibility must be one of: {valid_visibilities}")
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Limit tag length and count
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("Tag length cannot exceed 50 characters")
                if not tag.strip():
                    raise ValueError("Tags cannot be empty")
        return v

class DocumentSearchRequest(BaseModel):
    """Request model for document search"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    include_ekumen_content: bool = Field(True, description="Include Ekumen-provided content")

class DocumentListRequest(BaseModel):
    """Request model for document listing"""
    document_type: Optional[str] = Field(None, description="Filter by document type")
    visibility: Optional[str] = Field(None, description="Filter by visibility")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of records to return")

class SourceAttributionRequest(BaseModel):
    """Request model for source attribution"""
    query: str = Field(..., min_length=1, max_length=500, description="Query for source attribution")

class DocumentAnalyticsRequest(BaseModel):
    """Request model for document analytics"""
    period_days: int = Field(30, ge=1, le=365, description="Number of days to analyze")

class PaginatedResponse(BaseModel):
    """Standard paginated response format"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

def calculate_page_from_skip(skip: int, limit: int) -> int:
    """Convert skip/limit pagination to page number"""
    return (skip // limit) + 1

def create_paginated_response(
    items: List[Dict[str, Any]],
    total: int,
    page: int,
    per_page: int
) -> PaginatedResponse:
    """Create a standardized paginated response"""
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

def create_paginated_response_from_skip(
    items: List[Dict[str, Any]],
    total: int,
    skip: int,
    limit: int
) -> PaginatedResponse:
    """Create a standardized paginated response from skip/limit parameters"""
    page = calculate_page_from_skip(skip, limit)
    return create_paginated_response(items, total, page, limit)
