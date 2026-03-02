"""
Service para gerador de escala.

Orquestra:
- Helpers (puro, sem BD)
- Acesso a BD via SQLAlchemy + session_scope
- Logging apropriado
- Interface clara para GUI ou CLI

Padrão de retorno:
    (sucesso: bool, mensagem: str, escala: list[dict])
"""

import calendar
import logging
from collections import defaultdict
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.orm import joinedload

from infra.database import (
    session_scope,
    Event,
    Squad,
    Member,
    EventSquad,
    MemberSquad,
    MemberRestrictions,
    FamilyCouple,
)
from helpers.escala_generator import (
    is_valid_month,
    format_date_string,
    parse_date_string,
    process_couples,
    apply_balance_distribution,
    can_add_trainee_with_leader,
    format_schedule_entry,
    select_members_by_patron,
    count_people_in_selection,
    get_patron_rank,
)

logger = logging.getLogger(__name__)


class EscalaService:
    """Serviço para geração de escala mensal."""

    def __init__(self):
        """Inicializa service com configurações padrão."""
        self.dias_map = {
            "Monday": "Segunda",
            "Tuesday": "Terça",
            "Wednesday": "Quarta",
            "Thursday": "Quinta",
            "Friday": "Sexta",
            "Saturday": "Sábado",
            "Sunday": "Domingo",
        }
        self.dias_num = {
            "Segunda": 0,
            "Terça": 1,
            "Quarta": 2,
            "Quinta": 3,
            "Sexta": 4,
            "Sábado": 5,
            "Domingo": 6,
        }

    def generate_schedule(
        self,
        month: int,
        year: int,
        respect_couples: bool = True,
        balance_distribution: bool = True,
    ) -> Tuple[bool, str, List[Dict[str, str]]]:
        """
        Gera escala para mês/ano.
        
        Args:
            month: Mês (1-12)
            year: Ano (positivo)
            respect_couples: Se True, escalá casais juntos
            balance_distribution: Se True, ordena por menos escalados
        
        Returns:
            (sucesso, mensagem, escala)
            - sucesso: bool
            - mensagem: str com erros, avisos ou sucesso
            - escala: list[dict] com entradas formatadas
        """
        # 1. Validar entrada
        valid, msg = is_valid_month(month, year)
        if not valid:
            return False, msg, []

        try:
            # 2. Coletar eventos do mês
            eventos = self._collect_events(int(month), int(year))
            
            if not eventos:
                return False, f"Nenhum evento encontrado para {month}/{year}", []
            
            logger.info(f"Coletados {len(eventos)} eventos para {month}/{year}")

            # 3. Gerar escala
            escala, conflitos = self._generate_schedule_entries(
                eventos,
                respect_couples,
                balance_distribution,
            )

            # 4. Retornar resultado
            if conflitos:
                msg = "Conflitos encontrados:\n" + "\n".join(conflitos[:20])
                if len(conflitos) > 20:
                    msg += f"\n... e mais {len(conflitos) - 20} conflitos."
                logger.warning(f"Escala gerada com {len(conflitos)} conflitos")
                return True, msg, escala
            else:
                msg = f"Escala gerada com sucesso para {month}/{year}"
                logger.info(msg)
                return True, msg, escala

        except Exception as e:
            logger.exception(f"Erro ao gerar escala: {e}")
            return False, f"Erro: {str(e)}", []

    def _collect_events(self, month: int, year: int) -> List[Dict[str, Any]]:
        """
        Coleta eventos do mês/ano do banco de dados.
        
        Retorna eventos fixos (gera datas), sazonais e eventuais.
        
        Returns:
            Lista de dicts: {id, nome, data, dia_semana, horario, quantidades}
        """
        eventos_coletados = []

        with session_scope() as session:
            try:
                events = session.query(Event).all()
                logger.debug(f"Encontrados {len(events)} eventos no BD")

                for event in events:
                    # Eventos FIXOS: gerar datas com base no dia da semana
                    if event.type == "fixo" and event.day_of_week:
                        self._process_fixed_event(
                            session, event, month, year, eventos_coletados
                        )
                    
                    # Eventos SAZONAIS e EVENTUAIS: usar data única
                    elif event.type in ("sazonal", "eventual") and event.date:
                        self._process_date_based_event(
                            session, event, month, year, eventos_coletados
                        )

                # Ordenar por data
                eventos_coletados.sort(
                    key=lambda e: datetime.strptime(e["data"], "%d/%m/%Y")
                )

            except Exception as e:
                logger.exception(f"Erro ao coletar eventos: {e}")

        return eventos_coletados

    def _process_fixed_event(
        self,
        session,
        event,
        month: int,
        year: int,
        eventos_list: List[Dict],
    ) -> None:
        """
        Processa evento fixo: gera entradas para cada ocorrência no mês.
        
        Args:
            session: SQLAlchemy session
            event: Event object
            month: Mês-alvo
            year: Ano-alvo
            eventos_list: Lista a ser preenchida (modificada in-place)
        """
        num_dia = self.dias_num.get(event.day_of_week)
        if num_dia is None:
            logger.warning(f"Dia da semana inválido: {event.day_of_week}")
            return

        cal = calendar.monthcalendar(year, month)
        for week in cal:
            if week[num_dia] != 0:
                dia = week[num_dia]
                data_str = format_date_string(dia, month, year)
                quantidades = self._get_quantities(session, event.id)

                if quantidades:
                    eventos_list.append({
                        "id": str(event.id),
                        "nome": event.name,
                        "data": data_str,
                        "dia_semana": event.day_of_week,
                        "horario": event.time or "19:00",
                        "quantidades": quantidades,
                    })

    def _process_date_based_event(
        self,
        session,
        event,
        month: int,
        year: int,
        eventos_list: List[Dict],
    ) -> None:
        """
        Processa evento com data específica (sazonal ou eventual).
        
        Args:
            session: SQLAlchemy session
            event: Event object
            month: Mês-alvo
            year: Ano-alvo
            eventos_list: Lista a ser preenchida
        """
        try:
            data_obj = datetime.strptime(event.date, "%Y-%m-%d").date()
            
            if data_obj.month == month and data_obj.year == year:
                dia_semana_eng = calendar.day_name[data_obj.weekday()]
                dia_semana_pt = self.dias_map.get(dia_semana_eng, "")

                quantidades = self._get_quantities(session, event.id)
                if quantidades and dia_semana_pt:
                    data_str = format_date_string(
                        data_obj.day, data_obj.month, data_obj.year
                    )
                    eventos_list.append({
                        "id": str(event.id),
                        "nome": event.name,
                        "data": data_str,
                        "dia_semana": dia_semana_pt,
                        "horario": event.time or "09:00",
                        "quantidades": quantidades,
                    })

        except ValueError as e:
            logger.warning(f"Data inválida para evento {event.id}: {event.date} - {e}")

    def _get_quantities(self, session, event_id: str) -> Dict[str, int]:
        """
        Retorna {squad_nome: quantidade} para evento.
        
        Args:
            session: SQLAlchemy session
            event_id: ID do evento
        
        Returns:
            Dict {squad_nome: quantidade}
        """
        quantities = defaultdict(int)

        try:
            squad_map = {s.id: s.nome for s in session.query(Squad).all()}

            configs = session.query(EventSquad).filter(
                EventSquad.event_id == event_id,
                EventSquad.quantity > 0,
            ).all()

            for config in configs:
                squad_nome = squad_map.get(config.squad_id)
                if squad_nome:
                    quantities[squad_nome] = config.quantity

        except Exception as e:
            logger.exception(f"Erro em get_quantities para evento {event_id}: {e}")

        return dict(quantities)

    def _generate_schedule_entries(
        self,
        eventos: List[Dict],
        respect_couples: bool,
        balance_distribution: bool,
    ) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Gera entradas de escala para todos os eventos.
        
        Returns:
            (escala, conflitos)
            - escala: list[dict] com entradas formatadas
            - conflitos: list[str] com mensagens de conflito
        """
        escala = []
        conflitos = []
        contagem = defaultdict(int)  # {membro_nome: quantidade_escalada}

        for evento in eventos:
            data = evento["data"]
            dia_semana = evento["dia_semana"]
            evento_nome = evento["nome"]
            horario = evento["horario"]

            for squad_nome, qtd_total in evento["quantidades"].items():
                if qtd_total == 0:
                    continue

                # Buscar membros disponíveis
                disponiveis = self._get_available_members(
                    squad_nome, data, dia_semana, horario
                )

                if not disponiveis:
                    conflitos.append(
                        f"{data} - {evento_nome} - {squad_nome}: nenhum membro disponível"
                    )
                    continue

                # Processar casais
                if respect_couples:
                    disponiveis = self._process_couples_from_db(disponiveis)

                # Selecionar membros
                selecionados = self._select_members(
                    disponiveis,
                    qtd_total,
                    contagem,
                    balance_distribution,
                )

                # Registrar conflito se insuficiente
                if len(selecionados) < qtd_total:
                    conflitos.append(
                        f"{data} - {evento_nome} - {squad_nome}: "
                        f"precisa {qtd_total}, selecionados {len(selecionados)}"
                    )

                # Adicionar à escala
                for membro_nome in selecionados:
                    if membro_nome.startswith("CASAL:"):
                        # Expandir casal em duas entradas
                        membros_casal = [
                            m.strip() for m in membro_nome.replace("CASAL:", "").split("&")
                        ]
                        for membro in membros_casal:
                            escala.append(
                                format_schedule_entry(
                                    evento_nome, data, dia_semana, horario, squad_nome, membro
                                )
                            )
                            contagem[membro] += 1
                    else:
                        escala.append(
                            format_schedule_entry(
                                evento_nome, data, dia_semana, horario, squad_nome, membro_nome
                            )
                        )
                        contagem[membro_nome] += 1

        return escala, conflitos

    def _get_available_members(
        self,
        squad_nome: str,
        data: str,
        dia_semana: str,
        horario_evento: str,
    ) -> List[Tuple[str, str]]:
        """
        Retorna [(nome, patente), ...] de membros disponíveis para squad/data.
        
        Verifica:
        - Pertence à squad
        - Sem restrições para a data
        
        Args:
            squad_nome: Nome da squad
            data: Data em formato 'DD/MM/YYYY'
            dia_semana: Dia da semana (ignorado por enquanto)
            horario_evento: Horário do evento
        
        Returns:
            Lista de (nome, patente)
        """
        disponiveis = []

        with session_scope() as session:
            try:
                # Buscar squad
                squad = session.query(Squad).filter(
                    Squad.nome == squad_nome
                ).first()

                if not squad:
                    logger.debug(f"Squad não encontrada: {squad_nome}")
                    return []

                # Buscar membros da squad
                memberships = (
                    session.query(MemberSquad)
                    .options(joinedload(MemberSquad.member))
                    .filter(MemberSquad.squad_id == squad.id)
                    .all()
                )

                memberships = sorted(
                    memberships, key=lambda ms: (ms.member.name if ms.member else "")
                )

                # Parse data
                parsed = parse_date_string(data)
                if parsed:
                    data_obj = date(parsed[2], parsed[1], parsed[0])
                else:
                    logger.warning(f"Data inválida: {data}")
                    data_obj = None

                # Verificar cada membro
                for ms in memberships:
                    if not ms.member:
                        continue

                    membro_id = ms.member.id
                    membro_nome = ms.member.name
                    patente = self._get_member_patron(session, membro_id, squad.id)

                    # Verificar restrições
                    if data_obj:
                        restricao = (
                            session.query(MemberRestrictions)
                            .filter(
                                MemberRestrictions.member_id == membro_id,
                                MemberRestrictions.date == data_obj,
                            )
                            .first()
                        )
                        if restricao:
                            logger.debug(
                                f"Membro {membro_nome} tem restrição em {data}: "
                                f"{restricao.description}"
                            )
                            continue

                    disponiveis.append((membro_nome, patente))

            except Exception as e:
                logger.exception(f"Erro em get_available_members: {e}")

        return disponiveis

    def _get_member_patron(self, session, member_id: str, squad_id: str) -> str:
        """
        Retorna patente do membro na squad.
        
        Usa MemberSquad.level para mapear para nome de patente.
        """
        try:
            ms = session.query(MemberSquad).filter(
                MemberSquad.member_id == member_id,
                MemberSquad.squad_id == squad_id,
            ).first()

            if ms:
                level_map = {1: "Recruta", 2: "Membro", 3: "Treinador", 4: "Líder"}
                return level_map.get(ms.level, "Membro")
        except Exception as e:
            logger.debug(f"Erro ao recuperar patente: {e}")

        return "Membro"  # Default

    def _process_couples_from_db(
        self,
        available_members: List[Tuple[str, str]],
    ) -> List[Tuple[str, str]]:
        """
        Processa casais usando dados do BD.
        
        Args:
            available_members: Lista de (nome, patente)
        
        Returns:
            Lista filtrada respeitando casais
        """
        couples_map = {}

        with session_scope() as session:
            try:
                casais = session.query(FamilyCouple).all()
                for casal in casais:
                    if casal.member1 and casal.member2:
                        couples_map[casal.member1.name] = casal.member2.name
                        couples_map[casal.member2.name] = casal.member1.name
            except Exception as e:
                logger.exception(f"Erro ao recuperar casais: {e}")

        return process_couples(available_members, couples_map)

    def _select_members(
        self,
        disponiveis: List[Tuple[str, str]],
        quantidade: int,
        contagem: Dict[str, int],
        usar_equilibrio: bool,
    ) -> List[str]:
        """
        Seleciona membros respeitando:
        - Patente (Líder > Treinador > Membro > Recruta)
        - Equilíbrio (menos escalados primeiro)
        - Regra de recruta (só com Líder/Treinador)
        
        Args:
            disponiveis: Lista de (nome, patente)
            quantidade: Quantos membros precisam
            contagem: {nome: vezes_escalado}
            usar_equilibrio: Se aplica equilíbrio
        
        Returns:
            Lista de nomes selecionados
        """
        if not disponiveis or quantidade <= 0:
            return []

        # Ordenar por patente
        disponiveis = select_members_by_patron(disponiveis)

        # Separar por patente
        lideres = [m for m in disponiveis if m[1] in ("Líder", "Treinador")]
        membros = [m for m in disponiveis if m[1] == "Membro"]
        recrutas = [m for m in disponiveis if m[1] == "Recruta"]

        # Aplicar equilíbrio
        if usar_equilibrio:
            lideres.sort(key=lambda x: contagem.get(x[0], 0))
            membros.sort(key=lambda x: contagem.get(x[0], 0))
            recrutas.sort(key=lambda x: contagem.get(x[0], 0))

        selecionados = []

        # Selecionar líderes/treinadores
        while len(selecionados) < quantidade and lideres:
            selecionados.append(lideres.pop(0)[0])

        # Selecionar membros
        while len(selecionados) < quantidade and membros:
            selecionados.append(membros.pop(0)[0])

        # Selecionar recrutas (só se há líder)
        if can_add_trainee_with_leader(
            [(nome, "X") for nome in selecionados if nome in [l[0] for l in lideres]]
        ) or any(
            nome in [l[0] for l in disponiveis if l[1] in ("Líder", "Treinador")]
            for nome in selecionados
        ):
            while len(selecionados) < quantidade and recrutas:
                selecionados.append(recrutas.pop(0)[0])

        return selecionados
