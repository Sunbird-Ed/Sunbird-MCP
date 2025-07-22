# d:\sunbird_mcp\Sunbird-MCP\sunbird_mcp\src\api\search\api.py
import aiohttp
import logging
from typing import Any, Dict, Optional

from pydantic import ValidationError
import json

from core.base import BaseProcessor, BaseConfig
from models.search_models import SearchRequest, SearchResponse
from .validation import validate_search_params
from config import settings
from utils.exceptions import ValidationError as AppValidationError, SunbirdAPIError

logger = logging.getLogger(__name__)

class SearchConfig(BaseConfig):
    """Configuration for the Search API processor."""
    api_name: str = "search"
    description: str = "Search for educational content"
    timeout: int = 30
    base_url: str = settings.API_BASE_URL
    search_endpoint: str = settings.API_ENDPOINT_SEARCH
    max_retries: int = 3
    default_limit: int = 10
    max_limit: int = 100
    
    @property
    def full_search_url(self) -> str:
        """Get the full search URL by combining base URL and endpoint."""
        return f"{self.base_url.rstrip('/')}{self.search_endpoint}"

class SearchProcessor(BaseProcessor[SearchRequest]):
    """Processor for handling search requests."""
    
    def __init__(self, config: Optional[SearchConfig] = None):
        super().__init__(config or SearchConfig())
        self.session = None

    async def initialize(self):
        """Initialize the HTTP session with connection pooling."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            connector=aiohttp.TCPConnector(limit=100)
        )

    async def pre_process(self, request_data: Dict[str, Any]) -> SearchRequest:
        """Validate and transform search parameters."""
        logger.debug("Pre-processing search request: %s", request_data)
        validated, errors = validate_search_params(request_data)
        if errors:
            logger.warning("Validation failed: %s", errors)
            raise AppValidationError("Invalid search parameters", errors)
        return SearchRequest(**validated)
    
    async def execute(self, request: SearchRequest) -> Dict[str, Any]:
        """Execute the search operation against Sunbird API."""
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
            logger.error("Search API request failed for URL %s: %s", url, str(e), exc_info=True)
            raise SunbirdAPIError(f"Failed to execute search: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error during search: %s", str(e), exc_info=True)
            raise SunbirdAPIError("An unexpected error occurred during search")

    async def post_process(self, response: Dict[str, Any]) -> SearchResponse:
        """Transform the raw search response into a standardized format, including indexed books."""
        try:
            result = response.get("result", {})
            # Use _process_search_results to get indexed book list (as JSON string)
            try:
                books_json = _process_search_results(response)
                books = json.loads(books_json)
            except Exception as e:
                logger.error("Error in _process_search_results: %s", str(e), exc_info=True)
                books = {}
            return SearchResponse(
                success=True,
                data={
                    "books": books,
                    "count": result.get("count", 0),   
                },
                metadata={
                    "api": self.config.api_name,
                    "version": "1.0.0",
                    "total": result.get("count", 0)
                }
            )
        except Exception as e:
            logger.error("Error processing search response: %s", str(e), exc_info=True)
            raise SunbirdAPIError("Failed to process search results")

    def _build_search_payload(self, request: SearchRequest) -> Dict[str, Any]:
        """Build the search request payload according to Sunbird API spec."""
        return {
            "request": {
                "filters": request.filters or {},
                "query": request.query,
                "limit": request.limit,
                "offset": request.offset,
                "fields": request.fields or [],
                "facets": request.facets or [],
                "sort_by": request.sort_by or {"lastPublishedOn": "desc"}
            }
        }

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()

def _process_search_results(data: dict) -> str:
    """Process and format the search results from the Sunbird API."""
    book_list = {}
    for index, content in enumerate(data.get("result", {}).get("content", [])):
        book_details = {}
        book_details["name"] = content.get("name", "")
        book_details["identifier"] = content.get("identifier", "")
        book_details["se_subjects"] = content.get("se_subjects", [])
        book_details["se_mediums"] = content.get("se_mediums", [])
        book_details["se_boards"] = content.get("se_boards", [])
        book_details["se_gradeLevels"] = content.get("se_gradeLevels", [])
        book_number = f"book_{index+1}"
        book_list[book_number] = book_details
    return json.dumps(book_list, ensure_ascii=False)

async def search_sunbird_content(search_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for educational content on SUNBIRD platform.
    
    This is the main entry point for the search functionality. It creates a new
    SearchProcessor instance for each request to ensure thread safety and proper
    resource management.
    
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
        Dict containing search results
    """
    async with SearchProcessor() as processor:
        result = await processor.process(search_params)
        return result.dict()