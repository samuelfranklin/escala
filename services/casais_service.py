"""Serviço de casais: orquestra helpers + BD.

Responsável por:
1. Validar entrada (usando helpers)
2. Operações em BD (usando session_scope)
3. Retornar resultados ou lançar exceções

Não contém lógica de UI (Tkinter).
"""

from typing import Optional

from infra.database import FamilyCouple, Member, session_scope
from helpers.casais import validate_different_spouses, couples_are_same


class CasaisService:
    """Service para operações com casais e famílias."""

    @staticmethod
    def create_couple(
        spouse1_id: str,
        spouse2_id: str,
        family_type: int = 1,
    ) -> FamilyCouple:
        """Criar novo casal na BD.

        Args:
            spouse1_id: ID do primeiro cônjuge
            spouse2_id: ID do segundo cônjuge
            family_type: Tipo de familia (default 1 = cônjuges)

        Returns:
            FamilyCouple criado

        Raises:
            ValueError: Se cônjuges são iguais ou casal já existe
        """
        # Validação: cônjuges diferentes
        if not validate_different_spouses(spouse1_id, spouse2_id):
            raise ValueError("Os cônjuges devem ser pessoas diferentes.")

        with session_scope() as session:
            # Validação: casal único (qualquer ordem)
            existe = (
                session.query(FamilyCouple)
                .filter(
                    ((FamilyCouple.member1_id == spouse1_id) & (FamilyCouple.member2_id == spouse2_id))
                    | ((FamilyCouple.member1_id == spouse2_id) & (FamilyCouple.member2_id == spouse1_id))
                )
                .first()
            )
            if existe:
                raise ValueError("Este casal já existe.")

            # Criar
            novo_casal = FamilyCouple(
                member1_id=spouse1_id,
                member2_id=spouse2_id,
                family_type=family_type,
            )
            session.add(novo_casal)
            session.commit()
            
            # Carregar ID antes de fechar session (evita DetachedInstanceError)
            couple_id = novo_casal.id
            session.expunge(novo_casal)
            novo_casal.id = couple_id
            return novo_casal

    @staticmethod
    def find_couple(spouse1_id: str, spouse2_id: str) -> Optional[FamilyCouple]:
        """Encontrar casal pela combinação de IDs.

        Alice+Bob e Bob+Alice retornam o mesmo resultado.

        Args:
            spouse1_id: ID do primeiro cônjuge
            spouse2_id: ID do segundo cônjuge

        Returns:
            FamilyCouple se encontrado, None caso contrário
        """
        with session_scope() as session:
            couple = (
                session.query(FamilyCouple)
                .filter(
                    ((FamilyCouple.member1_id == spouse1_id) & (FamilyCouple.member2_id == spouse2_id))
                    | ((FamilyCouple.member1_id == spouse2_id) & (FamilyCouple.member2_id == spouse1_id))
                )
                .first()
            )
            if couple:
                couple_id = couple.id
                m1 = couple.member1_id
                m2 = couple.member2_id
                session.expunge(couple)
                couple.id = couple_id
                couple.member1_id = m1
                couple.member2_id = m2
            return couple

    @staticmethod
    def member_has_couple(member_id: str) -> bool:
        """Verificar se membro já está em um casal.

        Args:
            member_id: ID do membro

        Returns:
            True se membro está em um casal, False caso contrário
        """
        with session_scope() as session:
            couple = (
                session.query(FamilyCouple)
                .filter(
                    (FamilyCouple.member1_id == member_id) | (FamilyCouple.member2_id == member_id)
                )
                .first()
            )
            return couple is not None

    @staticmethod
    def delete_couple(couple_id: str) -> None:
        """Deletar casal da BD.

        Args:
            couple_id: ID do casal a deletar

        Raises:
            ValueError: Se casal não existe
        """
        with session_scope() as session:
            couple = session.query(FamilyCouple).filter(FamilyCouple.id == couple_id).first()
            if not couple:
                raise ValueError("Casal não encontrado.")
            session.delete(couple)
            session.commit()

    @staticmethod
    def get_all_couples() -> list[FamilyCouple]:
        """Obter todos os casais da BD.

        Returns:
            Lista de todos os casais cadastrados
        """
        with session_scope() as session:
            couples = session.query(FamilyCouple).order_by(FamilyCouple.member1_id).all()
            
            # Força carregamento das relacionamentos antes de fechar a sessão
            for couple in couples:
                _ = couple.member1
                _ = couple.member2
            
            return couples

    @staticmethod
    def get_couple_by_id(couple_id: str) -> Optional[FamilyCouple]:
        """Obter casal pelo ID.

        Args:
            couple_id: ID do casal

        Returns:
            FamilyCouple se encontrado, None caso contrário
        """
        with session_scope() as session:
            couple = session.query(FamilyCouple).filter(FamilyCouple.id == couple_id).first()
            return couple
