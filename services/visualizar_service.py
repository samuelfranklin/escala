"""Service layer for schedule visualization with database operations."""

from typing import List, Dict, Any, Optional
from infra.database import session_scope, Event, Squad, Member, EventSquad, MemberSquad


def get_all_events_with_allocations() -> List[Dict[str, Any]]:
    """
    Retrieve all events with their squad allocations from database.

    Returns:
        List of dictionaries with event and allocation information
    """
    with session_scope() as session:
        events = session.query(Event).all()
        result = []

        for event in events:
            for setting in event.settings:
                result.append(
                    {
                        "event_id": event.id,
                        "event_name": event.name,
                        "event_type": event.type,
                        "date": event.date,
                        "day_of_week": event.day_of_week,
                        "time": event.time,
                        "squad_id": setting.squad_id,
                        "squad_name": setting.squad.nome,
                        "level": setting.level,
                        "quantity": setting.quantity,
                    }
                )

        return result


def get_schedule_for_period(
    month: int, year: int
) -> List[Dict[str, Any]]:
    """
    Retrieve schedule for a specific month and year from database.

    Args:
        month: Month number (1-12)
        year: Year number

    Returns:
        List of schedule items with event, squad and member allocations
    """
    with session_scope() as session:
        events = session.query(Event).all()
        result = []

        for event in events:
            # Filter events by month/year from date field (YYYY-MM-DD format)
            if event.date:
                try:
                    event_year = int(event.date.split("-")[0])
                    event_month = int(event.date.split("-")[1])

                    if event_year == year and event_month == month:
                        for setting in event.settings:
                            result.append(
                                {
                                    "data": event.date,
                                    "dia": event.day_of_week or "",
                                    "evento": event.name,
                                    "horario": event.time or "",
                                    "squad": setting.squad.nome,
                                    "squad_id": setting.squad_id,
                                    "level": setting.level,
                                    "quantity": setting.quantity,
                                }
                            )
                except (ValueError, IndexError):
                    continue

        return result


def get_squad_allocations(squad_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all allocations for a specific squad from database.

    Args:
        squad_id: ID of the squad

    Returns:
        List of allocations for the squad
    """
    with session_scope() as session:
        squad = session.query(Squad).filter(Squad.id == squad_id).first()

        if not squad:
            return []

        result = []
        for event_setting in squad.event_settings:
            event = event_setting.event
            result.append(
                {
                    "event_id": event.id,
                    "event_name": event.name,
                    "date": event.date,
                    "day_of_week": event.day_of_week,
                    "time": event.time,
                    "squad_name": squad.nome,
                    "level": event_setting.level,
                    "quantity": event_setting.quantity,
                }
            )

        return result


def get_member_allocations(member_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all allocations for a specific member from database.

    Args:
        member_id: ID of the member

    Returns:
        List of allocations for the member
    """
    with session_scope() as session:
        member = session.query(Member).filter(Member.id == member_id).first()

        if not member:
            return []

        result = []
        for membership in member.memberships:
            squad = membership.squad
            for event_setting in squad.event_settings:
                event = event_setting.event
                result.append(
                    {
                        "event_id": event.id,
                        "event_name": event.name,
                        "date": event.date,
                        "day_of_week": event.day_of_week,
                        "time": event.time,
                        "squad_name": squad.nome,
                        "member_name": member.name,
                        "member_level": membership.level,
                        "allocation_quantity": event_setting.quantity,
                    }
                )

        return result


def get_all_squads() -> List[Dict[str, str]]:
    """
    Retrieve all squads from database.

    Returns:
        List of squad dictionaries with id and nome
    """
    with session_scope() as session:
        squads = session.query(Squad).all()
        return [{"id": squad.id, "nome": squad.nome} for squad in squads]


def get_all_members() -> List[Dict[str, str]]:
    """
    Retrieve all active members from database.

    Returns:
        List of member dictionaries with id and name
    """
    with session_scope() as session:
        members = session.query(Member).filter(Member.status == True).all()
        return [{"id": member.id, "name": member.name} for member in members]


def count_event_allocations(event_id: str) -> int:
    """
    Count total allocations for a specific event.

    Args:
        event_id: ID of the event

    Returns:
        Total count of allocations for the event
    """
    with session_scope() as session:
        event = session.query(Event).filter(Event.id == event_id).first()

        if not event:
            return 0

        total = 0
        for setting in event.settings:
            total += setting.quantity

        return total


def count_squad_allocations(squad_id: str) -> int:
    """
    Count total allocations for a specific squad.

    Args:
        squad_id: ID of the squad

    Returns:
        Total count of allocations for the squad
    """
    with session_scope() as session:
        squad = session.query(Squad).filter(Squad.id == squad_id).first()

        if not squad:
            return 0

        total = 0
        for event_setting in squad.event_settings:
            total += event_setting.quantity

        return total


def get_members_by_squad(squad_id: str) -> List[Dict[str, str]]:
    """
    Retrieve all members belonging to a specific squad.

    Args:
        squad_id: ID of the squad

    Returns:
        List of member dictionaries in the squad
    """
    with session_scope() as session:
        squad = session.query(Squad).filter(Squad.id == squad_id).first()

        if not squad:
            return []

        result = []
        for membership in squad.memberships:
            result.append(
                {
                    "member_id": membership.member_id,
                    "member_name": membership.member.name,
                    "level": membership.level,
                }
            )

        return result


def get_events_by_squad(squad_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all events allocated to a specific squad.

    Args:
        squad_id: ID of the squad

    Returns:
        List of event dictionaries allocated to the squad
    """
    with session_scope() as session:
        settings = (
            session.query(EventSquad)
            .filter(EventSquad.squad_id == squad_id)
            .all()
        )

        result = []
        for setting in settings:
            event = setting.event
            result.append(
                {
                    "event_id": event.id,
                    "event_name": event.name,
                    "event_type": event.type,
                    "date": event.date,
                    "day_of_week": event.day_of_week,
                    "time": event.time,
                    "squad_level": setting.level,
                    "required_quantity": setting.quantity,
                }
            )

        return result



class VisualizarService:
    """Wrapper de classe para compatibilidade com gui/visualizar.py."""

    def get_schedule_for_period(self, month: int, year: int):
        return get_schedule_for_period(month, year)

    def get_squad_allocations(self, squad_id: str):
        return get_squad_allocations(squad_id)

    def get_member_allocations(self, member_id: str):
        return get_member_allocations(member_id)
