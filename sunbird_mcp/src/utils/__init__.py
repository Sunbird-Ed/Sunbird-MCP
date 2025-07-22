"""
Utility functions and classes for the Sunbird MCP server.

This package contains shared utilities including:
- Custom exceptions
- Helper functions
- Common utilities
"""

from .exceptions import (
    SunbirdAPIError,
    ValidationError,
    AuthenticationError,
    ResourceNotFoundError,
    RateLimitExceededError,
)

__all__ = [
    'SunbirdAPIError',
    'ValidationError',
    'AuthenticationError',
    'ResourceNotFoundError',
    'RateLimitExceededError',
]
