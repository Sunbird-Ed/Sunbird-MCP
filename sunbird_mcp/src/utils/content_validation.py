"""
Shared content validation utilities.

This module contains common validation functions used across different content APIs.
"""
import re
from typing import Dict, List, Tuple, Any

def validate_content_id(content_id: str) -> List[str]:
    """Validate a Sunbird content ID.
    
    Valid content IDs must:
    - Start with 'do_'
    - Be followed by at least one digit
    - Not contain any other characters except digits after 'do_'
    
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
    elif len(content_id) <= 3 or not content_id[3:].isdigit():
        errors.append("Content ID must be 'do_' followed by numbers")
    return errors

def validate_content_request_base(params: Dict[str, Any], 
                                require_fields: bool = True) -> Tuple[Dict[str, Any], List[str]]:
    """
    Base validation for content requests.
    
    Args:
        params: Raw request parameters
        require_fields: Whether to validate the fields parameter
        
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
        content_id_errors = validate_content_id(content_id)
        if content_id_errors:
            errors.extend(content_id_errors)
        else:
            validated['content_id'] = content_id

    # Validate fields if required
    if require_fields and 'fields' in params:
        if not isinstance(params['fields'], list) or not all(isinstance(f, str) for f in params['fields']):
            errors.append("fields must be a list of strings")
        else:
            validated['fields'] = params['fields']

    return validated, errors
