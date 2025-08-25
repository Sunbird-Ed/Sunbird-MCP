# Sunbird MCP Server Architecture

This document outlines the structure and design of the Sunbird MCP Server implementation.

## Project Structure

```
sunbird_mcp/
├── src/
│   ├── __init__.py
│   ├── config.py          # Application configuration and settings
│   ├── server.py          # MCP server entry point
│   │
│   ├── core/              # Core application components
│   │   ├── __init__.py
│   │   └── base.py        # Abstract base classes and interfaces
│   │
│   ├── models/            # Data models and schemas
│   │   ├── __init__.py
│   │   └── models.py      # Pydantic models for data validation
│   │
│   ├── api/               # API implementations
│   │   ├── __init__.py
│   │   │
│   │   ├── search/        # Search API
│   │   │   ├── __init__.py
│   │   │   ├── api.py     # Search API implementation
│   │   │   └── validation.py  # Search-specific validation
│   │   │
│   │   └── content/       # Content API
│   │       ├── __init__.py
│   │       ├── api.py     # Content API implementation
│   │       └── validation.py  # Content-specific validation
│   │
│   └── utils/             # Shared utilities
│       ├── __init__.py
│       ├── exceptions.py  # Custom exception hierarchy
│       └── http.py        # HTTP client with retries
```

## Key Components

### 1. Core Module
- **`base.py`**: Abstract base classes for processors and models
- **`models/`**: Pydantic models for request/response validation
  - `__init__.py`: Exports all models
  - `models.py`: Model definitions
- **`utils/exceptions.py`**: Structured error handling with specific exception types

### 2. API Module
- **`search/`**: Search API implementation
  - `api.py`: Main search functionality
  - `validation.py`: Search-specific validation logic
- **`content/`**: Content API implementation
  - `api.py`: Content retrieval and operations
  - `validation.py`: Content-specific validation logic
- Each API follows the standard three-step flow:
  1. **Pre-processing**: Input validation and transformation
  2. **Execution**: Core business logic
  3. **Post-processing**: Response formatting

### 3. Utilities
- **`http.py`**: Reusable HTTP client with retry logic (having a common get,post request etc)
- **`validation.py`**: Common validation rules and helpers (having a common validation logic) if needed

## Design Principles

1. **Separation of Concerns**
   - Clear boundaries between components
   - Single responsibility principle

2. **Type Safety**
   - Pydantic models for request/response validation
   - Type hints throughout the codebase

3. **Error Handling**
   - Structured error responses
   - Meaningful error messages
   - Proper HTTP status codes
   - API-specific validation errors
   - Centralized exception handling in `utils/exceptions.py`

4. **Extensibility**
   - Easy to add new API endpoints
   - Pluggable components

## Next Steps

1. Implement remaining API endpoints
2. Add authentication and authorization
3. Set up logging and monitoring
4. Add comprehensive test coverage
5. Documentation and examples



## More Details on Core/ -pre process post
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseProcessor(ABC, Generic[T]):
    """Base class for API processors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def pre_process(self, request_data: Dict[str, Any]) -> T:
        """Validate and transform input parameters."""
        pass
    
    @abstractmethod
    async def execute(self, request: T) -> Any:
        """Execute the API call."""
        pass
    
    @abstractmethod
    async def post_process(self, response: Any) -> Dict[str, Any]:
        """Transform the API response."""
        pass
    
    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing pipeline."""
        try:
            validated = await self.pre_process(request_data)
            result = await self.execute(validated)
            return await self.post_process(result)
        except Exception as e:
            # Handle errors consistently
            return {"success": False, "error": str(e)}
```

Apis inherit from BaseProcessor and implement the three methods -pre_process, execute, post_process

example 
```python
from typing import Dict, Any
from pydantic import Field
from ..core.base import BaseProcessor
from ..core.models import BaseRequest, BaseResponse

class SearchRequest(BaseRequest):
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(10, ge=1, le=100)
    offset: int = 0

class SearchResponse(BaseResponse):
    results: list
    total: int
    facets: Optional[Dict[str, Any]] = None

class SearchProcessor(BaseProcessor[SearchRequest]):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = f"{self.config['api_base_url']}/api/content/v1/search"
    
    async def pre_process(self, request_data: Dict[str, Any]) -> SearchRequest:
        return SearchRequest(**request_data)
    
    async def execute(self, request: SearchRequest) -> Dict[str, Any]:
        # Make API call
        payload = {"request": request.dict(exclude_none=True)}
        # ... make HTTP request ...
        return response.json()
    
    async def post_process(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return SearchResponse(
            success=True,
            results=response.get("result", {}).get("content", []),
            total=response.get("result", {}).get("count", 0),
            facets=response.get("result", {}).get("facets")
        ).dict()
```
Note: This is only an example for understanding i have not coded as such


Finally in server.py only function call would be enough