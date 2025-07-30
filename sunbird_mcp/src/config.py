"""Configuration settings for the Sunbird MCP Server."""
from typing import Dict, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

import os
import json as _json

import logging
logger = logging.getLogger(__name__)


def load_default_filters():
    env_json = os.environ.get("SUNBIRD_CONTENT_FILTERS_JSON")
    if env_json:
        try:
            return _json.loads(env_json)
        except (ValueError, _json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse SUNBIRD_CONTENT_FILTERS_JSON: {e}")
            # fallback to default
    return {
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
        "se_gradeLevels": [f"Class {i}" for i in range(1, 13)],
        "se_mediums": ["English", "Hindi"],
        "se_subjects": [
            "Kannada", "English", "Hindi", "Mathematics", "Physical Science", "Biology",
            "History", "Geography", "Civics", "Economics", "Environmental Studies",
            "Health & Physical Education", "Computer Applications",
            "Art & Cultural Education - Music", "Drawing"
        ],
        "audience": ["Student", "Teacher"]
    }

def load_sandbox_filters():
    env_json = os.environ.get("SUNBIRD_SANDBOX_FILTERS_JSON")
    if env_json:
        try:
            return _json.loads(env_json)
        except (ValueError, _json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse SUNBIRD_SANDBOX_FILTERS_JSON: {e}")
    # Default sandbox filters
    return {
        "subject": ["english", "hindi"],
        "audience": ["Other", "Parent", "School head OR Officials", "Student", "Teacher"],
        "status": ["Live"],
        "contentType": ["Course"],
        "primaryCategory": ["Course", "Course Assessment"],
        "se_boards": ["CBSE"],
        "se_gradeLevels": [f"Class {i}" for i in range(1, 5)],
        "se_mediums": ["English", "Hindi", "Tamil", "Telugu"],
        "creator": ["content creator"],
        "organisation": ["sunbird org"]
    }


class Settings(BaseSettings):
    """Application settings and configuration."""
    # API Configuration
    API_BASE_URL: str = Field(
        default="https://diksha.gov.in",  # This is the base url for the sunbird api
        env="SUNBIRD_API_BASE_URL",
        description="Base URL for the Sunbird API (without trailing slash)",
        min_length=1
    )
    # API Endpoints
    API_ENDPOINT_SEARCH: str = Field(
        default="/api/content/v1/search",
        env="SUNBIRD_API_ENDPOINT_SEARCH",
        description="Endpoint for searching content"
    )
    API_ENDPOINT_READ: str = Field(
        default="/api/content/v1/read",
        env="SUNBIRD_API_ENDPOINT_READ",
        description="Endpoint for reading content details"
    )

    @field_validator('API_BASE_URL')
    @classmethod
    def validate_api_base_url(cls, v):
        """Ensure the API base URL doesn't end with a slash."""
        if isinstance(v, str):
            return v.rstrip('/')
        return v
    # Search Configuration
    DEFAULT_LIMIT: int = Field(
        default=10,
        ge=1,
        le=100,
        env="SUNBIRD_DEFAULT_LIMIT",
        description="Default number of search results to return"
    )
    MAX_LIMIT: int = Field(
        default=100,
        ge=1,
        le=1000,
        env="SUNBIRD_MAX_LIMIT",
        description="Maximum number of search results allowed per request"
    )
    # Timeout settings
    REQUEST_TIMEOUT: int = Field(
        default=30,
        gt=0,
        env="SUNBIRD_REQUEST_TIMEOUT",
        description="Timeout in seconds for API requests"
    )
    # Content Types and Filters
    # Content filters can be extended via environment variables or external config
    CONTENT_FILTERS: Dict[str, List[str]] = Field(
        default_factory=load_default_filters,
        env="SUNBIRD_CONTENT_FILTERS_JSON",
        description="Valid content filters and their allowed values"
    )

    # Fields Configuration
    DEFAULT_FIELDS: List[str] = Field(
        default_factory=lambda: [
            "name", "appIcon", "mimeType", "gradeLevel", "identifier", "medium", "pkgVersion",
            "board", "subject", "resourceType", "primaryCategory", "contentType", "channel",
            "organisation", "trackable", "se_boards", "se_subjects", "se_mediums", "se_gradeLevels",
            "me_averageRating", "me_totalRatingsCount", "me_totalPlaySessionCount"
        ],
        description="Default fields to include in search results"
    )

    # Facets Configuration
    VALID_FACETS: List[str] = Field(
        default_factory=lambda: [
            "se_boards", "se_gradeLevels", "se_subjects", "se_mediums", "primaryCategory"
        ],
        description="Default facets available for search and filtering"
    )

    # MIME Types and Content ID Prefix
    PDF_MIME_TYPE: str = Field(
        default="application/pdf",
        description="MIME type for PDF content"
    )
    EXCLUDED_MIME_TYPE: str = Field(
        default="application/vnd.ekstep.ecml-archive",
        description="MIME type to exclude (e.g., ECML format)"
    )
    CONTENT_ID_PREFIX: str = Field(
        default="do_",
        description="Prefix for valid SUNBIRD content IDs"
    )
    # Validation Settings
    ENABLE_INPUT_VALIDATION: bool = Field(
        default=True,
        env="SUNBIRD_ENABLE_VALIDATION",
        description="Enable/disable input validation"
    )

    # Sandbox Configuration
    SANDBOX_API_BASE_URL: str = Field(
        default="https://sandbox.sunbirded.org",
        env="SUNBIRD_SANDBOX_API_BASE_URL",
        description="Base URL for the Sunbird Sandbox API"
    )
    
    # Sandbox specific filters
    SANDBOX_FILTERS: Dict[str, List[str]] = Field(
        default_factory=load_sandbox_filters,
        env="SUNBIRD_SANDBOX_FILTERS_JSON",
        description="Valid content filters for sandbox environment"
    )
    
    # Sandbox default fields
    SANDBOX_DEFAULT_FIELDS: List[str] = Field(
        default_factory=lambda: [
            "name", "appIcon", "mimeType", "gradeLevel", "identifier", "medium", "pkgVersion",
            "board", "subject", "resourceType", "contentType", "channel", "organisation",
            "trackable", "se_boards", "se_subjects", "se_mediums", "se_gradeLevels", "creator"
        ],
        description="Default fields to include in sandbox search results"
    )
    
    # Sandbox default facets
    SANDBOX_VALID_FACETS: List[str] = Field(
        default_factory=lambda: ["se_subjects", "creator", "organisation"],
        description="Default facets for sandbox search"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False


# Create settings instance
settings = Settings()
