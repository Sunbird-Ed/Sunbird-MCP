# How to Integrate a New API into Sunbird MCP

This guide provides a step-by-step process for adding a new API to the Sunbird MCP server, using the search API as a reference. Follow these steps to ensure your new API is robust, maintainable, and consistent with the existing codebase.

---

## 1. **Overview & Prerequisites**
- Ensure you have a working Sunbird MCP server setup.
- Familiarize yourself with the existing code structure, especially the `search` API implementation.
- All new APIs should follow the modular, processor-based, and Pydantic-validated pattern.

---

## 2. **Create Request/Response Models**
- Define your request and response data structures using Pydantic models.
- Place them in a new or existing file in `src/models/` (e.g., `content_models.py`).

**Example:**
```python
# src/models/content_models.py
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ContentRequest(BaseModel):
    content_id: str = Field(..., description="The SUNBIRD content ID (starts with 'do_')")
    fields: Optional[List[str]] = Field(default_factory=list)

class ContentResponse(BaseModel):
    success: bool
    data: Dict[str, any]
    metadata: Dict[str, any] = Field(default_factory=dict)
    error: Optional[str] = None
```

---

## 3. **Write Validation Logic**
- Create a validation module (e.g., `src/api/content/validation.py`).
- Implement functions to validate and sanitize input parameters, similar to `validate_search_params`.
- Use centralized config for allowed values.

**Example:**
```python
# src/api/content/validation.py
def validate_content_params(params: Dict[str, any]) -> Tuple[Dict[str, any], List[str]]:
    errors = []
    validated = {...}  # Fill with defaults and validated values
    # Add validation logic here
    return validated, errors
```

---

## 4. **Implement the Processor Class**
- Create a processor class in `src/api/content/api.py`, subclassing `BaseProcessor`.
- Implement `pre_process`, `execute`, and `post_process` methods.
- Use async/await for all I/O operations.

**Example:**
```python
# src/api/content/api.py
from core.base import BaseProcessor
from .validation import validate_content_params
from models.content_models import ContentRequest, ContentResponse

class ContentProcessor(BaseProcessor[ContentRequest]):
    async def pre_process(self, request_data: Dict[str, any]) -> ContentRequest:
        validated, errors = validate_content_params(request_data)
        if errors:
            raise ValueError(errors)
        return ContentRequest(**validated)
    async def execute(self, request: ContentRequest) -> Dict[str, any]:
        # Call external API or perform logic
        ...
    async def post_process(self, response: Dict[str, any]) -> ContentResponse:
        # Format and return response
        ...
```

---

## 5. **Register the Tool in `server.py`**
- Import your processor and models.
- Register the new tool using the `@server.tool()` decorator.
- The tool function should accept a Pydantic model and return a dict.

**Example:**
```python
from models.content_models import ContentRequest
from api.content import get_content_details

@server.tool()
async def get_content(content_params: ContentRequest) -> dict:
    return await get_content_details(content_params.model_dump())
```

---

## 6. **Configuration and Settings**
- Add any new config options to `src/config.py`.
- Use environment variables or defaults as needed.
- Reference config in your validation and processor logic.

---

## 7. **Testing and Best Practices**
- Write unit tests for validation, processor, and tool registration.
- Test with both valid and invalid inputs.
- Use async test frameworks (e.g., pytest-asyncio) for async code.
- Log errors and edge cases for easier debugging.

---

## 8. **Directory Structure Example**
```
src/
  api/
    content/
      __init__.py
      api.py
      validation.py
    search/
      ...
  models/
    content_models.py
    search_models.py
  config.py
  server.py
```

---

## 9. **Tips for Extensibility and Maintainability**
- Keep validation, models, and processor logic in separate files.
- Use Pydantic for all request/response schemas.
- Centralize allowed values and config in `config.py`.
- Use descriptive docstrings and type hints everywhere.
- Follow the async/await pattern for all I/O.
- Use logging for all errors and important events.

---

## 10. **PEP8 and Documentation Standards**
- Use 4-space indentation, snake_case for variables/functions, CamelCase for classes.
- Add docstrings to all public classes, methods, and functions.
- Keep lines under 79 characters where possible.
- Group imports by standard library, third-party, and local modules.

---

## 11. **Sample Tool Function Template**
```python
@server.tool()
async def my_new_api_tool(params: MyRequestModel) -> dict:
    """
    Detailed description of what this tool does.
    Args:
        params (MyRequestModel): Description of input model.
    Returns:
        dict: Description of output.
    """
    return await my_processor_function(params.model_dump())
```

---

## 12. **Final Checklist**
- [ ] Models defined in `models/`
- [ ] Validation in `api/<api>/validation.py`
- [ ] Processor in `api/<api>/api.py`
- [ ] Tool registered in `server.py`
- [ ] Config updated if needed
- [ ] Tests written and passing
- [ ] Docstrings and PEP8 compliance

---

**By following this guide, you can add new APIs to Sunbird MCP that are robust, maintainable, and consistent with the rest of the system.** 