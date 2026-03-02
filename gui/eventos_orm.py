# gui/eventos_orm.py - Versão ORM de Eventos
import tkinter as tk
from tkinter import messagebox, ttk

from sqlalchemy.exc import IntegrityError

from infra.database import Event, EventSquad, Squad, session_scope
from utils import EventoDialog, center_popup

# ── Paleta (espelha main_window.py) ──────────────────────────────────
_BG = "#1e2533"
_BG_HDR = "#151b27"
_BG_CARD = "#ffffff"
_BG_CONT = "#f0f2f7"
_ACCENT = "#4f7ef8"
_ACCENT_DK = "#3d6ae0"
_FG_MUTED = "#a8b2c8"
_FG_DARK = "#2c3a52"
_FG_WHITE = "#ffffff"
_SEP = "#2e3650"
_BTN_HOVER = "#2a3347"
_ROW_ALT = "#f4f6fb"
_HDR_COL = "#e8ecf5"


class EventosFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_styles()
        self._build_ui()
        self.atualizar_lista()

    def _setup_styles(self) -> None:
        s = ttk.Style()
        s.configure("Eventos.Treeview",
                    background=_BG_CARD,
                    fieldbackground=_BG_CARD,
                    foreground=_FG_DARK,
                    rowheight=32,
                    font=("Segoe UI", 10),
                    borderwidth=0)
        s.configure("Eventos.Treeview.Heading",
                    background=_HDR_COL,
                    foreground=_FG_DARK,
                    font=("Segoe UI", 9, "bold"),
                    relief="flat",
                    padding=(10, 7))
        s.map("Eventos.Treeview",
              background=[("selected", "#dde4f8")],
              foreground=[("selected", _FG_DARK)])

    def _build_ui(self) -> None:
        # Header
        hdr = tk.Frame(self, bg=_BG, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr,
                 text="📅  Eventos",
                 font=("Segoe UI", 11, "bold"),
                 bg=_BG,
                 fg=_FG_WHITE,
                 padx=14).pack(side="left", fill="y")

        self._lbl_count = tk.Label(hdr,
                                    text="",
                                    font=("Segoe UI", 9),
                                    bg=_BG,
                                    fg=_FG_MUTED,
                                    padx=4)
        self._lbl_count.pack(side="left", fill="y")

        tk.Button(hdr,
                  text="↻",
                  command=self.atualizar_lista,
                  bg=_BG,
                  fg=_FG_MUTED,
                  activebackground=_BTN_HOVER,
                  activeforeground=_FG_WHITE,
                  relief="flat",
                  bd=0,
                  padx=8,
                  font=("Segoe UI", 13),
                  cursor="hand2").pack(side="right", padx=(2, 8), fill="y")

        for text, cmd, bg_n, bg_h in [
            ("✕", self.remover, _BTN_HOVER, _BG),
            ("✎", self.editar, _BTN_HOVER, _BG),
            ("＋", self.adicionar, _ACCENT, _ACCENT_DK),
        ]:
            tk.Button(hdr,
                      text=text,
                      command=cmd,
                      bg=bg_n,
                      fg=_FG_WHITE,
                      activebackground=bg_h,
                      activeforeground=_FG_WHITE,
                      relief="flat",
                      bd=0,
                      padx=10,
                      font=("Segoe UI", 10),
                      cursor="hand2").pack(side="right", padx=2, fill="y", pady=8)

        # Treeview
        tree_wrap = tk.Frame(self, bg=_BG_CARD)
        tree_wrap.pack(fill="both", expand=True)

        cols = ("Nome", "Tipo", "Data/Dia", "Horário")
        self.tree = ttk.Treeview(tree_wrap,
                                  columns=cols,
                                  show="headings",
                                  style="Eventos.Treeview",
                                  selectmode="browse")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Data/Dia", text="Data/Dia")
        self.tree.heading("Horário", text="Horário")
        self.tree.column("Nome", width=250, minwidth=100, stretch=False)
        self.tree.column("Tipo", width=100, minwidth=80, stretch=False)
        self.tree.column("Data/Dia", width=150, minwidth=80, stretch=False)
        self.tree.column("Horário", width=100, minwidth=60, stretch=True)

        self.tree.tag_configure("odd", background=_BG_CARD)
        self.tree.tag_configure("even", background=_ROW_ALT)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def atualizar_lista(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        with session_scope() as session:
            events = session.query(Event).order_by(Event.name).all()

            self._evento_data = {}
            for idx, event in enumerate(events):
                tag = "odd" if idx % 2 == 0 else "even"
                data_dia = event.day_of_week if event.type == "fixo" else (event.date or "")
                self.tree.insert("", "end",
                                iid=event.id,
                                values=(event.name, event.type.capitalize(), data_dia, event.time or ""),
                                tags=(tag,))
                self._evento_data[event.id] = (event.name, event.type, data_dia, event.time)

        total = len(self.tree.get_children())
        self._lbl_count.config(text=f"({total} evento{'s' if total != 1 else ''})")

    def adicionar(self) -> None:
        dlg = EventoDialog(self, "Novo Evento")
        center_popup(dlg.dialog)
        if not dlg.result:
            return

        nome, tipo, dia, data, horario, desc = dlg.result
        try:
            with session_scope() as session:
                event = Event(name=nome,
                             type=tipo,
                             date=data if tipo != "fixo" else None,
                             day_of_week=dia if tipo == "fixo" else None,
                             time=horario,
                             details=desc)
                session.add(event)
                session.flush()

                # Criar configurações padrão para todas as squads
                squads = session.query(Squad).all()
                for squad in squads:
                    session.add(EventSquad(event_id=event.id,
                                          squad_id=squad.id,
                                          quantity=0,
                                          level=2))
        except IntegrityError:
            messagebox.showerror("Erro", "Erro ao adicionar evento.")
            return

        messagebox.showinfo("Sucesso", f"Evento '{nome}' adicionado.")
        self.atualizar_lista()

    def editar(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um evento.")
            return

        event_id = sel[0]
        with session_scope() as session:
            event = session.query(Event).filter(Event.id == event_id).first()
            if not event:
                messagebox.showwarning("Aviso", "Evento não encontrado.")
                return

            dlg = EventoDialog(self,
                             "Editar Evento",
                             nome=event.name,
                             tipo=event.type,
                             dia=event.day_of_week or "Domingo",
                             data=event.date or "",
                             horario=event.time or "",
                             descricao=event.details or "")
            center_popup(dlg.dialog)
            if not dlg.result:
                return

            novo_nome, novo_tipo, novo_dia, nova_data, novo_horario, nova_desc = dlg.result
            event.name = novo_nome
            event.type = novo_tipo
            event.date = nova_data if novo_tipo != "fixo" else None
            event.day_of_week = novo_dia if novo_tipo == "fixo" else None
            event.time = novo_horario
            event.details = nova_desc

        messagebox.showinfo("Sucesso", "Evento atualizado.")
        self.atualizar_lista()

    def remover(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return

        event_id = sel[0]
        nome = self.tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", f"Remover evento '{nome}'?"):
            return

        with session_scope() as session:
            event = session.query(Event).filter(Event.id == event_id).first()
            if event:
                session.delete(event)

        messagebox.showinfo("Sucesso", "Evento removido.")
        self.atualizar_lista()
