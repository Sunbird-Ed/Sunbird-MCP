"""
Custom exceptions for the Sunbird MCP server.

This module defines the exception hierarchy used throughout the application
for consistent error handling and reporting.
"""
from typing import Any, Dict, Optional


class SunbirdAPIError(Exception):
    """Base exception for all Sunbird API errors.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for the error
        details: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SunbirdAPIError):
    """Raised when request validation fails.
    
    This typically indicates that the client sent malformed or invalid data.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Validation error: {message}",
            status_code=400,
            details=details
        )


class AuthenticationError(SunbirdAPIError):
    """Raised when authentication or authorization fails.
    
    This indicates that the request could not be authenticated or the
    authenticated user doesn't have permission to perform the requested action.
    """
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            details=details or {"code": "authentication_failed"}
        )


class ResourceNotFoundError(SunbirdAPIError):
    """Raised when a requested resource cannot be found.
    
    This indicates that the requested resource doesn't exist or the authenticated
    user doesn't have permission to access it.
    """
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            status_code=404,
            details={
                "code": "not_found",
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class RateLimitExceededError(SunbirdAPIError):
    """Raised when the rate limit has been exceeded.
    
    This indicates that the client has made too many requests in a given
    amount of time and should try again later.
    """
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            details={
                "code": "rate_limit_exceeded",
                "retry_after": retry_after
            }
        )


class DependencyError(SunbirdAPIError):
    """Raised when a required external service is unavailable.
    
    This indicates that the server cannot fulfill the request because a
    required external service is not responding or returned an error.
    """
    
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Service unavailable: {service_name}",
            status_code=503,
            details=details or {"code": "service_unavailable", "service": service_name}
        )


class ConfigurationError(Exception):
    """Raised when there's a problem with the server configuration.
    
    This is a critical error that should be fixed by the system administrator.
    """
    pass
