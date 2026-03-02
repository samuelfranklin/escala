"""
Helpers puros para validação e processamento de eventos.

Funções neste módulo não possuem side-effects e não acessam o banco de dados.
Podem ser testadas isoladamente e reutilizadas em qualquer contexto.
"""

from typing import Optional


def validate_event_name(name: str, existing_names: list[str] = None) -> tuple[bool, str]:
    """
    Valida o nome de um evento.
    
    Regras:
    - Nome não pode ser vazio
    - Nome não pode duplicar nomes existentes
    
    Args:
        name: Nome do evento a validar
        existing_names: Lista de nomes já existentes (para garantir unicidade)
    
    Returns:
        (is_valid, error_message) - (True, "") se válido, (False, mensagem) se inválido
    """
    if not name or not name.strip():
        return False, "Nome do evento não pode ser vazio."
    
    name = name.strip()
    
    if existing_names and name in existing_names:
        return False, f"Já existe um evento com o nome '{name}'."
    
    return True, ""


def validate_event_type(event_type: str) -> tuple[bool, str]:
    """
    Valida o tipo de evento.
    
    Tipos aceitos: "fixo", "sazonal", "eventual"
    
    Args:
        event_type: Tipo do evento a validar
    
    Returns:
        (is_valid, error_message)
    """
    valid_types = ["fixo", "sazonal", "eventual"]
    
    if not event_type or event_type not in valid_types:
        return False, f"Tipo de evento inválido. Deve ser um de: {', '.join(valid_types)}"
    
    return True, ""


def validate_day_of_week(day: str) -> tuple[bool, str]:
    """
    Valida dia da semana (para eventos tipo "fixo").
    
    Aceita nomes em EN ou PT-BR:
    - EN: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
    - PT-BR: Segunda-feira, Terça-feira, Quarta-feira, Quinta-feira, Sexta-feira, Sábado, Domingo
    
    Args:
        day: Nome do dia da semana
    
    Returns:
        (is_valid, error_message)
    """
    valid_days_en = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ]
    valid_days_pt = [
        "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
        "Sexta-feira", "Sábado", "Domingo"
    ]
    
    if not day or day not in valid_days_en + valid_days_pt:
        return False, f"Dia da semana inválido: '{day}'"
    
    return True, ""


def validate_date(date_str: str) -> tuple[bool, str]:
    """
    Valida data em formato DD/MM/YYYY (para eventos tipo "sazonal" ou "eventual").
    
    Args:
        date_str: String de data no formato DD/MM/YYYY
    
    Returns:
        (is_valid, error_message)
    """
    if not date_str or not date_str.strip():
        return False, "Data não pode ser vazia."
    
    date_str = date_str.strip()
    
    try:
        parts = date_str.split("/")
        if len(parts) != 3:
            return False, "Data deve estar no formato DD/MM/YYYY"
        
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        
        # Validar que ano tem 4 dígitos (simples check)
        if year < 1000 or year > 9999:
            return False, "Data inválida. Use formato DD/MM/YYYY com números."
        
        # Validações básicas
        if not (1 <= month <= 12):
            return False, "Mês inválido (deve estar entre 01 e 12)."
        
        if month in [1, 3, 5, 7, 8, 10, 12] and not (1 <= day <= 31):
            return False, f"Dia inválido para mês {month}."
        elif month in [4, 6, 9, 11] and not (1 <= day <= 30):
            return False, f"Dia inválido para mês {month}."
        elif month == 2:
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            max_day = 29 if is_leap else 28
            if not (1 <= day <= max_day):
                return False, f"Dia inválido para fevereiro de {year}."
        
        if year < 2000 or year > 2100:
            return False, "Ano deve estar entre 2000 e 2100."
        
        return True, ""
    
    except (ValueError, IndexError):
        return False, "Data inválida. Use formato DD/MM/YYYY com números."


def validate_time(time_str: str) -> tuple[bool, str]:
    """
    Valida horário em formato HH:MM (00:00 a 23:59).
    
    Args:
        time_str: String de horário no formato HH:MM
    
    Returns:
        (is_valid, error_message)
    """
    if not time_str or not time_str.strip():
        return False, "Horário não pode ser vazio."
    
    time_str = time_str.strip()
    
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return False, "Horário deve estar no formato HH:MM"
        
        hour, minute = int(parts[0]), int(parts[1])
        
        if not (0 <= hour <= 23):
            return False, "Hora deve estar entre 00 e 23."
        
        if not (0 <= minute <= 59):
            return False, "Minutos devem estar entre 00 e 59."
        
        return True, ""
    
    except (ValueError, IndexError):
        return False, "Horário inválido. Use formato HH:MM com números."


def validate_event_squads(squad_quantities: dict) -> tuple[bool, str]:
    """
    Valida configuração de squads para um evento.
    
    Regras:
    - squad_quantities deve ser um dicionário
    - Cada valor deve ser um inteiro >= 0
    - Se vazio, é aceito (será implementado em service)
    
    Args:
        squad_quantities: Dict com {squad_id: quantity, ...}
    
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(squad_quantities, dict):
        return False, "Squad quantities deve ser um dicionário."
    
    for squad_id, quantity in squad_quantities.items():
        if not isinstance(quantity, int) or quantity < 0:
            return False, f"Quantidade para squad '{squad_id}' deve ser um inteiro >= 0."
    
    return True, ""


def normalize_event_name(name: str) -> str:
    """
    Normaliza nome de evento (remove espaços extras).
    
    Args:
        name: Nome do evento
    
    Returns:
        Nome normalizado
    """
    return name.strip() if name else ""


def normalize_time(time_str: str) -> str:
    """
    Normaliza horário (zero-padding: "9:30" → "09:30").
    
    Args:
        time_str: String de horário
    
    Returns:
        Horário normalizado em formato HH:MM
    """
    if not time_str or ":" not in time_str:
        return time_str
    
    try:
        hour, minute = time_str.split(":")
        return f"{int(hour):02d}:{int(minute):02d}"
    except (ValueError, AttributeError):
        return time_str


def normalize_date(date_str: str) -> Optional[str]:
    """
    Normaliza data de DD/MM/YYYY para YYYY-MM-DD (formato ISO para banco).
    
    Args:
        date_str: String de data em formato DD/MM/YYYY
    
    Returns:
        Data em formato ISO (YYYY-MM-DD) ou None se vazio
    """
    if not date_str or not date_str.strip():
        return None
    
    try:
        day, month, year = date_str.strip().split("/")
        return f"{year}-{month:0>2}-{day:0>2}"
    except (ValueError, AttributeError):
        return None
