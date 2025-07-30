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

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from config import settings
from models.search_models import SearchRequest
from models.content_models import ContentRequest
from models.sandbox_content_models import SandboxContentRequest
from api.search import search_sunbird_content
from api.sandbox_search import search_sandbox_content
from api.content.api import get_content_artifacts
from api.sandbox_content import get_sandbox_content_artifacts

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


@server.tool()
async def sandbox_search_content(search_params: SearchRequest) -> dict:
    """
    Search for educational content in the Sunbird Sandbox environment.
    
    This endpoint provides access to test content in the Sunbird Sandbox environment.
    It's specifically designed for development and testing purposes.

    Args:
        search_params (SearchRequest): Pydantic model containing search parameters including:
            - filters (dict): Content filters (e.g., subject, grade level, board)
            - limit (int): Maximum number of results to return (1-100, default: 10)
            - offset (int): Pagination offset (default: 0)
            - sort_by (dict): Sorting criteria (e.g., {"lastPublishedOn": "desc"})
            - fields (list): Specific fields to include in the response
            - facets (list): Facets to include in the response
            - query (str): Text search query (optional)

    Example input:
        {
            "search_params": {
                "filters": {
                    "contentType": ["Course"],
                    "se_boards": ["CBSE"],
                    "se_gradeLevels": ["Class 1", "Class 2"],
                    "se_mediums": ["English", "Hindi"],
                    "subject": ["english", "hindi"],
                    "status": ["Live"]
                },
                "limit": 5,
                "offset": 0,
                "query": "",
                "fields": ["name", "identifier", "contentType", "se_subjects"],
                "facets": ["se_subjects", "creator"],
                "sort_by": {"lastPublishedOn": "desc"}
            }
        }

    Example Response:
        {
            "success": true,
            "data": {
                "content": [
                    {
                        "identifier": "do_21436405321781248017",
                        "name": "Mathematics Course 1",
                        "contentType": "Course",
                        "resourceType": "Course",
                        "mimeType": "application/vnd.ekstep.content-collection",
                        "se_subjects": ["Mathematics", "English"],
                        "se_mediums": ["English"],
                        "se_boards": ["CBSE"],
                        "se_gradeLevels": ["Class 1", "Class 2"],
                        "creator": "Content Creator",
                        "organisation": ["Sunbird Org"]
                    }
                ],
                "count": 1,
                "facets": [
                    {
                        "name": "se_subjects",
                        "values": [
                            {"name": "mathematics", "count": 1},
                            {"name": "english", "count": 1}
                        ]
                    },
                    {
                        "name": "creator",
                        "values": [
                            {"name": "Content Creator", "count": 1}
                        ]
                    }
                ]
            },
            "metadata": {
                "api": "sandbox_search",
                "version": "1.0",
                "total": 1,
                "responseCode": "OK",
                "ts": "2025-07-26T15:45:30.123Z"
            }
        }

    Error Response:
        {
            "success": false,
            "error": {
                "message": "Invalid search parameters",
                "details": ["Invalid filter value 'invalid_subject' for filter 'subject'"]
            }
        }
    """
    return await search_sandbox_content(search_params.model_dump())

@server.tool()
async def read_sandbox_content(content_params: SandboxContentRequest) -> Dict[str, Any]:
    """
    Retrieve content details and artifacts from the Sunbird Sandbox environment.
    
    This endpoint fetches content metadata and recursively processes collections to return
    all leaf node content items with their details.
    
    Args:
        content_params (SandboxContentRequest): Pydantic model containing:
            - content_id (str): The content ID to retrieve (must start with 'do_')
    
    Example Input:
        {
            "content_params": {
                "content_id": "do_21436405211893760014"
            }
        }
    
    Returns:
        dict: JSON-serializable dict containing:
            - success (bool): Indicates if the request was successful
            - content (list): List of content items with their details
            - count (int): Number of content items returned
            - message (str): Status message
            - error (str, optional): Error message if the request failed
    
    Example Response:
        {
            "success": true,
            "content": [
                {
                    "identifier": "do_21436405211893760014",
                    "name": "Sample Content",
                    "previewUrl": "https://.../sample.epub",
                    "artifactUrl": "https://.../sample.epub",
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
    
    Error Response:
        {
            "success": false,
            "content": [],
            "count": 0,
            "message": "Failed to retrieve content",
            "error": "Content not found or access denied"
        }
    """
    try:
        # Convert Pydantic model to dict and process the request
        result = await get_sandbox_content_artifacts(content_params.dict())
        return result
    except Exception as e:
        logger.error(f"Error in read_sandbox_content: {str(e)}", exc_info=True)
        return {
            "success": False,
            "content": [],
            "count": 0,
            "message": "Failed to retrieve content",
            "error": str(e)
        }

# # Run the server
# if __name__ == "__main__":
#     server.run()
