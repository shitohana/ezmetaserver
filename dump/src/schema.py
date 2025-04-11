from typing import List, Optional

from pydantic import BaseModel, Field


class EzMetaFetchRequest(BaseModel):
    """Schema for API requests to ezmetafetch"""

    # Search parameters
    terms: Optional[List[str]] = Field(
        default=None,
        description="List of search terms to query the database"
    )
    ids: Optional[List[int]] = Field(
        default=None,
        description="List of specific IDs to fetch metadata for"
    )

    max_results: int = Field(
        gt=0, le=1000,
        default=100,
        description="Maximum number of results to return"
    )

    # HTTP configuration
    api_key: Optional[str] = Field(
        default=None,
        description="NCBI API key for higher request rate limits"
    )

    class Config:
        schema_extra = {
            "example": {
                "terms": ["SARS-CoV-2", "human"],
                "db": "sra",
                "max_results": 50,
                "api_key": "your_api_key_here"
            }
        }


class EzMetaFetchResponse(BaseModel):
    """Schema for API responses from ezmetafetch"""
    search_ids: Optional[List[int]] = Field(
        default=None,
        description="Search NCBI IDs"
    )
    ids: Optional[List[int]] = Field(
        default=None,
        description="All dumped IDs"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Metadata records for the requested IDs"
    )
    status: str = Field(
        description="Status of the request (success/error)"
    )
    message: Optional[str] = Field(
        default=None,
        description="Additional information about the request"
    )
