# d:\\sunbird_mcp\\Sunbird-MCP\\sunbird_mcp\\src\\api\\sandbox_search\\validation.py
"""Validation for Sandbox Search API."""
from typing import Dict, List, Tuple, Any, Optional
from config import settings


def validate_filters(filters: Dict[str, Any]) -> List[str]:
    """
    Validate the provided filters against allowed values for sandbox environment.
    
    Args:
        filters: Dictionary of filter parameters to validate
    
    Returns:
        List of error messages for invalid filters, empty list if all are valid
    """
    if not settings.ENABLE_INPUT_VALIDATION:
        return []
        
    errors = []
    if not isinstance(filters, dict):
        return ["Filters must be a dictionary"]
        
    for key, values in filters.items():
        if key not in settings.SANDBOX_FILTERS:
            errors.append(f"Invalid filter key: {key}")
            continue
            
        if not isinstance(values, list):
            values = [values]
            
        valid_values = settings.SANDBOX_FILTERS.get(key, [])
        for value in values:
            if value not in valid_values:
                errors.append(
                    f"Invalid value '{value}' for filter '{key}'. "
                    f"Must be one of: {', '.join(valid_values)}"
                )
    
    return errors


def validate_fields_and_facets(fields: Optional[List[str]], facets: Optional[List[str]]) -> List[str]:
    """
    Validate the requested fields and facets against allowed values for sandbox.
    
    Args:
        fields: List of field names to include in the response
        facets: List of facet names to include in the response
        
    Returns:
        List of error messages for invalid fields/facets, empty list if all are valid
    """
    if not settings.ENABLE_INPUT_VALIDATION:
        return []
        
    errors = []
    
    if fields:
        for field in fields:
            if field not in settings.SANDBOX_DEFAULT_FIELDS:
                errors.append(f"Invalid field: {field}")
                
    if facets:
        for facet in facets:
            if facet not in settings.SANDBOX_VALID_FACETS:
                errors.append(f"Invalid facet: {facet}")
                
    return errors


def validate_search_params(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and sanitize search parameters for sandbox environment.
    
    Args:
        params: Raw search parameters
        
    Returns:
        Tuple of (validated_params, errors)
    """
    errors = []
    validated = {
        "query": "",
        "filters": {},
        "limit": 10,
        "offset": 0,
        "sort_by": {},
        "fields": settings.SANDBOX_DEFAULT_FIELDS.copy(),
        "facets": settings.SANDBOX_VALID_FACETS.copy()
    }
    
    # Validate query
    if 'query' in params and params['query']:
        if not isinstance(params['query'], str):
            errors.append("Query must be a string")
        else:
            validated['query'] = params['query'].strip()
    
    # Validate filters
    if 'filters' in params and params['filters']:
        if not isinstance(params['filters'], dict):
            errors.append("Filters must be a dictionary")
        else:
            validated['filters'] = params['filters']
            errors.extend(validate_filters(params['filters']))
    
    # Validate pagination
    if 'limit' in params:
        try:
            limit = int(params['limit'])
            if not (1 <= limit <= 100):
                raise ValueError
            validated['limit'] = limit
        except (ValueError, TypeError):
            errors.append("Limit must be an integer between 1 and 100")
    
    if 'offset' in params:
        try:
            offset = int(params['offset'])
            if offset < 0:
                raise ValueError
            validated['offset'] = offset
        except (ValueError, TypeError):
            errors.append("Offset must be a non-negative integer")
    
    # Validate fields and facets
    fields = params.get('fields', [])
    facets = params.get('facets', [])
    if fields or facets:
        errors.extend(validate_fields_and_facets(fields, facets))
    
    if 'fields' in params:
        if isinstance(params['fields'], list) and all(isinstance(x, str) for x in params['fields']):
            validated['fields'] = params['fields']
    
    if 'facets' in params:
        if isinstance(params['facets'], list) and all(isinstance(x, str) for x in params['facets']):
            validated['facets'] = params['facets']
    
    # Validate sort_by
    if 'sort_by' in params and params['sort_by']:
        if not isinstance(params['sort_by'], dict) or not all(
            isinstance(k, str) and isinstance(v, str) 
            for k, v in params['sort_by'].items()
        ):
            errors.append("sort_by must be a dictionary of string key-value pairs")
        else:
            validated['sort_by'] = params['sort_by']
    
    return validated, errors
