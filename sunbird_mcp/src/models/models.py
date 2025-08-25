"""
Data models for the Sunbird MCP server.

This module defines the Pydantic models used for request/response validation
and data transformation throughout the application.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime, timezone

# Request Models
class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request ID for debugging"
    )


# Utility Models
class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of external dependencies"
    )


class APIMetadata(BaseModel):
    """API metadata model."""
    name: str
    version: str
    description: str
    status: str
    endpoints: List[Dict[str, str]]
    documentation: Optional[HttpUrl] = None
    