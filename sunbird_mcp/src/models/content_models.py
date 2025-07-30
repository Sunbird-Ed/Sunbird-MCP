from typing import List, Optional
from pydantic import BaseModel, Field

class ContentRequest(BaseModel):
    """Request model for retrieving downloadable content artifacts for a specific book from SUNBIRD."""
    content_id: str = Field(..., description="The SUNBIRD content ID (starts with 'do_')")
    fields: Optional[List[str]] = Field(default_factory=list, description="Optional list of fields to include in the response.")

class ContentResponse(BaseModel):
    """Response model for downloadable content artifacts."""
    artifact_urls: List[str] = Field(..., description="List of direct PDF URLs.")
    count: int = Field(..., description="Number of URLs returned.")
    message: str = Field(..., description="Status message.")
    error: Optional[str] = Field(None, description="Error message, if any.")