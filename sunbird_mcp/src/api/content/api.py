import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from core.base import BaseProcessor, BaseConfig
from models.content_models import ContentRequest, ContentResponse
from .validation import validate_content_request
from config import settings
import logging

logger = logging.getLogger(__name__)

class ContentConfig(BaseConfig):
    """Configuration for the Content API processor."""
    api_name: str = "content"
    description: str = "Retrieve educational content"
    timeout: int = 30
    base_url: str = settings.API_BASE_URL
    content_endpoint: str = settings.API_ENDPOINT_READ
    max_retries: int = 3

    @property
    def full_content_url(self) -> str:
        """Get the full content URL by combining base URL and endpoint."""
        return f"{self.base_url.rstrip('/')}{self.content_endpoint}"

async def retrieve_content_ids(content_id: str, config: Optional[ContentConfig] = None) -> (List[str], str):
    """
    Helper function to retrieve leaf node content IDs for a given content ID.
    Returns (content_ids, error_message)
    """
    config = config or ContentConfig()
    try:
        api_url = f"{config.full_content_url}/{content_id}"
        timeout = aiohttp.ClientTimeout(total=config.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, headers={"Content-Type": "application/json"}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["result"]["content"].get("leafNodes", []), None
                error_data = await response.text()
                return None, f"Sunbird API request failed with status {response.status}: {error_data}"
    except Exception as e:
        return None, f"Failed to process request: {str(e)}"

async def fetch_and_filter(session, content_id, artifact_urls, config: Optional[ContentConfig] = None):
    """
    Fetch content metadata and filter for PDF artifacts.
    """
    config = config or ContentConfig()
    try:
        api_url = f"{config.full_content_url}/{content_id}"
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                content = data.get("result", {}).get("content", {})
                excluded_mime = settings.EXCLUDED_MIME_TYPE
                if (
                    content.get("mimeType") != excluded_mime and
                    content.get("mimeType") == settings.PDF_MIME_TYPE and
                    content.get("streamingUrl")
                ):
                    artifact_urls.append(content.get("streamingUrl"))
            else:
                logger.warning(f"Error with {content_id}: API returned status {response.status}")
    except Exception as e:
        logger.error(f"Error with {content_id}: {str(e)}", exc_info=True)

async def run_concurrent_fetches(session, content_ids, artifact_urls, config: Optional[ContentConfig] = None, limit=20):
    semaphore = asyncio.Semaphore(limit)
    async def fetch_with_limit(content_id):
        async with semaphore:
            await fetch_and_filter(session, content_id, artifact_urls, config=config)
    tasks = [fetch_with_limit(content_id) for content_id in content_ids]
    await asyncio.gather(*tasks)

class ContentProcessor(BaseProcessor[ContentRequest]):
    """
    Processor for handling content retrieval requests (PDF artifact URLs for a book).
    """
    def __init__(self, config: Optional[ContentConfig] = None):
        super().__init__(config or ContentConfig())
        self.config = self.config or ContentConfig()
        self.session = None

    async def initialize(self):
        """Initialize the HTTP session with connection pooling (if needed in future)."""
        pass

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # No session to close, but method is required for async context manager
        pass

    async def pre_process(self, request_data: Dict[str, Any]) -> ContentRequest:
        validated, errors = validate_content_request(request_data)
        if errors:
            raise ValueError(errors)
        return ContentRequest(**validated)

    async def execute(self, request: ContentRequest) -> Dict[str, Any]:
        # Step 1: Retrieve leaf node content IDs
        content_ids, error = await retrieve_content_ids(request.content_id, config=self.config)
        if error:
            return {"error": error, "artifact_urls": [], "count": 0, "message": "Failed to retrieve content IDs"}
        if not content_ids or not isinstance(content_ids, list):
            return {"error": "No content IDs found for the given content_id", "artifact_urls": [], "count": 0, "message": "No content found"}
        artifact_urls = []
        # Step 2: Fetch and filter artifact URLs concurrently
        async with aiohttp.ClientSession() as session:
            await run_concurrent_fetches(session, content_ids, artifact_urls, config=self.config, limit=20)
        return {
            "artifact_urls": artifact_urls,
            "count": len(artifact_urls),
            "message": "Successfully retrieved artifact URLs for non-ECML content"
        }

    async def post_process(self, response: Dict[str, Any]) -> ContentResponse:
        # If error, fill error field
        error = response.get("error")
        return ContentResponse(
            artifact_urls=response.get("artifact_urls", []),
            count=response.get("count", 0),
            message=response.get("message", ""),
            error=error
        )

async def get_content_artifacts(content_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for content artifact retrieval. Creates a new ContentProcessor instance for each request.
    Args:
        content_params: Dictionary containing content retrieval parameters (must include content_id)
    Returns:
        Dict containing artifact URLs, count, message, and error (if any)
    """
    async with ContentProcessor() as processor:
        result = await processor.process(content_params)
        return result.dict()
