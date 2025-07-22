# d:\sunbird_mcp\Sunbird-MCP\sunbird_mcp\src\models\search_models.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class SearchFilter(BaseModel):
    """Model for search filters."""
    contentTypes: Optional[List[str]] = None
    status: Optional[List[str]] = None
    objectType: Optional[List[str]] = None

class SearchRequest(BaseModel):
    """Search request model."""
    query: str = ""
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: Dict[str, str] = Field(default_factory=dict)
    fields: List[str] = Field(default_factory=list)
    facets: List[str] = Field(default_factory=list)

class SearchResultItem(BaseModel):
    """Model for individual search result item."""
    identifier: str
    name: str
    content_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchResponse(BaseModel):
    """Search response model."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None