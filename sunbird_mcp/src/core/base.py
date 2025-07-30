"""
Base classes for the Sunbird MCP server.

This module contains abstract base classes that define the core interfaces
for API processors and data models used throughout the application.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field
from utils.exceptions import SunbirdAPIError, AuthenticationError, ResourceNotFoundError, RateLimitExceededError, ValidationError

T = TypeVar('T', bound='BaseRequest')


class BaseConfig(BaseModel):
    """Base configuration model for API processors.
    
    Attributes:
        api_name: Unique identifier for the API endpoint
        description: Human-readable description of the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        enabled: Whether the API is currently enabled
    """
    api_name: str = Field(..., description="Unique identifier for the API endpoint")
    description: str = Field(..., description="Human-readable description of the API")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum number of retry attempts")
    enabled: bool = Field(True, description="Whether the API is currently enabled")


class BaseRequest(BaseModel):
    """Base request model that all API requests should inherit from.
    
    This class provides common fields and validation logic that applies to all
    API requests in the system.
    """
    class Config:
        extra = 'forbid'  # Prevent extra fields in requests
        json_encoders = {
            # Add custom JSON encoders here if needed
        }


class BaseResponse(BaseModel):
    """Base response model that all API responses should inherit from.
    
    Attributes:
        success: Whether the request was successful
        data: The response data (if successful)
        error: Error details (if unsuccessful)
        metadata: Additional metadata about the response
    """
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Response data (if successful)"
    )
    error: Optional[Dict[str, Any]] = Field(
        None,
        description="Error details (if unsuccessful)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response"
    )


class BaseProcessor(ABC, Generic[T]):
    """Abstract base class for all API processors.
    
    This class defines the standard interface for processing API requests,
    following a three-step pattern:
    1. pre_process: Validate and transform input parameters
    2. execute: Perform the main processing logic
    3. post_process: Transform and format the response
    
    Subclasses should implement these methods to provide specific functionality.
    """
    
    def __init__(self, config: BaseConfig):
        """Initialize the processor with its configuration.
        
        Args:
            config: Configuration for this processor
        """
        self.config = config
    
    def initialize(self) -> None:
        """Optional initialization hook.
        
        This method is called after __init__ and can be overridden by subclasses
        to perform any necessary setup.
        """
        pass
    
    @abstractmethod
    async def pre_process(self, request_data: Dict[str, Any]) -> T:
        """Validate and transform input parameters.
        
        Args:
            request_data: Raw request data from the client
            
        Returns:
            Validated and processed request object
            
        Raises:
            ValidationError: If the request data is invalid
        """
        pass
    
    @abstractmethod
    async def execute(self, request: T) -> Any:
        """Execute the main processing logic.
        
        Args:
            request: Validated request object
            
        Returns:
            Raw response data (before post-processing)
            
        Raises:
            SunbirdAPIError: If there's an error processing the request
        """
        pass
    
    @abstractmethod
    async def post_process(self, response: Any) -> Dict[str, Any]:
        """Transform and format the response.
        
        Args:
            response: Raw response from execute()
            
        Returns:
            Formatted response data
        """
        pass
    
    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request through the entire pipeline.
        
        This method implements the standard processing flow:
        1. Pre-process the request
        2. Execute the main logic
        3. Post-process the response
        
        Args:
            request_data: Raw request data from the client
            
        Returns:
            Formatted response data
        """
        try:
            # Step 1: Pre-processing
            validated_request = await self.pre_process(request_data)
            
            # Step 2: Execution
            raw_response = await self.execute(validated_request)
            
            # Step 3: Post-processing
            return await self.post_process(raw_response)
            
        except Exception as e:
            # Convert known exceptions to appropriate error responses
            if isinstance(e, (ValidationError, AuthenticationError, 
                           ResourceNotFoundError, RateLimitExceededError)):
                raise
                
            # Wrap unexpected errors in a generic API error
            raise SunbirdAPIError(
                message="An unexpected error occurred",
                status_code=500,
                details={"error": str(e)}
            ) from e
