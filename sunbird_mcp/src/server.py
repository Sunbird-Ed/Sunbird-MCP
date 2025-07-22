"""
SUNBIRD Content Search and Retrieval API Server

This module provides an API server for:
- searching and retrieving educational content from SUNBIRD
- It uses FastMCP for handling API requests asynchronously.

Key Features:
- Search for educational content with various filters
- Retrieve detailed metadata for specific content items
- Supports pagination, sorting, and field selection
- Validates input parameters for API requests
"""

import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from mcp.server.fastmcp import FastMCP
from config import settings
from models.search_models import SearchRequest
from models.content_models import ContentRequest
from api.search import search_sunbird_content
from api.content.api import get_content_artifacts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server with a unique identifier for this service
server = FastMCP("sunbird_mcp")

# Define constants for API endpoints
SEARCH_ENDPOINT = settings.API_ENDPOINT_SEARCH
CONTENT_ENDPOINT = settings.API_ENDPOINT_READ


@server.tool()
async def search_content(search_params: SearchRequest) -> dict:
    """
    Search for educational content on SUNBIRD platform using various filters. Divide the query 
    Preferred usage:
    - Use the 'filters' field (e.g., subject, grade, board, medium, etc.) for most searches.
    - Use the 'query' field for searching by exact book name only.

    Args:
        search_params (SearchRequest): Pydantic model containing search parameters including:
            - filters (dict): Content filters (e.g., subject, grade level, board)
            - limit (int): Maximum number of results to return (5-100)
            - offset (int): Pagination offset
            - sort_by (dict): Sorting criteria (e.g., {"lastPublishedOn": "desc"})
            - fields (list): Specific fields to include in the response
            - facets (list): Facets to include in the response
            - query (str): Text search query
    Example input:
        {search_params: {
            "filters": {
                "primaryCategory": filters.get("primaryCategory", ["Digital Textbook"]),
                "se_boards": ["CBSE"],
                "se_gradeLevels": ["Class 12"],
                "se_mediums": ["English"],
                "se_subjects": ["Physical Science"],
                "audience": ["Student"]
            },
            "limit": 5,
            "query": "",
            "sort_by": {"lastPublishedOn": "desc"},
            "fields": ["name", "identifier", "subject"],
            "facets": [],
            "offset": 0
        }}
    Example Response:
        {
            "book_1": {
                "name": "Physics Textbook",
                "identifier": "do_12345",
                "se_subjects": ["Physics"],
                "se_mediums": ["English"],
                "se_boards": ["CBSE"],
                "se_gradeLevels": ["Class 12"]
            }
        }

    Returns:
        dict: JSON-serializable dict containing search results or error information
    """
    return await search_sunbird_content(search_params.model_dump())

# New tool for reading content metadata
@server.tool()
async def read_sunbird_content(content_params: ContentRequest) -> dict:
    """
    Retrieve downloadable content artifacts for a specific book from SUNBIRD.
    This function fetches the leaf nodes of a content item (typically a textbook)
    and returns direct URLs to the PDF content, excluding ECML format content.
    Args:
        content_params (ContentRequest): Pydantic model containing content_id and optional fields.
    Example Input:
        { "content_params": { "content_id": "do_31400742839137075217260" } }
    Returns:
        dict: JSON-serializable dict containing:
            - artifact_urls (list): List of direct PDF URLs
            - count (int): Number of URLs returned
            - message (str): Status message
    Example Response:
        {
            "artifact_urls": ["https://diksha.gov.in/artifacts/.../content.pdf"],
            "count": 1,
            "message": "Successfully retrieved artifact URLs for non-ECML content"
        }
    """
    return await get_content_artifacts(content_params.model_dump())

# # Run the server
# if __name__ == "__main__":
#     server.run()
