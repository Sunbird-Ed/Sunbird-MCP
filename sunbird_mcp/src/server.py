"""
SUNBIRD Content Search and Retrieval API Server

This module provides an API server for searching and retrieving educational content from SUNBIRD,
India's national platform for school education. It uses FastMCP for handling API requests asynchronously.

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
from typing import Dict, Any, List, Optional, Union, Tuple
from mcp.server.fastmcp import FastMCP
from config import settings

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

# Get valid filters and fields from settings
VALID_FILTERS = settings.CONTENT_FILTERS
VALID_FIELDS = settings.DEFAULT_FIELDS
VALID_FACETS = settings.VALID_FACETS

def validate_filters(filters: Dict[str, Any]) -> List[str]:
    """
    Validate the provided filters against allowed values.
    
    Args:
        filters: Dictionary of filter parameters to validate
        
    Returns:
        List of error messages for invalid filters, empty list if all are valid
    """
    if not settings.ENABLE_INPUT_VALIDATION:
        return []
        
    errors = []
    if not isinstance(filters, dict):
        return ["Filters must be a dictionary"]
        
    for key, values in filters.items():
        if key not in VALID_FILTERS:
            errors.append(f"Invalid filter key: {key}")
        else:
            if not isinstance(values, list):
                values = [values]
            for value in values:
                if value not in VALID_FILTERS[key]:
                    errors.append(f"Invalid value '{value}' for filter '{key}'. Must be one of: {', '.join(VALID_FILTERS[key])}")
    
    return errors

def validate_fields_and_facets(fields: Optional[List[str]], facets: Optional[List[str]]) -> List[str]:
    """
    Validate the requested fields and facets against allowed values.
    
    Args:
        fields: List of field names to include in the response
        facets: List of facet names to include in the response
        
    Returns:
        List of error messages for invalid fields/facets, empty list if all are valid
    """
    if not settings.ENABLE_INPUT_VALIDATION:
        return []
        
    errors = []
    
    if fields:
        for field in fields:
            if field not in VALID_FIELDS:
                errors.append(f"Invalid field: {field}")
    
    if facets:
        for facet in facets:
            if facet not in VALID_FACETS:
                errors.append(f"Invalid facet: {facet}")
    
    return errors

# Existing search_sunbird_content tool (unchanged, using dict input as per previous correction)
@server.tool()
async def search_sunbird_content(search_params: Dict[str, Any]) -> str:
    """
    Search for educational content on SUNBIRD platform using various filters.
    
    This function serves as the main search interface to the SUNBIRD content repository.
    It validates input parameters, constructs the API request, and processes the response.
    
    Args:
        search_params (dict): Dictionary containing search parameters including:
            - filters (dict): Content filters (e.g., subject, grade level, board)
            - limit (int): Maximum number of results to return (1-100)
            - query (str): Text search query
            - sort_by (dict): Sorting criteria (e.g., {"lastPublishedOn": "desc"})
            - fields (list): Specific fields to include in the response
            - facets (list): Facets to include in the response
            - offset (int): Pagination offset
            
    Returns:
        str: JSON string containing search results or error information
        
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
    Example input:
        {search_params: {
            "filters": {
                "primaryCategory": filters.get("primaryCategory", ["Digital Textbook"]),
                "se_boards": ["CBSE"],
                "se_gradeLevels": ["Class 12"],
                "se_mediums": ["English"],
                "subject": ["Physical Science"],
                "audience": ["Student"]
            },
            "limit": 1,
            "query": "physics",
            "sort_by": {"lastPublishedOn": "desc"},
            "fields": ["name", "identifier", "subject"],
            "facets": ["se_subjects"],
            "offset": 0
        }}
    """
    try:
        # Validate input parameters
        if not isinstance(search_params, dict):
            return json.dumps({"error": "Search parameters must be a dictionary"}, ensure_ascii=False)
        
        # Extract and validate filters
        filters = search_params.get("filters", {})
        filter_errors = validate_filters(filters)
        if filter_errors:
            return json.dumps({"error": "Invalid filters", "details": filter_errors}, ensure_ascii=False)
        
        # Validate fields and facets if provided
        fields = search_params.get("fields", VALID_FIELDS)
        facets = search_params.get("facets", [])
        
        validation_errors = validate_fields_and_facets(fields, facets)
        if validation_errors:
            return json.dumps({"error": "Validation error", "details": validation_errors}, ensure_ascii=False)
        
        # Set up request parameters with defaults and configured limits
        limit = min(
            int(search_params.get("limit", settings.DEFAULT_LIMIT)),
            settings.MAX_LIMIT
        )
        offset = int(search_params.get("offset", 0))
        query = search_params.get("query", "")
        sort_by = search_params.get("sort_by", {"lastPublishedOn": "desc"})
        
        # Build request payload
        payload = {
            "request": {
                "filters": filters,
                "limit": limit,
                "offset": offset,
                "query": query,
                "sort_by": sort_by,
                "fields": fields
            }
        }
        
        if facets:
            payload["request"]["facets"] = facets
        
        # Build API URL
        api_url = f"{settings.API_BASE_URL.rstrip('/')}{SEARCH_ENDPOINT}"
        
        # Make API request with timeout
        try:
            timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        book_list={}
                        index=0
                        for content in data.get("result", {}).get("content", []):
                            # Ensure 'leafNodes' is present in each content item
                            book_details={}
                            book_details["name"] = content.get("name", "")
                            book_details["identifier"]= content.get("identifier", "")
                            book_details["se_subjects"] = content.get("se_subjects", [])
                            book_details["se_mediums"] = content.get("se_mediums", [])
                            book_details["se_boards"] = content.get("se_boards", [])
                            book_details["se_gradeLevels"] = content.get("se_gradeLevels", [])
                            book_number=f"book_{index+1}"
                            index+=1
                            book_list[book_number]=book_details
                        return json.dumps(book_list, ensure_ascii=False)
                    else:
                        error_data = await response.text()
                        return json.dumps({
                            "error": f"Sunbird API request failed with status {response.status}",
                            "details": error_data
                        }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": "Failed to process request", "details": str(e)}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": "Failed to process request", "details": str(e)}, ensure_ascii=False)

# New tool for reading content metadata
@server.tool()
async def read_sunbird_content(params: Dict[str, Any]) -> str:
    """
    Retrieve downloadable content artifacts for a specific book from SUNBIRD.
    
    This function fetches the leaf nodes of a content item (typically a textbook)
    and returns direct URLs to the PDF content, excluding ECML format content.
    
    Args:
        params (dict): Dictionary containing:
            - content_id (str): The SUNBIRD content ID (starts with 'do_')
            
    Returns:
        str: JSON string containing:
            - artifact_urls (list): List of direct PDF URLs
            - count (int): Number of URLs returned
            - message (str): Status message
            
    Example Response:
        {
            "artifact_urls": ["https://diksha.gov.in/artifacts/.../content.pdf"],
            "count": 1,
            "message": "Successfully retrieved artifact URLs for non-ECML content"
        }
    Example Input: {"content_id":"do_31400742839137075217260"}
    """

    async def retrieve_content_ids(content_id: str) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Helper function to retrieve leaf node content IDs for a given content ID.
        
        Args:
            content_id: The content ID to fetch leaf nodes for
            
        Returns:
            A tuple containing:
                - List of content IDs for the leaf nodes, or None if there was an error
                - Error message string if there was an error, or None on success
            
        Note:
            This is an internal helper function and should not be called directly.
        """
        try:
            # Build API URL
            api_url = f"{settings.API_BASE_URL.rstrip('/')}{CONTENT_ENDPOINT}/{content_id}"
            
            # First, get the content details with timeout
            timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    api_url,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["result"]["content"]["leafNodes"], None
                    else:
                        error_data = await response.text()
                        return None, f"Sunbird API request failed with status {response.status}: {error_data}"
        except Exception as e:
            return None, f"Failed to process request: {str(e)}"
    try:
        # Validate input parameters
        if not isinstance(params, dict) or "content_id" not in params:
            return json.dumps({"error": "content_id is required"}, ensure_ascii=False)
            
        content_id = params["content_id"]
        if not isinstance(content_id, str) or not content_id.strip():
            return json.dumps({"error": "content_id must be a non-empty string"}, ensure_ascii=False)
            
        if not content_id.startswith(settings.CONTENT_ID_PREFIX):
            return json.dumps({"error": f"content_id must start with '{settings.CONTENT_ID_PREFIX}'"}, ensure_ascii=False)
            
        # Extract content_ids from the API
        content_ids, error = await retrieve_content_ids(content_id)
        if error:
            return json.dumps({"error": error}, ensure_ascii=False)

        # Validate the returned content_ids
        if not content_ids:
            return json.dumps({"error": "No content IDs found for the given content_id"}, ensure_ascii=False)
            
        if not isinstance(content_ids, list):
            return json.dumps({"error": "Unexpected response format: content_ids is not a list"}, ensure_ascii=False)

        # Define excluded MIME type from config
        excluded_mime = settings.EXCLUDED_MIME_TYPE
        artifact_urls = []

        # Internal helper function to process individual content items asynchronously
        async def fetch_and_filter(session, content_id):
            """
            Fetch content metadata and filter for PDF artifacts.
            
            Args:
                session: aiohttp client session
                content_id: SUNBIRD content ID to process
                
            Note:
                This function modifies the artifact_urls list in the parent scope.
            """
            try:
                api_url = f"{settings.API_BASE_URL.rstrip('/')}{CONTENT_ENDPOINT}/{content_id}"
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("result", {}).get("content", {})
                        if content.get("mimeType") != excluded_mime and content.get("mimeType") == settings.PDF_MIME_TYPE and content.get("streamingUrl"):
                            artifact_urls.append(content.get("streamingUrl"))
                    else:
                        logger.warning(f"Error with {content_id}: API returned status {response.status}")
            except Exception as e:
                logger.error(f"Error with {content_id}: {str(e)}", exc_info=True)

        # Create a semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(20)  # Limit to 20 concurrent requests

        async def fetch_with_limit(session: aiohttp.ClientSession, content_id: str) -> None:
            async with semaphore:  # Acquire and release semaphore automatically
                await fetch_and_filter(session, content_id)

        # Create async session and process all content IDs with concurrency limit
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_with_limit(session, content_id) for content_id in content_ids]
            await asyncio.gather(*tasks)

        # Return the list of artifact URLs
        return json.dumps({
            "artifact_urls": artifact_urls,
            "count": len(artifact_urls),
            "message": "Successfully retrieved artifact URLs for non-ECML content"
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": "Failed to process request", "details": str(e)})

# # Run the server
# if __name__ == "__main__":
#     server.run()
