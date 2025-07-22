"""
Core package for Sunbird MCP server.

This package contains the core functionality and base classes
for the Model Context Protocol (MCP) server implementation.
"""

from .base import (
    BaseProcessor,
    BaseConfig,
    BaseRequest,
    BaseResponse
)

__all__ = [
    # Base classes
    'BaseProcessor',
    'BaseConfig',
    'BaseRequest',
    'BaseResponse',
]
