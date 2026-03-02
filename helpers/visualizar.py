"""Helper functions for schedule visualization and export. Pure functions without DB."""

import csv
from collections import defaultdict
from io import StringIO
from typing import Optional, List, Dict, Any, Tuple


def validate_schedule_period(month: int, year: int) -> Tuple[bool, Optional[str]]:
    """
    Validate if month and year are valid for scheduling.

    Args:
        month: Month number (1-12)
        year: Year number

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    if month < 1 or month > 12:
        return False, "Mês inválido"
    return True, None


def filter_schedule_by_period(
    schedule: List[Dict[str, Any]], month: int, year: int
) -> List[Dict[str, Any]]:
    """
    Filter schedule items by period (month/year).

    Args:
        schedule: List of schedule dictionaries with 'data' key in YYYY-MM-DD format
        month: Month to filter by (1-12)
        year: Year to filter by

    Returns:
        Filtered list of schedule items matching the period
    """
    filtered = []
    target_prefix = f"{year:04d}-{month:02d}"

    for item in schedule:
        if item.get("data", "").startswith(target_prefix):
            filtered.append(item)

    return filtered


def filter_schedule_by_squad(
    schedule: List[Dict[str, Any]], squad_name: str
) -> List[Dict[str, Any]]:
    """
    Filter schedule items by squad name.

    Args:
        schedule: List of schedule dictionaries
        squad_name: Name of the squad to filter by (case-sensitive)

    Returns:
        Filtered list of schedule items matching the squad
    """
    return [item for item in schedule if item.get("squad") == squad_name]


def filter_schedule_by_member(
    schedule: List[Dict[str, Any]], member_name: str
) -> List[Dict[str, Any]]:
    """
    Filter schedule items by member name.

    Args:
        schedule: List of schedule dictionaries
        member_name: Name of the member to filter by (case-sensitive)

    Returns:
        Filtered list of schedule items matching the member
    """
    return [item for item in schedule if item.get("membro") == member_name]


def count_allocations(schedule: List[Dict[str, Any]]) -> int:
    """
    Count total number of allocations in schedule.

    Args:
        schedule: List of schedule dictionaries

    Returns:
        Total count of items (allocations)
    """
    return len(schedule)


def group_schedule_by_event_date(
    schedule: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group schedule items by event date.

    Args:
        schedule: List of schedule dictionaries with 'data' key

    Returns:
        Dictionary where keys are dates and values are lists of items for that date
    """
    grouped = defaultdict(list)

    for item in schedule:
        data = item.get("data", "")
        grouped[data].append(item)

    return dict(grouped)


def validate_schedule_before_export(
    schedule: List[Dict[str, Any]],
) -> Tuple[bool, Optional[str]]:
    """
    Validate schedule before exporting.

    Args:
        schedule: List of schedule dictionaries to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    # Check if schedule is empty
    if not schedule:
        return False, "Escala vazia, nada para exportar"

    # Required fields for each item
    required_fields = ["data", "dia", "evento", "horario", "squad", "membro"]

    # Check each item
    for idx, item in enumerate(schedule):
        # Check if all required fields exist
        for field in required_fields:
            if field not in item:
                return False, f"Item {idx}: campo '{field}' está faltando"

        # Check if required fields are not empty
        for field in required_fields:
            if not str(item[field]).strip():
                return (
                    False,
                    f"Item {idx}: campo '{field}' não pode estar vazio",
                )

    return True, None


def export_schedule_to_csv_string(
    schedule: List[Dict[str, Any]], headers: List[str]
) -> str:
    """
    Export schedule to CSV format as string.

    Args:
        schedule: List of schedule dictionaries
        headers: List of column headers

    Returns:
        CSV string with semicolon delimiter
    """
    output = StringIO()
    writer = csv.writer(output, delimiter=";")

    # Write headers
    writer.writerow(headers)

    # Write data rows
    for item in schedule:
        row = [
            item.get("data", ""),
            item.get("dia", ""),
            item.get("evento", ""),
            item.get("horario", ""),
            item.get("squad", ""),
            item.get("membro", ""),
        ]
        writer.writerow(row)

    return output.getvalue()
