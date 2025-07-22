"""
Validation utilities for the Content API.

This module contains validation functions specific to content operations.
"""
import re
from typing import Dict, List, Tuple, Any

# Regular expression for valid Sunbird content IDs
CONTENT_ID_PATTERN = re.compile(r'^[a-f0-9]{32}$')

def validate_content_id(content_id: str) -> List[str]:
    """Validate a Sunbird content ID.
    
    Args:
        content_id: The content ID to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    if not content_id:
        errors.append("Content ID is required")
    elif not isinstance(content_id, str):
        errors.append("Content ID must be a string")
    elif not content_id.startswith('do_'):
        errors.append("Content ID must start with 'do_'")
    elif not CONTENT_ID_PATTERN.match(content_id[3:]):
        errors.append("Content ID format is invalid")
    return errors

def validate_content_request(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate content request parameters for content retrieval API.
    Args:
        params: Raw request parameters
    Returns:
        Tuple of (validated_params, errors)
    """
    errors = []
    validated = {}

    # Validate content_id
    if 'content_id' not in params:
        errors.append("content_id is required")
    else:
        content_id = params['content_id']
        if not isinstance(content_id, str) or not content_id.strip():
            errors.append("content_id must be a non-empty string")
        elif not content_id.startswith('do_'):
            errors.append("content_id must start with 'do_'")
        else:
            validated['content_id'] = content_id

    # Validate fields (if present)
    if 'fields' in params:
        if not isinstance(params['fields'], list) or not all(isinstance(f, str) for f in params['fields']):
            errors.append("fields must be a list of strings")
        else:
            validated['fields'] = params['fields']

    return validated, errors
