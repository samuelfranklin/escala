"""Lógica pura para validação e processamento de casais.

Todas as funções são determinísticas e sem side-effects,
facilitando testes e reuso.
"""


def validate_different_spouses(spouse1_id: str, spouse2_id: str) -> bool:
    """Validar que os dois cônjuges são pessoas diferentes.

    Args:
        spouse1_id: ID do primeiro cônjuge
        spouse2_id: ID do segundo cônjuge

    Returns:
        True se são IDs diferentes, False caso contrário.
    """
    return spouse1_id != spouse2_id


def couple_key(spouse1_id: str, spouse2_id: str) -> tuple:
    """Gerar chave canônica para um casal.

    Alice+Bob e Bob+Alice geram a mesma chave,
    permitindo detectar duplicatas.

    Args:
        spouse1_id: ID do primeiro cônjuge
        spouse2_id: ID do segundo cônjuge

    Returns:
        Tuple com IDs ordenados alfabeticamente.
    """
    return tuple(sorted([spouse1_id, spouse2_id]))


def couples_are_same(
    spouse1_id_a: str,
    spouse2_id_a: str,
    spouse1_id_b: str,
    spouse2_id_b: str,
) -> bool:
    """Verificar se dois casais representam a mesma relação.

    Considera que Alice+Bob == Bob+Alice.

    Args:
        spouse1_id_a: ID do primeiro cônjuge do casal A
        spouse2_id_a: ID do segundo cônjuge do casal A
        spouse1_id_b: ID do primeiro cônjuge do casal B
        spouse2_id_b: ID do segundo cônjuge do casal B

    Returns:
        True se representam o mesmo casal, False caso contrário.
    """
    return couple_key(spouse1_id_a, spouse2_id_a) == couple_key(
        spouse1_id_b, spouse2_id_b
    )
