"""
Validation utilities for the Content API.

This module contains validation functions specific to content operations.
"""
from typing import Dict, List, Tuple, Any
from utils.content_validation import validate_content_request_base

def validate_content_request(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate content request parameters for content retrieval API.
    
    Args:
        params: Raw request parameters
        
    Returns:
        Tuple of (validated_params, errors)
    """
    # Use the shared validation logic with fields validation enabled
    return validate_content_request_base(params, require_fields=True)
