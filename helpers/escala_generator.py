"""
Helpers para gerador de escala - Funções PURAS (sem BD, sem logging pesado).

Arquitetura:
- Funções puras: input -> output determinístico
- Sem side-effects
- Sem acesso a BD
- Reutilizáveis em contextos diferentes
- 100% testáveis

Padrões SOLID:
- Single Responsibility: cada função faz UMA coisa
- Composição: usado por services para orquestração + BD
"""

from typing import Optional, Tuple, List, Dict, Any


def is_valid_month(month: Any, year: Any) -> Tuple[bool, str]:
    """
    Valida mês (1-12) e ano.
    
    Args:
        month: int ou str (1-12)
        year: int ou str (positivo)
    
    Returns:
        (sucesso, mensagem)
    """
    try:
        m = int(month)
        y = int(year)
    except (ValueError, TypeError):
        return False, "Mês e ano devem ser números"
    
    if not (1 <= m <= 12):
        return False, f"Mês deve estar entre 1 e 12, recebido: {m}"
    
    if y <= 0:
        return False, f"Ano deve ser positivo, recebido: {y}"
    
    return True, ""


def format_date_string(day: Any, month: Any, year: Any) -> str:
    """
    Formata (dia, mês, ano) -> 'DD/MM/YYYY'.
    
    Args:
        day: int ou str (1-31)
        month: int ou str (1-12)
        year: int ou str
    
    Returns:
        String formatada 'DD/MM/YYYY'
    
    Raises:
        ValueError: Se data inválida
    """
    try:
        d = int(day)
        m = int(month)
        y = int(year)
    except (ValueError, TypeError):
        raise ValueError("Dia, mês e ano devem ser números")
    
    if not (1 <= d <= 31):
        raise ValueError(f"Dia inválido: {d}")
    if not (1 <= m <= 12):
        raise ValueError(f"Mês inválido: {m}")
    if y <= 0:
        raise ValueError(f"Ano inválido: {y}")
    
    return f"{d:02d}/{m:02d}/{y}"


def parse_date_string(date_str: Any) -> Optional[Tuple[int, int, int]]:
    """
    Parse 'DD/MM/YYYY' -> (dia, mês, ano).
    
    Args:
        date_str: String no formato 'DD/MM/YYYY' ou None
    
    Returns:
        (dia, mês, ano) ou None se formato inválido
    """
    if date_str is None or not isinstance(date_str, str):
        return None
    
    try:
        parts = date_str.split("/")
        if len(parts) != 3:
            return None
        
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
        
        if not (1 <= day <= 31):
            return None
        if not (1 <= month <= 12):
            return None
        if year <= 0:
            return None
        
        return (day, month, year)
    except (ValueError, AttributeError):
        return None


def process_couples(
    available_members: List[Tuple[str, str]],
    couples_map: Dict[str, str],
) -> List[Any]:
    """
    Processa casais: se membro1 selecionado, membro2 também deve estar.
    
    Lógica:
    - Se ambos do casal estão em available_members, mantém ambos
    - Se apenas um está, remove ambos (casal não pode ser quebrado)
    - Se nenhum em couples_map, retorna como está
    
    Args:
        available_members: Lista de (nome, patente)
        couples_map: Dict {nome1: nome2, nome2: nome1}
    
    Returns:
        Lista filtrada de (nome, patente)
    """
    if not available_members or not couples_map:
        return available_members
    
    # Construir dicts para acesso rápido
    member_names = {name for name, _ in available_members}
    name_to_patron = {name: patron for name, patron in available_members}
    
    # Track which members são parte de casais ambos disponíveis
    valid_members = set()
    processed_couples = set()
    
    for name in member_names:
        if name in processed_couples:
            continue
        
        partner = couples_map.get(name)
        
        if partner and partner in member_names and partner not in processed_couples:
            # Casal completo - ambos podem ser adicionados
            valid_members.add(name)
            valid_members.add(partner)
            processed_couples.add(name)
            processed_couples.add(partner)
        elif not partner or partner not in member_names:
            # Sem parceiro ou parceiro não disponível - exclui este membro
            # (respeitando regra de casal)
            processed_couples.add(name)
    
    return [(name, name_to_patron[name]) for name in valid_members]


def apply_balance_distribution(
    members: List[str],
    counts_dict: Dict[str, int],
) -> List[str]:
    """
    Ordena membros por menos escalados primeiro (equilíbrio).
    
    Args:
        members: Lista de nomes
        counts_dict: {nome: quantidade_escalada}
    
    Returns:
        Lista ordenada de nomes (menos escalados primeiro)
    """
    if not members:
        return []
    
    def get_count(name: str) -> int:
        return counts_dict.get(name, 0)
    
    return sorted(members, key=get_count)


def can_add_trainee_with_leader(
    selected_members: List[Tuple[str, str]],
) -> bool:
    """
    Verifica se há Líder ou Treinador entre os selecionados.
    
    Regra: Recruta só pode escalar se há pelo menos um Líder ou Treinador.
    
    Args:
        selected_members: Lista de (nome, patente)
    
    Returns:
        True se há Líder/Treinador
    """
    if not selected_members:
        return False
    
    return any(
        patron in ("Líder", "Treinador")
        for _, patron in selected_members
    )


def format_schedule_entry(
    event_name: str,
    date: str,
    day_name: str,
    time: str,
    squad_name: str,
    member_name: str,
) -> Dict[str, str]:
    """
    Formata entrada de escala como dicionário.
    
    Args:
        event_name: Nome do evento
        date: Data em formato 'DD/MM/YYYY'
        day_name: Nome do dia (Segunda, Terça, etc)
        time: Horário (HH:MM)
        squad_name: Nome da squad
        member_name: Nome do membro
    
    Returns:
        Dict com campos: evento, data, dia_semana, horario, squad, membro
    """
    return {
        "evento": event_name,
        "data": date,
        "dia_semana": day_name,
        "horario": time,
        "squad": squad_name,
        "membro": member_name,
    }


def get_patron_rank(patron: str) -> int:
    """
    Retorna rank numérico da patente (menor = selecionado antes).
    
    Args:
        patron: Nome da patente
    
    Returns:
        0 = Líder (primeiro), 1 = Treinador, 2 = Membro, 3+ = Recruta (último)
    """
    rank_map = {
        "Líder": 0,
        "Treinador": 1,
        "Membro": 2,
        "Recruta": 3,
    }
    return rank_map.get(patron, 4)


def select_members_by_patron(
    available_members: List[Tuple[str, str]],
) -> List[Tuple[str, str]]:
    """
    Ordena membros por rank de patente: Líder > Treinador > Membro > Recruta.
    
    Args:
        available_members: Lista de (nome, patente)
    
    Returns:
        Lista ordenada por patente (melhor primeiro)
    """
    if not available_members:
        return []
    
    return sorted(available_members, key=lambda x: get_patron_rank(x[1]))


def count_people_in_selection(selection: List[Any]) -> int:
    """
    Conta quantas pessoas estão na seleção.
    
    Regra:
    - Tupla (nome, patente) = 1 pessoa
    - String "CASAL:nome1 & nome2" = 2 pessoas
    
    Args:
        selection: Lista contendo tuplas ou strings de casal
    
    Returns:
        Contagem total de pessoas
    """
    count = 0
    for item in selection:
        if isinstance(item, tuple):
            count += 1
        elif isinstance(item, str) and item.startswith("CASAL:"):
            count += 2
    return count
