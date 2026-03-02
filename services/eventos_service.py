"""
Serviço de EVENTOS - Orquestra helpers + banco de dados.

Este serviço implementa as funcionalidades de gerenciamento de eventos,
chamando helpers para validação e usando session_scope() para persistência.

Padrão:
1. Validar entrada com helpers (sem BD)
2. Buscar dados existentes no BD se necessário
3. Executar lógica
4. Persistir mudanças
5. Retornar resultado

Não contém lógica de negócio - apenas orquestra.
"""

from typing import Optional
from sqlalchemy.exc import IntegrityError

from infra.database import Event, EventSquad, Squad, session_scope
from helpers.eventos import (
    validate_event_name,
    validate_event_type,
    validate_day_of_week,
    validate_date,
    validate_time,
    validate_event_squads,
    normalize_event_name,
    normalize_time,
    normalize_date,
)


class EventosService:
    """Serviço de gerenciamento de eventos."""

    def create_event(
        self,
        name: str,
        event_type: str,
        time: str,
        day_of_week: Optional[str] = None,
        date: Optional[str] = None,
        details: Optional[str] = None,
        squad_quantities: Optional[dict] = None,
    ) -> tuple[bool, str, Optional[Event]]:
        """
        Cria um novo evento.
        
        Args:
            name: Nome do evento
            event_type: Tipo ("fixo", "sazonal", "eventual")
            time: Horário em formato HH:MM
            day_of_week: Dia da semana (apenas para tipo "fixo")
            date: Data em formato DD/MM/YYYY (para tipo "sazonal"/"eventual")
            details: Descrição/detalhes do evento
            squad_quantities: Dict {squad_id: quantity} para evento
        
        Returns:
            (success: bool, message: str, event: Event or None)
        """
        # Validar nome
        with session_scope() as session:
            existing_names = [e.name for e in session.query(Event.name).all()]
        
        is_valid, msg = validate_event_name(name, existing_names)
        if not is_valid:
            return False, msg, None
        
        # Validar tipo
        is_valid, msg = validate_event_type(event_type)
        if not is_valid:
            return False, msg, None
        
        # Validar horário
        is_valid, msg = validate_time(time)
        if not is_valid:
            return False, msg, None
        
        # Validações específicas do tipo
        if event_type == "fixo":
            if not day_of_week:
                return False, "Dia da semana é obrigatório para evento fixo.", None
            is_valid, msg = validate_day_of_week(day_of_week)
            if not is_valid:
                return False, msg, None
            date = None
        
        elif event_type in ["sazonal", "eventual"]:
            if not date:
                return False, f"Data é obrigatória para evento {event_type}.", None
            is_valid, msg = validate_date(date)
            if not is_valid:
                return False, msg, None
            date = normalize_date(date)
            day_of_week = None
        
        # Validar squads se fornecidos
        if squad_quantities is None:
            squad_quantities = {}
        
        is_valid, msg = validate_event_squads(squad_quantities)
        if not is_valid:
            return False, msg, None
        
        # Normalizar entradas
        name = normalize_event_name(name)
        time = normalize_time(time)
        
        # Persistir
        try:
            with session_scope() as session:
                event = Event(
                    name=name,
                    type=event_type,
                    date=date,
                    day_of_week=day_of_week,
                    time=time,
                    details=details or "",
                )
                session.add(event)
                session.flush()
                
                # Se squad_quantities vazio, criar com defaults para todas as squads
                if not squad_quantities:
                    squads = session.query(Squad).all()
                    for squad in squads:
                        session.add(
                            EventSquad(
                                event_id=event.id,
                                squad_id=squad.id,
                                quantity=0,
                                level=2,
                            )
                        )
                else:
                    for squad_id, quantity in squad_quantities.items():
                        session.add(
                            EventSquad(
                                event_id=event.id,
                                squad_id=squad_id,
                                quantity=quantity,
                                level=2,
                            )
                        )
                
                session.commit()
                return True, f"Evento '{name}' criado com sucesso.", event
        
        except IntegrityError as e:
            return False, f"Erro ao criar evento: {str(e)}", None
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}", None

    def update_event(
        self,
        event_id: str,
        name: Optional[str] = None,
        event_type: Optional[str] = None,
        time: Optional[str] = None,
        day_of_week: Optional[str] = None,
        date: Optional[str] = None,
        details: Optional[str] = None,
    ) -> tuple[bool, str, Optional[Event]]:
        """
        Atualiza um evento existente.
        
        Args:
            event_id: ID do evento a atualizar
            Demais args: campos a atualizar (None = não altera)
        
        Returns:
            (success: bool, message: str, updated_event: Event or None)
        """
        try:
            with session_scope() as session:
                event = session.query(Event).filter(Event.id == event_id).first()
                if not event:
                    return False, f"Evento com ID '{event_id}' não encontrado.", None
                
                # Validar novo nome se fornecido
                if name is not None:
                    existing_names = [
                        e.name
                        for e in session.query(Event.name).filter(Event.id != event_id).all()
                    ]
                    is_valid, msg = validate_event_name(name, existing_names)
                    if not is_valid:
                        return False, msg, None
                    event.name = normalize_event_name(name)
                
                # Validar novo tipo se fornecido
                if event_type is not None:
                    is_valid, msg = validate_event_type(event_type)
                    if not is_valid:
                        return False, msg, None
                    event.type = event_type
                
                # Validar novo horário se fornecido
                if time is not None:
                    is_valid, msg = validate_time(time)
                    if not is_valid:
                        return False, msg, None
                    event.time = normalize_time(time)
                
                # Validar dia/data conforme tipo
                if event_type == "fixo" or (event_type is None and event.type == "fixo"):
                    if day_of_week is not None:
                        is_valid, msg = validate_day_of_week(day_of_week)
                        if not is_valid:
                            return False, msg, None
                        event.day_of_week = day_of_week
                    event.date = None
                
                elif event_type in ["sazonal", "eventual"] or (
                    event_type is None and event.type in ["sazonal", "eventual"]
                ):
                    if date is not None:
                        is_valid, msg = validate_date(date)
                        if not is_valid:
                            return False, msg, None
                        event.date = normalize_date(date)
                    event.day_of_week = None
                
                # Atualizar detalhes se fornecido
                if details is not None:
                    event.details = details
                
                session.commit()
                return True, f"Evento '{event.name}' atualizado com sucesso.", event
        
        except Exception as e:
            return False, f"Erro ao atualizar evento: {str(e)}", None

    def delete_event(self, event_id: str) -> tuple[bool, str]:
        """
        Deleta um evento (cascata remove EventSquad também).
        
        Args:
            event_id: ID do evento a deletar
        
        Returns:
            (success: bool, message: str)
        """
        try:
            with session_scope() as session:
                event = session.query(Event).filter(Event.id == event_id).first()
                if not event:
                    return False, f"Evento com ID '{event_id}' não encontrado."
                
                event_name = event.name
                session.delete(event)
                session.commit()
                return True, f"Evento '{event_name}' deletado com sucesso."
        
        except Exception as e:
            return False, f"Erro ao deletar evento: {str(e)}"

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Busca um evento por ID.
        
        Args:
            event_id: ID do evento
        
        Returns:
            Event ou None se não encontrado
        """
        try:
            with session_scope() as session:
                event = session.query(Event).filter(Event.id == event_id).first()
                return event
        except Exception:
            return None

    def list_all_events(self) -> list[Event]:
        """
        Lista todos os eventos ordenados por nome.
        
        Returns:
            Lista de Event
        """
        try:
            with session_scope() as session:
                events = session.query(Event).order_by(Event.name).all()
                return events
        except Exception:
            return []

    def configure_event_squads(
        self, event_id: str, squad_quantities: dict
    ) -> tuple[bool, str]:
        """
        Configura as squads necessárias para um evento.
        
        Args:
            event_id: ID do evento
            squad_quantities: Dict {squad_id: quantity}
        
        Returns:
            (success: bool, message: str)
        """
        is_valid, msg = validate_event_squads(squad_quantities)
        if not is_valid:
            return False, msg
        
        try:
            with session_scope() as session:
                event = session.query(Event).filter(Event.id == event_id).first()
                if not event:
                    return False, f"Evento com ID '{event_id}' não encontrado."
                
                # Deletar configurações antigas
                session.query(EventSquad).filter(EventSquad.event_id == event_id).delete()
                
                # Criar novas configurações
                for squad_id, quantity in squad_quantities.items():
                    # Validar que squad existe
                    squad = session.query(Squad).filter(Squad.id == squad_id).first()
                    if not squad:
                        return False, f"Squad com ID '{squad_id}' não encontrada."
                    
                    session.add(
                        EventSquad(
                            event_id=event_id,
                            squad_id=squad_id,
                            quantity=quantity,
                            level=2,
                        )
                    )
                
                session.commit()
                return True, "Configuração de squads atualizada com sucesso."
        
        except Exception as e:
            return False, f"Erro ao configurar squads: {str(e)}"


# Singleton conveniente
_service_instance = None


def get_eventos_service() -> EventosService:
    """Padrão Singleton para o serviço."""
    global _service_instance
    if _service_instance is None:
        _service_instance = EventosService()
    return _service_instance
