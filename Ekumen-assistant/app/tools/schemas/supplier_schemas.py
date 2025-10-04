"""
Supplier Search Tool Schemas
Pydantic models for supplier search functionality
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SupplierInfo(BaseModel):
    """Information about a single supplier"""
    name: str = Field(description="Supplier company name")
    description: str = Field(description="Supplier description and services")
    url: str = Field(description="Supplier website URL")
    location: Optional[str] = Field(default=None, description="Supplier location/region")
    contact_info: Optional[str] = Field(default=None, description="Contact information if available")
    specialties: Optional[List[str]] = Field(default=None, description="Product/service specialties")


class SupplierSearchInput(BaseModel):
    """Input schema for supplier search"""
    query: str = Field(
        description="Search query for agricultural suppliers (e.g., 'fournisseur engrais azoté', 'distributeur tracteur')",
        min_length=3,
        max_length=200
    )


class SupplierSearchOutput(BaseModel):
    """Output schema for supplier search results"""
    success: bool = Field(description="Whether the search was successful")
    query: str = Field(description="Original search query")
    suppliers: List[SupplierInfo] = Field(description="List of found suppliers")
    total_found: int = Field(description="Total number of suppliers found")
    search_tips: List[str] = Field(description="Tips for contacting suppliers")
    error: Optional[str] = Field(default=None, description="Error message if search failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Search timestamp")
