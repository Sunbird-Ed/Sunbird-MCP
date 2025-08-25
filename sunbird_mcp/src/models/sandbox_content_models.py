from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class SandboxContentRequest(BaseModel):
    """Request model for retrieving content from the Sandbox environment."""
    content_id: str = Field(..., description="The Sandbox content ID (starts with 'do_')")

    @validator('content_id')
    def validate_content_id(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("content_id must be a non-empty string")
        if not v.startswith('do_'):
            raise ValueError("content_id must start with 'do_'")
        return v

class SandboxContentItem(BaseModel):
    """Model for individual content item in the response."""
    identifier: str = Field(..., description="Unique identifier of the content")
    name: str = Field(..., description="Name/title of the content")
    previewUrl: Optional[str] = Field(None, description="URL to preview the content")
    artifactUrl: Optional[str] = Field(None, description="Direct URL to the content artifact")
    mimeType: str = Field(..., description="MIME type of the content")
    primaryCategory: str = Field(..., description="Primary category of the content")
    subject: List[str] = Field(default_factory=list, description="List of subjects")
    gradeLevel: List[str] = Field(default_factory=list, description="List of grade levels")
    medium: List[str] = Field(default_factory=list, description="List of mediums")
    board: Optional[str] = Field(None, description="Education board")
    lastPublishedOn: Optional[str] = Field(None, description="Timestamp of last publication")

class SandboxContentResponse(BaseModel):
    """Response model for sandbox content retrieval."""
    success: bool = Field(..., description="Indicates if the request was successful")
    content: List[SandboxContentItem] = Field(..., description="List of content items")
    count: int = Field(..., description="Number of content items returned")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message, if any")

    def dict(self, **kwargs):
        # Ensure the response is properly serialized
        return {
            "success": self.success,
            "content": [item.dict(exclude_none=True) for item in self.content],
            "count": self.count,
            "message": self.message,
            "error": self.error
        }
