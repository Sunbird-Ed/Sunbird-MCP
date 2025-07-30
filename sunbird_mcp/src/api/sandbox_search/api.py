# d:\\sunbird_mcp\\Sunbird-MCP\\sunbird_mcp\\src\\api\\sandbox_search\\api.py
"""Sandbox Search API implementation."""
import aiohttp
import logging
import json
from typing import Any, Dict, Optional, List

from pydantic import ValidationError

from core.base import BaseProcessor, BaseConfig
from models.search_models import SearchRequest, SearchResponse
from .validation import validate_search_params
from config import settings
from utils.exceptions import ValidationError as AppValidationError, SunbirdAPIError

logger = logging.getLogger(__name__)

class SandboxSearchConfig(BaseConfig):
    """Configuration for the Sandbox Search API processor."""
    api_name: str = "sandbox_search"
    description: str = "Search for educational content in Sunbird Sandbox"
    timeout: int = 30
    base_url: str = settings.SANDBOX_API_BASE_URL
    search_endpoint: str = "/api/content/v1/search"
    max_retries: int = 3
    default_limit: int = 10
    max_limit: int = 100
    
    @property
    def full_search_url(self) -> str:
        """Get the full search URL by combining base URL and endpoint with required query params."""
        return f"{self.base_url.rstrip('/')}{self.search_endpoint}?orgdetails=orgName,email&framework=NCF"

class SandboxSearchProcessor(BaseProcessor[SearchRequest]):
    """Processor for handling search requests in the Sandbox environment."""
    
    def __init__(self, config: Optional[SandboxSearchConfig] = None):
        super().__init__(config or SandboxSearchConfig())
        self.session = None

    async def initialize(self):
        """Initialize the HTTP session with connection pooling."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            connector=aiohttp.TCPConnector(limit=100)
        )

    async def pre_process(self, request_data: Dict[str, Any]) -> SearchRequest:
        """
        Validate and transform search parameters for sandbox environment.
        
        Args:
            request_data: Raw request data
            
        Returns:
            Validated SearchRequest object
        """
        logger.debug("Pre-processing sandbox search request: %s", request_data)
        validated, errors = validate_search_params(request_data)
        if errors:
            logger.warning("Validation failed: %s", errors)
            raise AppValidationError("Invalid search parameters", errors)
            
        # Ensure required filters for sandbox are included
        if 'status' not in validated['filters']:
            validated['filters']['status'] = ["Live"]
            
        return SearchRequest(**validated)
    
    async def execute(self, request: SearchRequest) -> Dict[str, Any]:
        """
        Execute the search operation against Sunbird Sandbox API.
        
        Args:
            request: Validated search request
            
        Returns:
            Raw API response as a dictionary
        """
        payload = self._build_search_payload(request)
        url = self.config.full_search_url
        logger.debug("Sending search request to %s with payload: %s", url, payload)
        
        try:
            async with self.session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error("Sandbox Search API request failed for URL %s: %s", url, str(e), exc_info=True)
            raise SunbirdAPIError(f"Failed to execute search in sandbox: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error during sandbox search: %s", str(e), exc_info=True)
            raise SunbirdAPIError("An unexpected error occurred during sandbox search")

    async def post_process(self, response: Dict[str, Any]) -> SearchResponse:
        """
        Transform the raw search response into a standardized format.
        
        Args:
            response: Raw API response
            
        Returns:
            Standardized SearchResponse object with the following structure:
            {
                "success": bool,
                "data": {
                    "content": List[Dict],  # List of content items
                    "count": int,          # Total number of results
                    "facets": List[Dict]    # Facet information
                },
                "metadata": {
                    "api": str,
                    "version": str,
                    "total": int,
                    "responseCode": str,
                    "ts": str
                }
            }
        """
        try:
            result = response.get("result", {})
            content = result.get("content", [])
            facets = result.get("facets", [])
            count = result.get("count", 0)
            
            return SearchResponse(
                success=response.get("responseCode") == "OK",
                data={
                    "content": self._process_search_results(content),
                    "count": count,
                    "facets": facets
                },
                metadata={
                    "api": self.config.api_name,
                    "version": response.get("ver", "1.0"),
                    "total": count,
                    "responseCode": response.get("responseCode"),
                    "ts": response.get("ts"),
                    "params": response.get("params", {})
                }
            )
        except Exception as e:
            logger.error("Error processing sandbox search response: %s", str(e), exc_info=True)
            raise SunbirdAPIError("Failed to process sandbox search results")

    def _build_search_payload(self, request: SearchRequest) -> Dict[str, Any]:
        """
        Build the search request payload according to Sunbird Sandbox API spec.
        
        Args:
            request: Validated search request
            
        Returns:
            Payload dictionary for the API request
        """
        # Ensure required fields are included
        fields = set(request.fields or settings.SANDBOX_DEFAULT_FIELDS)
        fields.update(["identifier", "name", "contentType", "resourceType", "mimeType"])
        
        return {
            "request": {
                "filters": request.filters or {},
                "query": request.query,
                "limit": request.limit,
                "offset": request.offset,
                "fields": list(fields),
                "facets": request.facets or settings.SANDBOX_VALID_FACETS,
                "sort_by": request.sort_by or {"lastPublishedOn": "desc"}
            }
        }
    
    def _process_search_results(self, content_items: list) -> List[Dict[str, Any]]:
        """
        Process and format the search results from the Sunbird Sandbox API.
        
        Args:
            content_items: List of content items from the API response
            
        Returns:
            List of processed content items with only essential fields
        """
        processed_items = []
        
        for item in content_items:
            # Create a new dict with only the essential fields
            processed_item = {
                "identifier": item.get("identifier"),
                "name": item.get("name"),
                "contentType": item.get("contentType"),
                "mimeType": item.get("mimeType"),
                "subject": item.get("subject", []),
                "se_subjects": item.get("se_subjects", []),
                "se_mediums": item.get("se_mediums", []),
                "se_boards": item.get("se_boards", []),
                "se_gradeLevels": item.get("se_gradeLevels", [])
            }
            
            processed_items.append(processed_item)
            
        return processed_items

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()


async def search_sandbox_content(search_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for educational content in Sunbird Sandbox environment.
    
    This is the main entry point for the sandbox search functionality.
    
    Args:
        search_params: Dictionary containing search parameters:
            - query (str): Search query string
            - filters (dict): Content filters
            - limit (int): Max results (1-100)
            - offset (int): Pagination offset
            - sort_by (dict): Sorting criteria
            - fields (list): Fields to include
            - facets (list): Facets to include
            
    Returns:
        Dict containing search results in standardized format
    """
    async with SandboxSearchProcessor() as processor:
        result = await processor.process(search_params)
        return result.dict()
