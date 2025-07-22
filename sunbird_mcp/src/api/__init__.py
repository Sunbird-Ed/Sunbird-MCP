"""
API package for Sunbird MCP server.

This package contains the implementation of various API endpoints
organized by functionality (search, content, etc.).

Modules:
    search: Search functionality for educational content
    content: Content retrieval and management
"""

from .search import search_sunbird_content
from .content import get_content_artifacts

__all__ = [
    'search_sunbird_content',
    'get_content_artifacts',
]
