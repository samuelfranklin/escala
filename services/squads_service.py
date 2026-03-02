"""Squad service layer.

This module orchestrates helpers and database operations for Squad management.
Uses session_scope() for database transactions.
"""

from typing import Optional

from infra.database import Member, MemberSquad, Squad, session_scope
from helpers.squads import (
    get_rank_level,
    validate_member_not_duplicate_in_squad,
    validate_squad_name,
)


class SquadsService:
    """Service for Squad operations with database integration."""

    @staticmethod
    def create_squad(name: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Create a new squad."""
        with session_scope() as session:
            existing_squads = session.query(Squad).all()
            existing_names = [s.nome for s in existing_squads]

            is_valid, error = validate_squad_name(name, existing_names)
            if not is_valid:
                return False, error, None

            squad = Squad(nome=name.strip())
            session.add(squad)
            session.flush()
            squad_id = squad.id

        return True, None, squad_id

    @staticmethod
    def update_squad_name(squad_id: str, new_name: str) -> tuple[bool, Optional[str]]:
        """Update squad name."""
        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            if not squad:
                return False, "Equipe não encontrada."

            other_squads = session.query(Squad).filter(Squad.id != squad_id).all()
            other_names = [s.nome for s in other_squads]

            is_valid, error = validate_squad_name(new_name, other_names)
            if not is_valid:
                return False, error

            squad.nome = new_name.strip()

        return True, None

    @staticmethod
    def delete_squad(squad_id: str) -> tuple[bool, Optional[str]]:
        """Delete a squad."""
        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            if not squad:
                return False, "Equipe não encontrada."

            session.delete(squad)

        return True, None

    @staticmethod
    def add_member_to_squad(
        squad_id: str, member_id: str, patente: str
    ) -> tuple[bool, Optional[str]]:
        """Add member to squad with specified rank."""
        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            if not squad:
                return False, "Equipe não encontrada."

            member = session.query(Member).filter(Member.id == member_id).first()
            if not member:
                return False, "Membro não encontrado."

            existing = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == squad_id,
                    MemberSquad.member_id == member_id,
                )
                .first()
            )
            if existing:
                return False, "Membro já está neste time."

            level = get_rank_level(patente)
            membership = MemberSquad(
                member_id=member_id, squad_id=squad_id, level=level
            )
            session.add(membership)

        return True, None

    @staticmethod
    def remove_member_from_squad(squad_id: str, member_id: str) -> tuple[bool, Optional[str]]:
        """Remove member from squad."""
        with session_scope() as session:
            membership = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == squad_id,
                    MemberSquad.member_id == member_id,
                )
                .first()
            )
            if not membership:
                return False, "Membro não está neste time."

            session.delete(membership)

        return True, None

    @staticmethod
    def update_member_rank_in_squad(
        squad_id: str, member_id: str, patente: str
    ) -> tuple[bool, Optional[str]]:
        """Update member rank in squad."""
        with session_scope() as session:
            membership = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == squad_id,
                    MemberSquad.member_id == member_id,
                )
                .first()
            )
            if not membership:
                return False, "Membro não está neste time."

            level = get_rank_level(patente)
            membership.level = level

        return True, None

    @staticmethod
    def get_squad_by_id(squad_id: str) -> Optional[dict]:
        """Retrieve squad details by ID."""
        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            if not squad:
                return None

            memberships = session.query(MemberSquad).filter(
                MemberSquad.squad_id == squad_id
            ).all()

            squad_data = {
                'id': squad.id,
                'nome': squad.nome,
                'member_count': len(memberships),
                'memberships': [
                    {
                        'member_id': m.member_id,
                        'level': m.level,
                    }
                    for m in memberships
                ]
            }

        return squad_data

    @staticmethod
    def get_all_squads() -> list[dict]:
        """Retrieve all squads with member counts."""
        squads = []
        with session_scope() as session:
            all_squads = session.query(Squad).order_by(Squad.nome).all()

            for squad in all_squads:
                member_count = (
                    session.query(MemberSquad)
                    .filter(MemberSquad.squad_id == squad.id)
                    .count()
                )
                squads.append({
                    'id': squad.id,
                    'nome': squad.nome,
                    'member_count': member_count,
                })

        return squads

    @staticmethod
    def get_squad_members(squad_id: str) -> list[dict]:
        """Retrieve all members in a squad with their ranks."""
        members = []
        with session_scope() as session:
            memberships = (
                session.query(MemberSquad)
                .filter(MemberSquad.squad_id == squad_id)
                .all()
            )

            for membership in memberships:
                member = session.query(Member).filter(
                    Member.id == membership.member_id
                ).first()
                if member:
                    members.append({
                        'member_id': membership.member_id,
                        'name': member.name,
                        'level': membership.level,
                    })

        return members

    @staticmethod
    def get_all_members() -> list[dict]:
        """Retrieve all members ordered by name."""
        members = []
        with session_scope() as session:
            all_members = session.query(Member).order_by(Member.name).all()
            members = [
                {
                    'id': m.id,
                    'name': m.name,
                }
                for m in all_members
            ]
        return members

    @staticmethod
    def bulk_update_squad_memberships(
        squad_id: str, memberships: list[tuple[str, int]]
    ) -> tuple[bool, Optional[str]]:
        """Replace all squad memberships in one operation."""
        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            if not squad:
                return False, "Equipe não encontrada."

            session.query(MemberSquad).filter(
                MemberSquad.squad_id == squad_id
            ).delete(synchronize_session=False)

            for member_id, level in memberships:
                member = session.query(Member).filter(Member.id == member_id).first()
                if not member:
                    return False, f"Membro {member_id} não encontrado."

                membership = MemberSquad(
                    member_id=member_id,
                    squad_id=squad_id,
                    level=level,
                )
                session.add(membership)

        return True, None
