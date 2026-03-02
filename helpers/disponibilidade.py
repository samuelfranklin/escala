"""
Helpers puros para lógica de disponibilidade e restrições de membros.

Funções determinísticas, sem side-effects, testáveis em isolamento.
Não fazem acesso a BD - chamadas por services.
"""

from datetime import date, datetime
from typing import Optional


class MemberRestrictionError(Exception):
    """Erro específico para operações de restrição de disponibilidade."""

    pass


def parse_date_string(date_str: str) -> date:
    """
    Converte string 'DD/MM/YYYY' em objeto date.

    Args:
        date_str: String com formato 'DD/MM/YYYY'

    Returns:
        date: Objeto date convertido

    Raises:
        MemberRestrictionError: Se formato é inválido ou data é impossível
    """
    if not date_str:
        raise MemberRestrictionError("Data não pode estar vazia.")

    date_str = date_str.strip()

    try:
        parsed = datetime.strptime(date_str, "%d/%m/%Y")
        return parsed.date()
    except ValueError as e:
        raise MemberRestrictionError(
            f"Data '{date_str}' está em formato inválido. Use DD/MM/YYYY."
        ) from e


def format_date_to_display(d: date) -> str:
    """
    Converte date em string formatada 'DD/MM/YYYY'.

    Args:
        d: Objeto date

    Returns:
        str: Data formatada como 'DD/MM/YYYY'
    """
    return d.strftime("%d/%m/%Y")


def is_date_in_future(d: date) -> bool:
    """
    Verifica se data não está no passado (hoje ou depois).

    Args:
        d: Data a validar

    Returns:
        bool: True se data >= hoje, False se no passado
    """
    today = date.today()
    return d >= today


def validate_restriction_date(date_str: str) -> date:
    """
    Valida e converte data para restrição.

    Combina:
    1. Parsing do formato DD/MM/YYYY
    2. Validação de que data não está no passado

    Args:
        date_str: String com formato 'DD/MM/YYYY'

    Returns:
        date: Data validada

    Raises:
        MemberRestrictionError: Se formato inválido OU data no passado
    """
    # Etapa 1: Parse
    try:
        parsed = parse_date_string(date_str)
    except MemberRestrictionError:
        raise

    # Etapa 2: Validar futuro
    if not is_date_in_future(parsed):
        raise MemberRestrictionError(
            f"Data {format_date_to_display(parsed)} não pode ser no passado. "
            f"Use uma data de hoje em diante."
        )

    return parsed
