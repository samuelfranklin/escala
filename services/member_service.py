from sqlalchemy.exc import IntegrityError

from infra.database import Member, MemberSquad, Squad, session_scope


class MemberService:
    def __init__(self):
        pass

    def create_member(
        self,
        name: str,
        birth_date: str,
        phone_number: str,
        email: str,
        instagram: str,
        status: bool = True,
    ) -> Member:
        with session_scope() as session:
            new_member = Member(
                name=name,
                birth_date=birth_date,
                phone_number=phone_number,
                email=email,
                instagram=instagram,
                status=status,
            )
            session.add(new_member)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raise
            return new_member

    def get_all_members(self) -> list[Member]:
        with session_scope() as session:
            try:
                members = session.query(Member).all()
                return members
            except Exception as e:
                print(f"Erro ao buscar membros: {e}")
                return []

    def get_member_by_id(self, member_id: str) -> Member | None:
        with session_scope() as session:
            try:
                member = session.query(Member).filter_by(id=member_id).first()
                return member
            except Exception as e:
                print(f"Erro ao buscar membro por ID: {e}")
                return None

    def update_member(self, member: Member) -> Member | None:
        with session_scope() as session:
            try:
                existing_member = session.query(Member).filter_by(id=member.id).first()
                if not existing_member:
                    raise ValueError("Membro não encontrado")
                existing_member.name = member.name
                existing_member.birth_date = member.birth_date
                existing_member.phone_number = member.phone_number
                existing_member.email = member.email
                existing_member.instagram = member.instagram
                existing_member.status = member.status
                session.commit()
                return existing_member
            except Exception as e:
                print(f"Erro ao atualizar membro: {e}")
                return None

    def remove_member(self, member_id: str) -> bool:
        with session_scope() as session:
            try:
                member = self.get_member_by_id(member_id)
                if not member:
                    raise ValueError("Membro não encontrado")
                member.status = False  # Marca como inativo
                session.commit()
                return member
            except Exception as e:
                print(f"Erro ao remover membro: {e}")
                return False

    def reactivate_member(self, member_id: str) -> bool:
        with session_scope() as session:
            try:
                member = self.get_member_by_id(member_id)
                if not member:
                    raise ValueError("Membro não encontrado")
                member.status = True  # Marca como ativo
                session.commit()
                return member
            except Exception as e:
                print(f"Erro ao reativar membro: {e}")
                return False

    def define_member_squads(self, member_id: Member, squad_ids: list[str]) -> bool:
        with session_scope() as session:
            try:
                member = self.get_member_by_id(member_id)
                if not member:
                    raise ValueError("Membro não encontrado")
                # Limpa as associações atuais
                member.memberships.clear()
                # Adiciona novas associações
                for squad_id in squad_ids:
                    membership = MemberSquad(member_id=member.id, squad_id=squad_id)
                    member.memberships.append(membership)
                session.commit()
                return True
            except Exception as e:
                print(f"Erro ao definir squads para membro: {e}")
                return False

    def get_member_squads(self, member_id: Member) -> list[Squad]:
        with session_scope():
            try:
                member = self.get_member_by_id(member_id)
                if not member:
                    raise ValueError("Membro não encontrado")
                squads = [membership.squad for membership in member.memberships]
                return squads
            except Exception as e:
                print(f"Erro ao buscar squads de membro: {e}")
                return []
