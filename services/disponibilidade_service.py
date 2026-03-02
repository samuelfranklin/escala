"""
Services para gerenciamento de disponibilidade e restrições.

Orquestra lógica pura (helpers) com operações de BD via session_scope.
Cada função é simples, responsável por uma operação.
"""

from datetime import date
from typing import List

from infra.database import Member, MemberRestrictions, session_scope
from helpers.disponibilidade import (
    parse_date_string,
    format_date_to_display,
    validate_restriction_date,
    MemberRestrictionError,
)


class DisponibilidadeService:
    """Centro de orquestra para operações de disponibilidade."""

    @staticmethod
    def create_restriction(
        member_id: str,
        date_str: str,
        description: str = "",
    ) -> dict:
        """
        Cria nova restrição de disponibilidade.

        Orquestra:
        1. Validação via helper (parse + validação de futuro)
        2. Persistência via BD

        Args:
            member_id: ID do membro
            date_str: Data em formato 'DD/MM/YYYY'
            description: Descrição opcional (ex: "Férias", "Licença")

        Returns:
            dict com chaves:
            - 'success': bool (True se criado, False se erro)
            - 'message': str (mensagem de sucesso ou erro)
            - 'restriction_id': str | None (ID se sucesso)

        Raises:
            MemberRestrictionError: Se validação falha
        """
        try:
            # Etapa 1: Validar data via helper
            validated_date = validate_restriction_date(date_str)

            # Etapa 2: Persistir
            with session_scope() as session:
                # Verificar que membro existe
                member = session.query(Member).filter(Member.id == member_id).first()
                if not member:
                    raise MemberRestrictionError(f"Membro {member_id} não encontrado.")

                # Criar restrição
                restriction = MemberRestrictions(
                    member_id=member_id,
                    date=validated_date,
                    description=description.strip() if description else None,
                )
                session.add(restriction)
                session.flush()  # Para obter o ID antes do commit
                restriction_id = restriction.id

            return {
                "success": True,
                "message": f"Restrição criada para {format_date_to_display(validated_date)}.",
                "restriction_id": restriction_id,
            }

        except MemberRestrictionError as e:
            return {
                "success": False,
                "message": str(e),
                "restriction_id": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao criar restrição: {str(e)}",
                "restriction_id": None,
            }

    @staticmethod
    def remove_restriction(member_id: str, date_str: str) -> dict:
        """
        Remove restrição de disponibilidade.

        Args:
            member_id: ID do membro
            date_str: Data em formato 'DD/MM/YYYY'

        Returns:
            dict com:
            - 'success': bool
            - 'message': str
        """
        try:
            # Parse da data para localizar
            parsed_date = parse_date_string(date_str)

            with session_scope() as session:
                restriction = (
                    session.query(MemberRestrictions)
                    .filter(
                        (MemberRestrictions.member_id == member_id)
                        & (MemberRestrictions.date == parsed_date)
                    )
                    .first()
                )

                if not restriction:
                    raise MemberRestrictionError(
                        f"Restrição não encontrada para {format_date_to_display(parsed_date)}."
                    )

                session.delete(restriction)

            return {
                "success": True,
                "message": f"Restrição de {format_date_to_display(parsed_date)} removida.",
            }

        except MemberRestrictionError as e:
            return {
                "success": False,
                "message": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao remover restrição: {str(e)}",
            }

    @staticmethod
    def get_restrictions_by_member(member_id: str) -> List[dict]:
        """
        Retorna todas as restrições de um membro.

        Returns:
            Lista de dicts com chaves: 'date', 'date_display', 'description'
        """
        try:
            with session_scope() as session:
                restrictions = (
                    session.query(MemberRestrictions)
                    .filter(MemberRestrictions.member_id == member_id)
                    .order_by(MemberRestrictions.date)
                    .all()
                )

                return [
                    {
                        "id": r.id,
                        "date": r.date,
                        "date_display": format_date_to_display(r.date),
                        "description": r.description or "",
                    }
                    for r in restrictions
                ]

        except Exception as e:
            print(f"Erro ao listar restrições: {e}")
            return []

    @staticmethod
    def is_member_available_on_date(member_id: str, check_date: date) -> bool:
        """
        Verifica se membro está disponível em data específica.

        Args:
            member_id: ID do membro
            check_date: date object a verificar

        Returns:
            bool: True se disponível (sem restrição), False se indisponível
        """
        try:
            with session_scope() as session:
                restriction = (
                    session.query(MemberRestrictions)
                    .filter(
                        (MemberRestrictions.member_id == member_id)
                        & (MemberRestrictions.date == check_date)
                    )
                    .first()
                )

                return restriction is None  # None = sem restrição = disponível

        except Exception as e:
            print(f"Erro ao verificar disponibilidade: {e}")
            return True  # Fallback: assume disponível se erro
