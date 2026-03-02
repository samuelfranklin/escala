import calendar
import logging
import tkinter as tk
from collections import defaultdict
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

from sqlalchemy import func, text
from sqlalchemy.orm import joinedload

from infra.database import Event, EventSquad, Member, MemberSquad, Squad, session_scope

# Configure module-level logger to append to a debug file
logger = logging.getLogger("escala.gerar_escala")
if not logger.handlers:
    handler = logging.FileHandler("escala_debug.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class GerarEscalaFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.patentes = ["Líder", "Treinador", "Membro", "Recruta"]
        self.criar_widgets()

    def criar_widgets(self):
        periodo = ttk.LabelFrame(self, text="Período da Escala")
        periodo.pack(fill="x", padx=10, pady=5)

        ttk.Label(periodo, text="Mês:").grid(row=0, column=0, padx=5, pady=2)
        self.mes = ttk.Combobox(periodo, values=list(range(1, 13)), width=5)
        self.mes.set(datetime.now().month)
        self.mes.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(periodo, text="Ano:").grid(row=0, column=2, padx=5, pady=2)
        self.ano = ttk.Entry(periodo, width=6)
        self.ano.insert(0, str(datetime.now().year))
        self.ano.grid(row=0, column=3, padx=5, pady=2)

        opcoes = ttk.LabelFrame(self, text="Opções")
        opcoes.pack(fill="x", padx=10, pady=5)

        self.var_respeitar_casais = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            opcoes,
            text="Respeitar casais (escalar juntos)",
            variable=self.var_respeitar_casais,
        ).pack(anchor="w", padx=5, pady=2)

        self.var_equilibrio = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            opcoes,
            text="Distribuir equilíbrio (menos escalados primeiro)",
            variable=self.var_equilibrio,
        ).pack(anchor="w", padx=5, pady=2)

        ttk.Button(self, text="Gerar Escala", command=self.gerar).pack(pady=10)

    def gerar(self):
        try:
            mes = int(self.mes.get())
            ano = int(self.ano.get())
        except Exception:
            messagebox.showerror("Erro", "Mês/Ano inválidos.")
            return

        eventos = self.coletar_eventos(mes, ano)
        if not eventos:
            messagebox.showwarning("Aviso", "Nenhum evento encontrado neste mês.")
            return

        contagem = defaultdict(int)
        escala = []
        conflitos = []

        for ev in eventos:
            data = ev["data"]
            dia_semana = ev["dia_semana"]
            evento_nome = ev["nome"]
            horario = ev["horario"]

            for squad_nome, qtd_total in ev["quantidades"].items():
                if qtd_total == 0:
                    continue

                # Buscar todos os membros disponíveis para esta squad na data/horário
                disponiveis = self.buscar_disponiveis(
                    squad_nome, data, dia_semana, horario
                )

                # Processar casais
                if self.var_respeitar_casais.get():
                    disponiveis = self.processar_casais(disponiveis)

                # Selecionar membros de acordo com a quantidade e regras de patente
                selecionados = self.selecionar_membros(
                    squad_nome,
                    disponiveis,
                    qtd_total,
                    contagem,
                    self.var_equilibrio.get(),
                )

                if len(selecionados) < qtd_total:
                    conflitos.append(
                        f"{data} - {evento_nome} - {squad_nome}: precisa {qtd_total}, tem {len(selecionados)}"
                    )

                for membro in selecionados:
                    escala.append(
                        {
                            "data": data,
                            "dia": dia_semana,
                            "evento": evento_nome,
                            "horario": horario,
                            "squad": squad_nome,
                            "membro": membro,
                        }
                    )

        if conflitos:
            msg = "Conflitos encontrados:\n\n" + "\n".join(conflitos[:20])
            if len(conflitos) > 20:
                msg += f"\n... e mais {len(conflitos) - 20} conflitos."
            messagebox.showwarning("Conflitos", msg)
        else:
            messagebox.showinfo(
                "Sucesso", f"Escala gerada para {mes}/{ano} com sucesso!"
            )

        if hasattr(self.app, "frames") and "Visualizar" in self.app.frames:
            self.app.frames["Visualizar"].set_escala(escala)
        else:
            self.escala = escala

    def coletar_eventos(self, mes, ano):
        eventos_coletados = []
        dias_map = {
            "Monday": "Segunda",
            "Tuesday": "Terça",
            "Wednesday": "Quarta",
            "Thursday": "Quinta",
            "Friday": "Sexta",
            "Saturday": "Sábado",
            "Sunday": "Domingo",
        }
        dias_num = {
            "Segunda": 0,
            "Terça": 1,
            "Quarta": 2,
            "Quinta": 3,
            "Sexta": 4,
            "Sábado": 5,
            "Domingo": 6,
        }

        with session_scope() as session:
            # ── Buscar eventos via ORM ──
            try:
                events = session.query(Event).all()
            except Exception as e:
                logger.exception("Erro ao buscar eventos: %s", e)
                return []

            for event in events:
                # Campos do ORM: id, name, type, date, day_of_week, time
                if event.type == "fixo" and event.day_of_week:
                    num_dia = dias_num.get(event.day_of_week)
                    if num_dia is None:
                        logger.warning("Dia da semana inválido: %s", event.day_of_week)
                        continue
                    cal = calendar.monthcalendar(ano, mes)
                    for week in cal:
                        if week[num_dia] != 0:
                            dia = week[num_dia]
                            current_data_str = f"{dia:02d}/{mes:02d}/{ano}"
                            quantidades = self.get_quantidades(session, event.id)
                            if quantidades:
                                eventos_coletados.append(
                                    {
                                        "id": str(event.id),
                                        "nome": event.name,
                                        "data": current_data_str,
                                        "dia_semana": event.day_of_week,
                                        "horario": event.time or "19:00",
                                        "quantidades": quantidades,
                                    }
                                )
                elif event.type == "sazonal" and event.date:
                    # Para eventos sazonais, verificar se está no período do mês
                    try:
                        data_obj = datetime.strptime(event.date, "%Y-%m-%d")
                        if data_obj.month == mes and data_obj.year == ano:
                            dia_semana_eng = calendar.day_name[data_obj.weekday()]
                            dia_semana_pt = dias_map.get(dia_semana_eng, "")
                            quantidades = self.get_quantidades(session, event.id)
                            if quantidades:
                                data_str = event.date.replace("-", "/")[::-1].replace("/", "-")
                                # Converter YYYY-MM-DD para DD/MM/YYYY
                                data_str = "/".join(reversed(event.date.split("-")))
                                eventos_coletados.append(
                                    {
                                        "id": str(event.id),
                                        "nome": event.name,
                                        "data": data_str,
                                        "dia_semana": dia_semana_pt,
                                        "horario": event.time or "09:00",
                                        "quantidades": quantidades,
                                    }
                                )
                    except ValueError:
                        logger.warning(
                            "Data inválida para evento sazonal (ID: %s, Data: %s)",
                            event.id,
                            event.date,
                        )
                        continue
                elif event.type == "eventual" and event.date:
                    # Para eventos eventuais, verificar se está no período do mês
                    try:
                        data_obj = datetime.strptime(event.date, "%Y-%m-%d")
                        if data_obj.month == mes and data_obj.year == ano:
                            dia_semana_eng = calendar.day_name[data_obj.weekday()]
                            dia_semana_pt = dias_map.get(dia_semana_eng, "")
                            quantidades = self.get_quantidades(session, event.id)
                            if quantidades:
                                data_str = "/".join(reversed(event.date.split("-")))
                                eventos_coletados.append(
                                    {
                                        "id": str(event.id),
                                        "nome": event.name,
                                        "data": data_str,
                                        "dia_semana": dia_semana_pt,
                                        "horario": event.time or "08:00",
                                        "quantidades": quantidades,
                                    }
                                )
                    except ValueError:
                        logger.warning(
                            "Data inválida para evento eventual (ID: %s, Data: %s)",
                            event.id,
                            event.date,
                        )
                        continue

        eventos_coletados.sort(key=lambda x: datetime.strptime(x["data"], "%d/%m/%Y"))
        return eventos_coletados

    def get_quantidades(self, session, evento_id):  # Adicionado 'session'
        """Retorna dicionário: squad_nome -> quantidade_total"""
        quant = defaultdict(int)

        try:
            # Buscar Squads usando SQLAlchemy ORM
            squad_map = {s.id: s.nome for s in session.query(Squad).all()}

            # Buscar configurações de evento-squad via ORM (EventSquad)
            event_squad_configs = session.query(EventSquad).filter(
                EventSquad.event_id == evento_id,
                EventSquad.quantity > 0
            ).all()

            for config in event_squad_configs:
                squad_nome = squad_map.get(config.squad_id)
                if squad_nome:
                    quant[squad_nome] = config.quantity
        except Exception as e:
            logger.exception("get_quantidades error for evento_id=%s: %s", evento_id, e)

        return quant

    def buscar_disponiveis(self, squad_nome, data, dia_semana, horario_evento):
        """
        Retorna lista de nomes de membros que pertencem à squad e não têm restrições.
        OBS: Usa MemberRestrictions para validar bloqueios de data específica.
        """
        disponiveis = []
        with session_scope() as session:
            try:
                # Buscar o objeto Squad pelo nome usando SQLAlchemy ORM
                squad = session.query(Squad).filter(Squad.nome == squad_nome).first()
                if not squad:
                    logger.info("buscar_disponiveis: squad not found: %s", squad_nome)
                    return []

                logger.info(
                    "buscar_disponiveis: squad=%s (id=%s) date=%s",
                    squad_nome,
                    squad.id,
                    data,
                )

                # Buscar membros da squad usando SQLAlchemy ORM
                from infra.database import MemberRestrictions
                
                memberships = (
                    session.query(MemberSquad)
                    .options(joinedload(MemberSquad.member))
                    .filter(MemberSquad.squad_id == squad.id)
                    .all()
                )
                
                # Ordenar por nome após carregar da session
                memberships = sorted(memberships, key=lambda ms: ms.member.name if ms.member else "")

                membros_na_squad = []
                for ms in memberships:
                    if ms.member:  # Garante que o membro existe
                        membros_na_squad.append(
                            (ms.member.id, ms.member.name, ms.level)
                        )

                logger.info(
                    "buscar_disponiveis: membros_found=%d for squad_id=%s",
                    len(membros_na_squad),
                    squad.id,
                )

                # Converter data de string "DD/MM/YYYY" para objeto date
                try:
                    from datetime import datetime
                    data_parts = data.split("/")
                    data_obj = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0])).date()
                except Exception as e:
                    logger.warning("Erro ao converter data %s: %s", data, e)
                    data_obj = None

                for mid, mnome, patente in membros_na_squad:
                    # Verificar restrições (MemberRestrictions com data específica e descrição)
                    if data_obj:
                        restricao = (
                            session.query(MemberRestrictions)
                            .filter(
                                MemberRestrictions.member_id == mid,
                                MemberRestrictions.date == data_obj
                            )
                            .first()
                        )
                        if restricao:
                            logger.info(
                                "membro %s(%s) tem restrição em %s: %s", 
                                mnome, mid, data, restricao.description
                            )
                            continue

                    # Se passou em todas as checagens, incluir como disponível
                    disponiveis.append((mnome, patente))
                    logger.info("membro %s disponível para %s em %s", mnome, squad_nome, data)
                    
            except Exception as e:
                logger.exception("Erro em buscar_disponiveis: %s", e)

        return disponiveis

    def horario_compativel(self, horario_disponivel, horario_evento):
        try:
            disp_inicio, disp_fim = horario_disponivel.split("-")
            ev_inicio, ev_fim = horario_evento.split("-")

            def to_min(t):
                h, m = map(int, t.split(":"))
                return h * 60 + m

            return to_min(ev_inicio) >= to_min(disp_inicio) and to_min(
                ev_fim
            ) <= to_min(disp_fim)
        except Exception:
            # If any parsing error, be permissive (do not exclude)
            return True

    def processar_casais(self, disponiveis):
        """disponiveis é lista de (nome, patente). Retorna lista de strings (nomes ou "CASAL:...")"""
        if not disponiveis:
            return []

        conjuge = {}
        with session_scope() as session:
            try:
                from infra.database import FamilyCouple
                
                casais = session.query(FamilyCouple).all()

                for casal in casais:
                    if casal.member1 and casal.member2:
                        conjuge[casal.member1.name] = casal.member2.name
                        conjuge[casal.member2.name] = casal.member1.name
            except Exception as e:
                logger.exception("Erro ao recuperar casais: %s", e)
            # O bloco finally com conn.close() é removido

        # Construir dicionário de nome -> patente
        patente_dict = {nome: pat for nome, pat in disponiveis}
        nomes = [nome for nome, _ in disponiveis]

        usados = set()
        resultado = []
        for nome in nomes:
            if nome in usados:
                continue
            if (
                nome in conjuge
                and conjuge[nome] in patente_dict
                and conjuge[nome] not in usados
            ):
                # Casal completo disponível
                resultado.append(f"CASAL:{nome} & {conjuge[nome]}")
                usados.add(nome)
                usados.add(conjuge[nome])
            elif nome not in usados:
                resultado.append((nome, patente_dict[nome]))
                usados.add(nome)

        return resultado

    def selecionar_membros(
        self, squad_nome, disponiveis, quantidade, contagem, usar_equilibrio
    ):
        """
        disponiveis: lista de (nome, patente) ou strings "CASAL:..."
        Retorna lista de nomes (strings) dos membros selecionados, respeitando a regra de recrutas.
        Regra: Recrutas só podem ser escalados se houver pelo menos um Líder ou Treinador na mesma squad no mesmo evento.
        """
        if not disponiveis:
            return []

        # If disponiveis contains CASAL strings, expand pairs into tuples for selection logic.
        unidades = []
        for item in disponiveis:
            if isinstance(item, str) and item.startswith("CASAL:"):
                # Keep the CASAL marker as a single selectable unit; selection returns the string
                unidades.append(item)
            elif isinstance(item, tuple):
                unidades.append(item)
            else:
                # Unexpected format: skip
                continue

        # Delegate to internal selection implementation which expects tuple list for individuals
        # and strings for casais
        return self._selecionar_com_regras(
            squad_nome, unidades, quantidade, contagem, usar_equilibrio
        )

    def _selecionar_com_regras(
        self, squad_nome, disponiveis, quantidade, contagem, usar_equilibrio
    ):
        """
        disponiveis: lista contendo elementos do tipo:
            - tuple: (nome, patente)
            - string: "CASAL:nome1 & nome2"
        """
        if not disponiveis:
            return []

        # Expand disponiveis into structures for selection:
        casais = [
            d for d in disponiveis if isinstance(d, str) and d.startswith("CASAL:")
        ]
        individuos = [d for d in disponiveis if isinstance(d, tuple)]

        # Count of leaders/treinadores available among all units (including inside casal not expanded here)
        # To handle casais' patentes accurately we'd need to query DB; for simplicity, prioritize individuals by patente
        lideres = [d for d in individuos if d[1] in ["Líder", "Treinador"]]
        membros = [d for d in individuos if d[1] == "Membro"]
        recrutas = [d for d in individuos if d[1] == "Recruta"]

        # Optionally order by contagem (less assigned first)
        if usar_equilibrio:
            lideres.sort(key=lambda x: contagem[x[0]])
            membros.sort(key=lambda x: contagem[x[0]])
            recrutas.sort(key=lambda x: contagem[x[0]])
            # casais are left as-is (no per-person contagem available here), could be enhanced later

        selecionados_units = []

        # First pick leaders/treinadores
        while self._count_people_in_units(selecionados_units) < quantidade and lideres:
            selecionados_units.append(lideres.pop(0))

        # Then members
        while self._count_people_in_units(selecionados_units) < quantidade and membros:
            selecionados_units.append(membros.pop(0))

        # Consider casais as units; try to add them if still needed (each casal counts as 2 people)
        # Only add casais if adding them won't exceed the desired quantity too much (we allow slight overfill if necessary)
        for casal in casais:
            if self._count_people_in_units(selecionados_units) >= quantidade:
                break
            # Adding casal counts as 2; only add if at least one slot remains (we may allow adding casal if exactly 1 slot left,
            # to preserve couple together - business rule can be adjusted)
            if (
                self._count_people_in_units(selecionados_units) + 2 <= quantidade
                or self._count_people_in_units(selecionados_units) < quantidade
            ):
                selecionados_units.append(casal)

        # Now, if still need people, allow recrutas but only if a leader/treinador is already selected among units
        has_leader = any(
            (isinstance(u, tuple) and u[1] in ["Líder", "Treinador"])
            for u in selecionados_units
        )
        # Note: we are not inspecting patentes inside casais here. This can be improved by expanding casal composition earlier.

        if has_leader:
            while (
                self._count_people_in_units(selecionados_units) < quantidade
                and recrutas
            ):
                selecionados_units.append(recrutas.pop(0))
        else:
            # If there's no leader and no way to add one, we shouldn't add recrutas
            pass

        # Convert selected units to output strings: tuples -> name, casais stay as string
        result = []
        for unit in selecionados_units:
            if isinstance(unit, tuple):
                result.append(unit[0])
            else:
                # casal string
                result.append(unit)

        return result

    @staticmethod
    def _count_people_in_units(units):
        """Helper: count how many people are represented by selected units.
        - tuple: 1 person
        - casal string: 2 people
        """
        count = 0
        for u in units:
            if isinstance(u, tuple):
                count += 1
            elif isinstance(u, str) and u.startswith("CASAL:"):
                count += 2
        return count
