"""
Feature Scaling Utilities

Handles level-scaling features with dynamic placeholders.
"""

from typing import Dict, Any, Union


def resolve_scaling_feature(feature_data: Union[str, Dict[str, Any]], character_level: int) -> str:
    """
    Replace {placeholders} in feature description with scaled values based on character level.
    
    Args:
        feature_data: Feature data (string description or dict with scaling)
        character_level: Current character level
    
    Returns:
        Resolved feature description with scaled values
    
    Example:
        >>> feature = {
        ...     "description": "Deal {damage} damage. {uses} uses per rest.",
        ...     "scaling": {
        ...         "damage": [
        ...             {"min_level": 1, "value": "1d6"},
        ...             {"min_level": 5, "value": "2d6"}
        ...         ],
        ...         "uses": [
        ...             {"min_level": 1, "value": "2"},
        ...             {"min_level": 10, "value": "3"}
        ...         ]
        ...     }
        ... }
        >>> resolve_scaling_feature(feature, 7)
        'Deal 2d6 damage. 2 uses per rest.'
    """
    # If it's just a string, return as-is
    if isinstance(feature_data, str):
        return feature_data
    
    # If it's a dict without scaling, return the description
    if not isinstance(feature_data, dict):
        return str(feature_data)
    
    description = feature_data.get('description', '')
    scaling = feature_data.get('scaling', {})
    
    # If no scaling metadata, return description as-is
    if not scaling:
        return description
    
    # Resolve each placeholder
    for placeholder, scale_list in scaling.items():
        if not isinstance(scale_list, list):
            continue
        
        # Find the highest min_level that's <= character_level
        current_value = None
        for scale in sorted(scale_list, key=lambda x: x.get('min_level', 0)):
            min_level = scale.get('min_level', 0)
            if character_level >= min_level:
                current_value = scale.get('value', '')
        
        # Replace placeholder with current value
        if current_value is not None:
            description = description.replace(f'{{{placeholder}}}', str(current_value))
    
    return description


def get_scaling_value(scaling_data: list, character_level: int) -> Any:
    """
    Get the scaled value for a specific character level.
    
    Args:
        scaling_data: List of scaling breakpoints
        character_level: Current character level
    
    Returns:
        The scaled value for the current level
    
    Example:
        >>> scaling = [
        ...     {"min_level": 1, "value": "1d6"},
        ...     {"min_level": 5, "value": "2d6"},
        ...     {"min_level": 10, "value": "3d6"}
        ... ]
        >>> get_scaling_value(scaling, 7)
        '2d6'
    """
    if not isinstance(scaling_data, list):
        return None
    
    current_value = None
    for scale in sorted(scaling_data, key=lambda x: x.get('min_level', 0)):
        min_level = scale.get('min_level', 0)
        if character_level >= min_level:
            current_value = scale.get('value')
    
    return current_value
