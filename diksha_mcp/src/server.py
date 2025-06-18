"""
DIKSHA Content Search and Retrieval API Server

This module provides an API server for searching and retrieving educational content from DIKSHA,
India's national platform for school education. It uses FastMCP for handling API requests asynchronously.

Key Features:
- Search for educational content with various filters
- Retrieve detailed metadata for specific content items
- Supports pagination, sorting, and field selection
- Validates input parameters for API requests
"""

import json
import aiohttp
import re
import asyncio
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server with a unique identifier for this service
server = FastMCP("diksha_search_tool")

# Define allowed values for search filters to ensure data quality and API compliance
# These filters are used to validate user input before making requests to DIKSHA API
VALID_FILTERS = {
    "primaryCategory": [
        "Collection", "Resource", "Content Playlist", "Course", "Course Assessment",
        "Digital Textbook", "eTextbook", "Explanation Content", "Learning Resource",
        "Practice Question Set", "Teacher Resource", "Textbook Unit", "LessonPlan",
        "FocusSpot", "Learning Outcome Definition", "Curiosity Questions",
        "MarkingSchemeRubric", "ExplanationResource", "ExperientialResource",
        "Practice Resource", "TVLesson", "Question paper"
    ],
    "visibility": ["Default", "Parent"],
    "se_boards": ["CBSE", "State (Andhra Pradesh)"],
    "se_gradeLevels": [
        "Class 1", "Class 2", "Class 3", "Class 4", "Class 5",
        "Class 6", "Class 7", "Class 8", "Class 9", "Class 10",
        "Class 11", "Class 12"
    ],
    "se_mediums": ["English", "Hindi"],
    "subject": ["Physical Science", "Mathematics"],
    "audience": ["Student", "Teacher"]
}

# TOTAL VALID_FIELDS = [
#     "name", "appIcon", "mimeType", "gradeLevel", "identifier", "medium", "pkgVersion",
#     "board", "subject", "resourceType", "primaryCategory", "contentType", "channel",
#     "organisation", "trackable", "se_boards", "se_subjects", "se_mediums", "se_gradeLevels",
#     "me_averageRating", "me_totalRatingsCount", "me_totalPlaySessionCount"
# ]
VALID_FIELDS = [
    "name", "identifier", "primaryCategory", "contentType",
    "organisation","se_boards", "se_subjects", "se_mediums", "se_gradeLevels"
]
VALID_FACETS = ["se_boards", "se_gradeLevels", "se_subjects", "se_mediums", "primaryCategory"]

def validate_filters(filters):
    """
    Validate the provided filters against allowed values.
    
    Args:
        filters (dict): Dictionary of filter parameters to validate
        
    Returns:
        list: List of error messages for invalid filters, empty list if all are valid
    """
    errors = []
    for key, values in filters.items():
        if key in VALID_FILTERS and values:
            if not all(val in VALID_FILTERS[key] for val in values):
                errors.append(
                    f"Invalid {key} value(s). Valid options: {', '.join(VALID_FILTERS[key])}"
                )
    return errors

def validate_fields_and_facets(fields, facets):
    """
    Validate the requested fields and facets against allowed values.
    
    Args:
        fields (list): List of field names to include in the response
        facets (list): List of facet names to include in the response
        
    Returns:
        list: List of error messages for invalid fields/facets, empty list if all are valid
    """
    errors = []
    if fields and not all(field in VALID_FIELDS for field in fields):
        errors.append(f"Invalid fields value(s). Valid options: {', '.join(VALID_FIELDS)}")
    if facets and not all(facet in VALID_FACETS for facet in facets):
        errors.append(f"Invalid facets value(s). Valid options: {', '.join(VALID_FACETS)}")
    return errors

# Existing search_diksha_content tool (unchanged, using dict input as per previous correction)
@server.tool()
async def search_diksha_content(search_params: dict) -> str:
    """
    Search for educational content on DIKSHA platform using various filters.
    
    This function serves as the main search interface to the DIKSHA content repository.
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
    

    Args:
        search_params: Dictionary containing search parameters, e.g., filters, limit, query, sort_by, fields, facets.

    Example input:
        {
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
        }
    """
    try:
        # Extract parameters with defaults
        filters = search_params.get("filters", {})
        limit = search_params.get("limit",10 )
        query = search_params.get("query", "")
        sort_by = search_params.get("sort_by", {"lastPublishedOn": "desc"})
        fields = search_params.get("fields", [])
        facets = search_params.get("facets", [])
        offset = search_params.get("offset", 0)

        # Validate limit
        if not isinstance(limit, int) or limit < 0 or limit > 100:
            return json.dumps({"error": "Limit must be an integer between 0 and 100"})

        # Validate offset
        if not isinstance(offset, int) or offset < 0 or offset > 10000:
            return json.dumps({"error": "Offset must be an integer between 0 and 10000"})

        # Validate filters
        filter_errors = validate_filters(filters)
        if filter_errors:
            return json.dumps({"errors": filter_errors})

        # Validate fields and facets
        field_facet_errors = validate_fields_and_facets(fields, facets)
        if field_facet_errors:
            return json.dumps({"errors": field_facet_errors})

        # Construct DIKSHA API request body
        request_body = {
            "request": {
                "filters": {
                    "primaryCategory": ["Digital Textbook"],##Deliberately hardcoded to Digital Textbook
                    "visibility": filters.get("visibility", []),
                    "se_boards": filters.get("se_boards", []),
                    "se_gradeLevels": filters.get("se_gradeLevels", []),
                    "se_mediums": filters.get("se_mediums", []),
                    "subject": filters.get("subject", []),
                    "audience": filters.get("audience", []),
                    "channel": filters.get("channel", []),
                    "verticals": filters.get("verticals", [])
                },
                "limit": limit,
                "query": query,
                "sort_by": sort_by,
                "fields": fields if fields else VALID_FIELDS,
                #"facets": facets, not used in the request
                "offset": offset
            }
        }

        # Make async request to DIKSHA API
        async with aiohttp.ClientSession() as session:
+            timeout = aiohttp.ClientTimeout(total=15)
            async with session.post(
                "https://diksha.gov.in/api/content/v1/search",
                json=request_body,
+               timeout=timeout,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    x={}
                    i=0
                    for content in data.get("result", {}).get("content", []):
                        # Ensure 'leafNodes' is present in each content item
                        y={}
                        y["name"] = content.get("name", "")
                        y["identifier"]= content.get("identifier", [])
                        y["se_subjects"] = content.get("se_subjects", [])
                        y["se_mediums"] = content.get("se_mediums", [])
                        y["se_boards"] = content.get("se_boards", [])
                        y["se_gradeLevels"] = content.get("se_gradeLevels", [])
                        book_number=f"book_{i+1}"
                        i+=1
                        x[book_number]=y
                    return json.dumps(x, ensure_ascii=False)
                else:
                    error_data = await response.text()
                    return json.dumps({
                        "error": f"DIKSHA API request failed with status {response.status}",
                        "details": error_data
                    })

    except Exception as e:
        return json.dumps({"error": "Failed to process request", "details": str(e)})

# New tool for reading content metadata
@server.tool()
async def read_diksha_content(params: dict) -> str:
    """
    Retrieve downloadable content artifacts for a specific book from DIKSHA.
    
    This function fetches the leaf nodes of a content item (typically a textbook)
    and returns direct URLs to the PDF content, excluding ECML format content.
    
    Args:
        params (dict): Dictionary containing:
            - content_id (str): The DIKSHA content ID (starts with 'do_')
            
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
    

    Args:
        params:dictionary containing a content ID.
            Example: {"content_id":"do_31400742839137075217260"}

    Returns:
        JSON string containing a list of artifact URLs for content items where mimeType is not 'application/vnd.ekstep.ecml-archive',
        or an error message.
    """
    async def retrieve_content_ids(params: str) -> tuple[list[str] | None, str | None]:
        """
        Helper function to retrieve leaf node content IDs for a given content ID.
        
        Args:
            params (str): The content ID to fetch leaf nodes for
            
        Returns:
            tuple[list[str] | None, str | None]: A tuple containing:
                - List of content IDs for the leaf nodes, or None if there was an error
                - Error message string if there was an error, or None on success
            
        Note:
            This is an internal helper function and should not be called directly.
        """
        try:
            # Extract content_id from params
            content_id = params
            # Validate content_id
            if not content_id:
                return None, "content_id is required"
            if not re.match(r"^do_[0-9]+$", content_id):
                return None, "Invalid content_id format. Must start with 'do_' followed by numbers"

            # Construct DIKSHA API URL
            api_url = f"https://diksha.gov.in/api/content/v1/read/{content_id}?contentType=TextBook"

            # Make async request to DIKSHA API
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        content_ids = data["result"]["content"]["leafNodes"]
                        return content_ids, None
                    else:
                        error_data = await response.text()
                        return None, f"DIKSHA API request failed with status {response.status}: {error_data}"

        except Exception as e:
            return None, f"Failed to process request: {str(e)}"
    try:
        # Extract content_ids from params
        content_ids, error = await retrieve_content_ids(params["content_id"])
        if error:
            return json.dumps({"error": error})

        # Since we know content_ids is either a list or None at this point,
        # and error was None (we checked above), we can safely assert it's a list
        assert content_ids is not None, "content_ids should not be None when error is None"
        
        if not content_ids:
            return json.dumps({"error": "content_ids list cannot be empty"})
        if not isinstance(content_ids, list):
            return json.dumps({"error": "content_ids must be a list"})
        for content_id in content_ids:
            if not isinstance(content_id, str) or not content_id.strip():
                return json.dumps({"error": f"Invalid content_id: {content_id}. All IDs must be non-empty strings"})
            if not re.match(r"^do_[0-9]+$", content_id):
                return json.dumps({"error": f"Invalid content_id format: {content_id}. Must start with 'do_' followed by numbers"})

        # Define excluded MIME type
        excluded_mime = "application/vnd.ekstep.ecml-archive"
        artifact_urls = []

        # Internal helper function to process individual content items asynchronously
        async def fetch_and_filter(session, content_id):
            """
            Fetch content metadata and filter for PDF artifacts.
            
            Args:
                session: aiohttp client session
                content_id: DIKSHA content ID to process
                
            Note:
                This function modifies the artifact_urls list in the parent scope.
            """
            try:
                api_url = f"https://diksha.gov.in/api/content/v1/read/{content_id}"
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("result", {}).get("content", {})
                        if content.get("mimeType") != excluded_mime and content.get("mimeType") == "application/pdf" and content.get("streamingUrl"):
                            artifact_urls.append(content.get("streamingUrl"))
                    else:
                        print(f"⚠️ Error with {content_id}: API returned status {response.status}")
            except Exception as e:
                print(f"⚠️ Error with {content_id}: {str(e)}")

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
# async def read_diksha_content(params: dict) -> str:
#     """Retrieve metadata for a DIKSHA content item by its content ID.

#     Args:
#         params: Dictionary containing the content ID.
#             Example: {"content_id": "do_31268582767737241615189"}

#     Returns:
#         JSON string containing the content metadata or an error message.
#     """
    # try:
    #     # Extract content_id from params
    #     content_id = params.get("content_id", "").strip()

    #     # Validate content_id
    #     if not content_id:
    #         return json.dumps({"error": "content_id is required"})
    #     if not re.match(r"^do_[0-9]+$", content_id):
    #         return json.dumps({"error": "Invalid content_id format. Must start with 'do_' followed by numbers"})

    #     # Construct DIKSHA API URL
    #     api_url = f"https://diksha.gov.in/api/content/v1/read/{content_id}"

    #     # Make async request to DIKSHA API
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(
    #             api_url,
    #             headers={"Content-Type": "application/json"}
    #         ) as response:
    #             if response.status == 200:
    #                 data = await response.json()
    #                 return json.dumps(data, ensure_ascii=False)
    #             else:
    #                 error_data = await response.text()
    #                 return json.dumps({
    #                     "error": f"DIKSHA API request failed with status {response.status}",
    #                     "details": error_data
    #                 })

    # except Exception as e:
    #     return json.dumps({"error": "Failed to process request", "details": str(e)})

# # Run the server
# if __name__ == "__main__":
#     server.run()