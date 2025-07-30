"""Sandbox Content API implementation.

This module provides functionality to retrieve and process content from the Sunbird Sandbox environment.
"""
import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Set

from core.base import BaseProcessor, BaseConfig
from models.sandbox_content_models import SandboxContentRequest, SandboxContentResponse, SandboxContentItem
from .validation import validate_content_request
from config import settings
from utils.exceptions import ValidationError as AppValidationError, SunbirdAPIError

logger = logging.getLogger(__name__)

class SandboxContentConfig(BaseConfig):
    """Configuration for the Sandbox Content API processor."""
    api_name: str = "sandbox_content"
    description: str = "Retrieve educational content from Sunbird Sandbox"
    timeout: int = 30
    base_url: str = settings.SANDBOX_API_BASE_URL
    content_endpoint: str = "/api/content/v1/read"
    max_retries: int = 3
    max_concurrent: int = 20  # Maximum concurrent requests

    @property
    def full_content_url(self) -> str:
        """Get the full content URL by combining base URL and endpoint."""
        return f"{self.base_url.rstrip('/')}{self.content_endpoint}"

class SandboxContentProcessor(BaseProcessor[SandboxContentRequest]):
    """Processor for handling content retrieval from the Sandbox environment."""
    
    def __init__(self, config: Optional[SandboxContentConfig] = None):
        super().__init__(config or SandboxContentConfig())
        self.session = None
        self.visited_ids: Set[str] = set()
        self.content_items: List[SandboxContentItem] = []

    async def initialize(self):
        """Initialize the HTTP session with connection pooling."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            connector=aiohttp.TCPConnector(limit=100)
        )
        self.visited_ids = set()
        self.content_items = []

    async def pre_process(self, request_data: Dict[str, Any]) -> SandboxContentRequest:
        """Validate and transform request parameters."""
        validated, errors = validate_content_request(request_data)
        if errors:
            logger.warning(f"Validation failed: {errors}")
            raise AppValidationError("Invalid content parameters", errors)
        return SandboxContentRequest(**validated)

    async def execute(self, request: SandboxContentRequest) -> Dict[str, Any]:
        """Execute the content retrieval operation."""
        try:
            await self._process_content(request.content_id)
            return {
                "content": self.content_items,
                "count": len(self.content_items),
                "message": "Successfully retrieved content items",
                "success": True
            }
        except Exception as e:
            logger.error(f"Error processing content: {str(e)}", exc_info=True)
            return {
                "content": [],
                "count": 0,
                "message": f"Failed to retrieve content: {str(e)}",
                "success": False,
                "error": str(e)
            }

    async def _process_content(self, content_id: str) -> None:
        """Process a content item by ID, recursively handling collections."""
        if content_id in self.visited_ids:
            return
            
        self.visited_ids.add(content_id)
        
        try:
            # Fetch content details
            content = await self._fetch_content(content_id)
            if not content:
                return
                
            # Check if it's a collection
            if content.get("mimeType") == "application/vnd.ekstep.content-collection":
                # Process child nodes
                child_nodes = content.get("leafNodes", [])
                if child_nodes:
                    await self._process_child_nodes(child_nodes)
            else:
                # Process individual content item
                content_item = self._extract_content_item(content)
                if content_item:
                    self.content_items.append(content_item)
                    
        except Exception as e:
            logger.error(f"Error processing content {content_id}: {str(e)}", exc_info=True)
            raise

    async def _process_child_nodes(self, node_ids: List[str]) -> None:
        """Process multiple child nodes concurrently."""
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def process_node(node_id: str):
            async with semaphore:
                await self._process_content(node_id)
        
        tasks = [process_node(node_id) for node_id in node_ids]
        await asyncio.gather(*tasks)

    async def _fetch_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Fetch content details from the API."""
        url = f"{self.config.full_content_url}/{content_id}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result", {}).get("content")
                elif response.status == 404:
                    logger.warning(f"Content not found: {content_id}")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"API error for {content_id}: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching content {content_id}: {str(e)}", exc_info=True)
            raise

    def _extract_content_item(self, content: Dict[str, Any]) -> Optional[SandboxContentItem]:
        """Extract relevant fields from content metadata."""
        try:
            # Handle different field name variations
            subject = content.get("subject", [])
            if not subject and "se_subjects" in content:
                subject = content["se_subjects"]
                
            grade_level = content.get("gradeLevel", [])
            if not grade_level and "se_gradeLevels" in content:
                grade_level = content["se_gradeLevels"]
                
            medium = content.get("medium", [])
            if not medium and "se_mediums" in content:
                medium = content["se_mediums"]
                
            board = content.get("board")
            if not board and "se_boards" in content and content["se_boards"]:
                board = content["se_boards"][0]
            
            return SandboxContentItem(
                identifier=content.get("identifier", ""),
                name=content.get("name", ""),
                previewUrl=content.get("previewUrl"),
                artifactUrl=content.get("artifactUrl"),
                mimeType=content.get("mimeType", ""),
                primaryCategory=content.get("primaryCategory", ""),
                subject=subject if isinstance(subject, list) else [subject] if subject else [],
                gradeLevel=grade_level if isinstance(grade_level, list) else [grade_level] if grade_level else [],
                medium=medium if isinstance(medium, list) else [medium] if medium else [],
                board=board,
                lastPublishedOn=content.get("lastPublishedOn")
            )
        except Exception as e:
            logger.error(f"Error extracting content item: {str(e)}", exc_info=True)
            return None

    async def post_process(self, response: Dict[str, Any]) -> SandboxContentResponse:
        """Transform the raw response into a standardized format."""
        return SandboxContentResponse(
            success=response.get("success", False),
            content=response.get("content", []),
            count=response.get("count", 0),
            message=response.get("message", ""),
            error=response.get("error")
        )

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()


async def get_sandbox_content_artifacts(content_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for sandbox content artifact retrieval.
    
    Args:
        content_params: Dictionary containing content retrieval parameters
            - content_id (str): The content ID to retrieve (required)
            
    Returns:
        Dict containing content items, count, and status information
        
    Example:
        {
            "success": true,
            "content": [
                {
                    "identifier": "do_12345",
                    "name": "Sample Content",
                    "previewUrl": "https://.../content.epub",
                    "artifactUrl": "https://.../content.epub",
                    "mimeType": "application/epub",
                    "primaryCategory": "eTextbook",
                    "subject": ["English"],
                    "gradeLevel": ["Class 1"],
                    "medium": ["English"],
                    "board": "CBSE",
                    "lastPublishedOn": "2025-07-25T06:24:28.762+0000"
                }
            ],
            "count": 1,
            "message": "Successfully retrieved content items"
        }
    """
    async with SandboxContentProcessor() as processor:
        result = await processor.process(content_params)
        return result.dict()
