"""Pure helper functions for Squad business logic.

This module contains testable, database-agnostic functions for validating
and processing Squad operations. All functions are pure (no side effects).
"""

from typing import Optional, Tuple


# ── Rank/Patente to Level mapping ────────────────────────────────────
PATENTE_TO_LEVEL = {
    "Líder": 4,
    "Treinador": 3,
    "Membro": 2,
    "Recruta": 1,
}

LEVEL_TO_PATENTE = {v: k for k, v in PATENTE_TO_LEVEL.items()}

ALL_PATENTES = ["Líder", "Treinador", "Membro", "Recruta"]


def validate_squad_name(
    name: str, existing_names: list[str]
) -> Tuple[bool, Optional[str]]:
    """Validate squad name for creation/update.

    Args:
        name: Squad name to validate
        existing_names: List of existing squad names (excluding current squad being edited)

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
        - (True, None) if valid
        - (False, error_msg) if invalid
    """
    if not name or not name.strip():
        return False, "Nome da squad é obrigatório"

    name_stripped = name.strip()

    if name_stripped in existing_names:
        return False, "Squad com este nome já existe"

    return True, None


def validate_member_not_duplicate_in_squad(
    member_id: str, member_ids_in_squad: list[str]
) -> bool:
    """Check if member is not already in squad (prevent duplicates).

    Args:
        member_id: Member ID to check
        member_ids_in_squad: List of member IDs already in this squad

    Returns:
        True if member is not in squad (can be added), False if already present
    """
    return member_id not in member_ids_in_squad


def get_member_rank_in_squad(level: int) -> str:
    """Convert numeric level to patente string.

    Args:
        level: Numeric level (1-4)

    Returns:
        Patente string (e.g., "Líder", "Membro") or "Membro" as fallback
    """
    return LEVEL_TO_PATENTE.get(level, "Membro")


def get_rank_level(patente: str) -> int:
    """Convert patente string to numeric level.

    Args:
        patente: Patente string (e.g., "Líder", "Membro")

    Returns:
        Numeric level (1-4) or 2 (Membro) as fallback
    """
    return PATENTE_TO_LEVEL.get(patente, 2)


def count_members_in_squad(member_ids_list: list[str]) -> int:
    """Count members in a squad.

    Args:
        member_ids_list: List of member IDs in squad

    Returns:
        Member count
    """
    return len(member_ids_list)


def is_valid_patente(patente: str) -> bool:
    """Check if patente is valid.

    Args:
        patente: Patente string to validate

    Returns:
        True if patente is in the allowed list
    """
    return patente in ALL_PATENTES


def get_all_patentes() -> list[str]:
    """Get list of all valid patentes in order.

    Returns:
        List of patentes: ["Líder", "Treinador", "Membro", "Recruta"]
    """
    return ALL_PATENTES.copy()


def rank_members_by_level(
    member_squad_tuples: list[Tuple[str, str, int]]
) -> Tuple[list[Tuple[str, str, int]], list[Tuple[str, str, int]]]:
    """Partition members into enrolled and available.

    Args:
        member_squad_tuples: List of (member_id, member_name, level) tuples
            - level: 0 = not enrolled, >0 = enrolled with that level

    Returns:
        Tuple of (enrolled_list, available_list) where each contains
        only the members with level > 0 or == 0 respectively
    """
    enrolled = [m for m in member_squad_tuples if m[2] > 0]
    available = [m for m in member_squad_tuples if m[2] == 0]
    return enrolled, available
