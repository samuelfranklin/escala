"""Member Service - Orchestrates helper functions with database operations.

This service uses session_scope() to manage database transactions
and calls pure helper functions for validation logic.
"""

from typing import Optional

from infra.database import Member, MemberSquad, Squad, session_scope
from helpers.membros import (
    validate_member_name,
    validate_member_rank,
    count_member_schedules,
)


class MembrosService:
    """Service for Member operations with database integration."""

    @staticmethod
    def get_all_members() -> list[Member]:
        """Fetch all active members from database.
        
        Returns:
            List of Member objects ordered by name
        """
        with session_scope() as session:
            try:
                members = session.query(Member).filter_by(status=True).order_by(Member.name).all()
                return members
            except Exception as e:
                print(f"Erro ao buscar membros: {e}")
                return []

    @staticmethod
    def get_member_by_id(member_id: str) -> Optional[Member]:
        """Fetch a single member by ID.
        
        Args:
            member_id: UUID of the member
            
        Returns:
            Member object or None if not found
        """
        with session_scope() as session:
            try:
                member = session.query(Member).filter_by(id=member_id, status=True).first()
                return member
            except Exception as e:
                print(f"Erro ao buscar membro: {e}")
                return None

    @staticmethod
    def create_member(
        name: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        instagram: Optional[str] = None,
    ) -> Optional[Member]:
        """Create a new member with validation.
        
        Validates that:
        - Name is not empty
        - Name is unique in database
        
        Args:
            name: Member's name
            phone_number: Optional phone number
            email: Optional email address
            instagram: Optional Instagram handle
            
        Returns:
            Created Member object or None if validation failed
        """
        # Validate name is not empty
        valid, error = validate_member_name(name, [])
        if not valid:
            print(f"Validação de nome falhou: {error}")
            return None
        
        # Check for duplicates in database
        with session_scope() as session:
            existing = session.query(Member).filter_by(name=name.strip(), status=True).first()
            if existing:
                print("Membro com este nome já existe")
                return None
            
            try:
                new_member = Member(
                    name=name.strip(),
                    phone_number=phone_number,
                    email=email,
                    instagram=instagram,
                    status=True,
                )
                session.add(new_member)
                session.commit()
                return new_member
            except Exception as e:
                print(f"Erro ao criar membro: {e}")
                return None

    @staticmethod
    def update_member(
        member_id: str,
        name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        instagram: Optional[str] = None,
    ) -> Optional[Member]:
        """Update member details with validation.
        
        If name is provided, validates uniqueness (excluding current member).
        
        Args:
            member_id: UUID of member to update
            name: New name (optional)
            phone_number: New phone number (optional)
            email: New email (optional)
            instagram: New Instagram handle (optional)
            
        Returns:
            Updated Member object or None if failed
        """
        with session_scope() as session:
            member = session.query(Member).filter_by(id=member_id).first()
            if not member:
                print("Membro não encontrado")
                return None
            
            # Validate new name if provided
            if name is not None:
                # Get all other members' names for uniqueness check
                other_names = [
                    m.name for m in session.query(Member).filter(Member.id != member_id, Member.status == True).all()
                ]
                valid, error = validate_member_name(name, other_names)
                if not valid:
                    print(f"Validação de nome falhou: {error}")
                    return None
                member.name = name.strip()
            
            # Update optional fields
            if phone_number is not None:
                member.phone_number = phone_number
            if email is not None:
                member.email = email
            if instagram is not None:
                member.instagram = instagram
            
            try:
                session.commit()
                return member
            except Exception as e:
                print(f"Erro ao atualizar membro: {e}")
                return None

    @staticmethod
    def delete_member(member_id: str) -> bool:
        """Delete (soft delete - mark as inactive) a member.
        
        Args:
            member_id: UUID of member to delete
            
        Returns:
            True if successful, False otherwise
        """
        with session_scope() as session:
            member = session.query(Member).filter_by(id=member_id).first()
            if not member:
                print("Membro não encontrado")
                return False
            
            try:
                member.status = False
                session.commit()
                return True
            except Exception as e:
                print(f"Erro ao deletar membro: {e}")
                return False

    @staticmethod
    def get_member_schedule_count(member_id: str) -> int:
        """Get the number of squads a member belongs to.
        
        Args:
            member_id: UUID of member
            
        Returns:
            Count of squad memberships
        """
        with session_scope() as session:
            member = session.query(Member).filter_by(id=member_id).first()
            if not member:
                return 0
            
            # Use the pure helper function
            return count_member_schedules(member.memberships)

    @staticmethod
    def get_all_member_names() -> list[str]:
        """Get list of all active member names for validation/uniqueness checks.
        
        Returns:
            List of member names
        """
        with session_scope() as session:
            members = session.query(Member).filter_by(status=True).all()
            return [m.name for m in members]

    @staticmethod
    def assign_member_to_squad(
        member_id: str,
        squad_id: str,
        level: int = 1
    ) -> Optional[MemberSquad]:
        """Assign a member to a squad with a rank level.
        
        Args:
            member_id: UUID of member
            squad_id: UUID of squad
            level: Rank level (1-4, default 1 for Recruta)
            
        Returns:
            Created MemberSquad object or None if failed
        """
        with session_scope() as session:
            member = session.query(Member).filter_by(id=member_id).first()
            if not member:
                print("Membro não encontrado")
                return None
            
            squad = session.query(Squad).filter_by(id=squad_id).first()
            if not squad:
                print("Squad não encontrada")
                return None
            
            # Check if already assigned
            existing = session.query(MemberSquad).filter_by(
                member_id=member_id,
                squad_id=squad_id
            ).first()
            if existing:
                print("Membro já está neste squad")
                return None
            
            try:
                ms = MemberSquad(
                    member_id=member_id,
                    squad_id=squad_id,
                    level=level
                )
                session.add(ms)
                session.commit()
                return ms
            except Exception as e:
                print(f"Erro ao atribuir membro ao squad: {e}")
                return None

    @staticmethod
    def remove_member_from_squad(member_id: str, squad_id: str) -> bool:
        """Remove a member from a squad.
        
        Args:
            member_id: UUID of member
            squad_id: UUID of squad
            
        Returns:
            True if successful, False otherwise
        """
        with session_scope() as session:
            ms = session.query(MemberSquad).filter_by(
                member_id=member_id,
                squad_id=squad_id
            ).first()
            if not ms:
                print("Associação membro-squad não encontrada")
                return False
            
            try:
                session.delete(ms)
                session.commit()
                return True
            except Exception as e:
                print(f"Erro ao remover membro do squad: {e}")
                return False

    @staticmethod
    def get_member_squads(member_id: str) -> list[Squad]:
        """Get all squads that a member belongs to.
        
        Args:
            member_id: UUID of member
            
        Returns:
            List of Squad objects
        """
        with session_scope() as session:
            member = session.query(Member).filter_by(id=member_id).first()
            if not member:
                return []
            
            squads = [ms.squad for ms in member.memberships]
            return squads

    @staticmethod
    def get_all_squads() -> list[Squad]:
        """Fetch all active squads ordered by name.
        
        Returns:
            List of Squad objects
        """
        with session_scope() as session:
            try:
                squads = session.query(Squad).filter_by(status=True).order_by(Squad.nome).all()
                return squads
            except Exception as e:
                print(f"Erro ao buscar squads: {e}")
                return []
