"""Pure helper functions for Member validation and processing.

Functions here have no side effects and no database access.
They are pure utilities for validating names, ranks, and counting schedules.
"""

from typing import Any, Optional


def validate_member_name(name: Optional[str], existing_names: list[str]) -> tuple[bool, Optional[str]]:
    """Validate member name - must be non-empty and unique.
    
    Args:
        name: The name to validate (can be None)
        existing_names: List of existing names to check against
        
    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, error_message_string)
    """
    if name is None or not name or not name.strip():
        return False, "Nome é obrigatório"
    
    trimmed_name = name.strip()
    if trimmed_name in existing_names:
        return False, "Membro com este nome já existe"
    
    return True, None


def validate_member_rank(rank: Optional[str]) -> tuple[bool, Optional[str]]:
    """Validate member rank against allowed values.
    
    Valid ranks are: Líder, Treinador, Membro, Recruta
    
    Args:
        rank: The rank to validate (can be None)
        
    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, error_message_string)
    """
    valid_ranks = ["Líder", "Treinador", "Membro", "Recruta"]
    
    if rank not in valid_ranks:
        return False, f"Patente inválida: {rank}"
    
    return True, None


def count_member_schedules(memberships: list[Any]) -> int:
    """Count number of squad associations (schedules) for a member.
    
    This function accepts memberships as either:
    - List of dicts with 'squad_id' key
    - List of objects with 'squad_id' attribute
    
    Args:
        memberships: List of membership objects/dicts
        
    Returns:
        Integer count of memberships
    """
    return len(memberships) if memberships else 0
