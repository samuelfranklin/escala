# gui/squads.py
import tkinter as tk
from tkinter import messagebox, ttk

from sqlalchemy.exc import IntegrityError

from infra.database import Member, MemberSquad, Squad, session_scope
from utils import SquadDialog

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

# Cores para linhas "matriculado"
_ENROLL_BG = "#e8f0fe"
_ENROLL_BG_ALT = "#dde7fd"

_PATENTE_TO_LEVEL = {"Líder": 4, "Treinador": 3, "Membro": 2, "Recruta": 1}
_LEVEL_TO_PATENTE = {v: k for k, v in _PATENTE_TO_LEVEL.items()}


class SquadsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.patentes = ["Líder", "Treinador", "Membro", "Recruta"]
        self.membros_widgets: dict[str, tuple[tk.BooleanVar, tk.StringVar]] = {}
        self._squad_selecionado: str | None = None
        self._setup_styles()
        self._build_ui()
        self.atualizar_lista()

    def _setup_styles(self) -> None:
        s = ttk.Style()
        s.configure("SContent.TFrame", background=_BG_CONT)
        s.configure("SCard.TFrame", background=_BG_CARD)

        s.configure(
            "Squads.Treeview",
            background=_BG_CARD,
            fieldbackground=_BG_CARD,
            foreground=_FG_DARK,
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        s.configure(
            "Squads.Treeview.Heading",
            background=_HDR_COL,
            foreground=_FG_DARK,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=(10, 7),
        )
        s.map(
            "Squads.Treeview",
            background=[("selected", "#dde4f8")],
            foreground=[("selected", _FG_DARK)],
        )
        s.map(
            "Squads.Treeview.Heading",
            background=[("active", "#d0d7ed")],
            relief=[("active", "flat")],
        )

    def _build_ui(self) -> None:
        self.configure(style="SContent.TFrame")

        paned = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            bg=_BG_CONT,
            sashwidth=8,
            sashrelief="flat",
            sashpad=0,
        )
        paned.pack(fill="both", expand=True, padx=12, pady=10)

        left = tk.Frame(paned, bg=_BG_CARD)
        paned.add(left, minsize=380, stretch="always")
        self._build_left(left)

        right = tk.Frame(paned, bg=_BG_CARD)
        paned.add(right, minsize=280, stretch="never")
        self._build_right(right)

    def _build_left(self, parent: tk.Frame) -> None:
        hdr = tk.Frame(parent, bg=_BG, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="🏷️  Times",
            font=("Segoe UI", 11, "bold"),
            bg=_BG,
            fg=_FG_WHITE,
            padx=14,
        ).pack(side="left", fill="y")

        self._lbl_count = tk.Label(
            hdr,
            text="",
            font=("Segoe UI", 9),
            bg=_BG,
            fg=_FG_MUTED,
            padx=4,
        )
        self._lbl_count.pack(side="left", fill="y")

        tk.Button(
            hdr,
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
            cursor="hand2",
        ).pack(side="right", padx=(2, 8), fill="y")

        for text, cmd, bg_n, bg_h in [
            ("✕", self.remover, _BTN_HOVER, _BG),
            ("✎", self.editar, _BTN_HOVER, _BG),
            ("＋", self.adicionar, _ACCENT, _ACCENT_DK),
        ]:
            tk.Button(
                hdr,
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
                cursor="hand2",
            ).pack(side="right", padx=2, fill="y", pady=8)

        tree_wrap = tk.Frame(parent, bg=_BG_CARD)
        tree_wrap.pack(fill="both", expand=True)

        cols = ("Time", "Descrição")
        self.tree_squads = ttk.Treeview(
            tree_wrap,
            columns=cols,
            show="headings",
            style="Squads.Treeview",
            selectmode="browse",
        )
        self.tree_squads.heading("Time", text="Time")
        self.tree_squads.heading("Descrição", text="Descrição")
        self.tree_squads.column("Time", width=170, minwidth=100, stretch=False)
        self.tree_squads.column("Descrição", width=210, minwidth=80, stretch=True)

        self.tree_squads.tag_configure("odd", background=_BG_CARD)
        self.tree_squads.tag_configure("even", background=_ROW_ALT)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree_squads.yview)
        self.tree_squads.configure(yscrollcommand=vsb.set)
        self.tree_squads.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree_squads.bind("<<TreeviewSelect>>", self._on_select)

    def _build_right(self, parent: tk.Frame) -> None:
        rhdr = tk.Frame(parent, bg=_BG_HDR)
        rhdr.pack(fill="x")

        tk.Label(
            rhdr,
            text="Membros do Time",
            font=("Segoe UI", 10, "bold"),
            bg=_BG_HDR,
            fg=_FG_WHITE,
            padx=14,
            pady=10,
        ).pack(side="left")

        self._lbl_squad_nome = tk.Label(
            rhdr,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=_BG_HDR,
            fg=_ACCENT,
            padx=4,
        )
        self._lbl_squad_nome.pack(side="left", fill="y")

        tk.Button(
            rhdr,
            text="💾",
            command=self.salvar_membros,
            bg=_BG_HDR,
            fg=_FG_WHITE,
            activebackground=_BTN_HOVER,
            activeforeground=_FG_WHITE,
            relief="flat",
            bd=0,
            padx=10,
            font=("Segoe UI Emoji", 13),
            cursor="hand2",
        ).pack(side="right", padx=(2, 10), fill="y")

        tk.Frame(parent, bg=_SEP, height=1).pack(fill="x")

        canvas_wrap = tk.Frame(parent, bg=_BG_CARD)
        canvas_wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(canvas_wrap, bg=_BG_CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(canvas_wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=_BG_CARD)
        self._canvas_win = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", self._sync_scroll)
        self._canvas.bind("<Configure>", self._sync_width)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._show_placeholder()

    def _sync_scroll(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _sync_width(self, event) -> None:
        self._canvas.itemconfig(self._canvas_win, width=event.width)

    def _on_mousewheel(self, event) -> None:
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _show_placeholder(self) -> None:
        for w in self._inner.winfo_children():
            w.destroy()
        tk.Label(
            self._inner,
            text="Selecione um time\npara gerenciar seus membros",
            font=("Segoe UI", 10),
            bg=_BG_CARD,
            fg=_FG_MUTED,
            justify="center",
            pady=40,
        ).pack(fill="x")

    def _section_label(self, text: str, bg: str, fg: str) -> None:
        f = tk.Frame(self._inner, bg=bg, height=26)
        f.pack(fill="x")
        f.pack_propagate(False)
        tk.Label(
            f,
            text=text,
            font=("Segoe UI", 8, "bold"),
            bg=bg,
            fg=fg,
            anchor="w",
            padx=12,
        ).pack(side="left", fill="y")

    def _membro_row(
        self,
        membro_id: str,
        membro_nome: str,
        patente: str,
        is_enrolled: bool,
        idx: int,
    ) -> None:
        bg = (
            (_ENROLL_BG if idx % 2 == 0 else _ENROLL_BG_ALT)
            if is_enrolled
            else (_BG_CARD if idx % 2 == 0 else _ROW_ALT)
        )

        row = tk.Frame(self._inner, bg=bg, height=38)
        row.pack(fill="x")
        row.pack_propagate(False)

        accent = _ACCENT if is_enrolled else _SEP
        tk.Frame(row, bg=accent, width=3).pack(side="left", fill="y")

        var_check = tk.BooleanVar(value=is_enrolled)
        tk.Checkbutton(
            row,
            text=membro_nome,
            variable=var_check,
            bg=bg,
            fg=_FG_DARK,
            selectcolor=_BG_CARD,
            activebackground=bg,
            activeforeground=_FG_DARK,
            font=("Segoe UI", 9),
            anchor="w",
            cursor="hand2",
        ).pack(side="left", padx=8, fill="y")

        var_patente = tk.StringVar(value=patente)
        ttk.Combobox(
            row,
            textvariable=var_patente,
            values=self.patentes,
            width=10,
            state="readonly",
            font=("Segoe UI", 9),
        ).pack(side="right", padx=10, pady=6)

        self.membros_widgets[membro_id] = (var_check, var_patente)

    def atualizar_lista(self) -> None:
        for item in self.tree_squads.get_children():
            self.tree_squads.delete(item)

        with session_scope() as session:
            squads = session.query(Squad).order_by(Squad.nome).all()

            for idx, squad in enumerate(squads):
                tag = "odd" if idx % 2 == 0 else "even"
                self.tree_squads.insert(
                    "", "end", iid=squad.id, values=(squad.nome, ""), tags=(tag,)
                )

        total = len(self.tree_squads.get_children())
        self._lbl_count.config(text=f"({total} time{'s' if total != 1 else ''})")
        self._show_placeholder()
        self._lbl_squad_nome.config(text="")
        self._squad_selecionado = None

    def _on_select(self, _event=None) -> None:
        sel = self.tree_squads.selection()
        if not sel:
            return

        squad_id = sel[0]
        self._squad_selecionado = squad_id
        nome = self.tree_squads.item(sel[0])["values"][0]
        self._lbl_squad_nome.config(text=nome)

        for w in self._inner.winfo_children():
            w.destroy()
        self.membros_widgets = {}

        with session_scope() as session:
            todos = session.query(Member).order_by(Member.name).all()
            enrolled_rows = (
                session.query(MemberSquad)
                .filter(MemberSquad.squad_id == squad_id)
                .all()
            )
            enrolled = {
                row.member_id: _LEVEL_TO_PATENTE.get(row.level, "Membro")
                for row in enrolled_rows
            }

        if not todos:
            tk.Label(
                self._inner,
                text="Nenhum membro cadastrado.\nAdicione membros na aba Membros.",
                font=("Segoe UI", 10),
                bg=_BG_CARD,
                fg=_FG_MUTED,
                justify="center",
                pady=30,
            ).pack(fill="x")
            return

        matriculados = [(m.id, m.name) for m in todos if m.id in enrolled]
        disponiveis = [(m.id, m.name) for m in todos if m.id not in enrolled]

        if matriculados:
            self._section_label(
                f"✓  Matriculado  ({len(matriculados)})",
                bg=_ENROLL_BG,
                fg=_ACCENT,
            )
            for i, (mid, mn) in enumerate(matriculados):
                self._membro_row(mid, mn, enrolled[mid], True, i)

        if matriculados and disponiveis:
            tk.Frame(self._inner, bg=_SEP, height=1).pack(fill="x", pady=2)

        if disponiveis:
            self._section_label(
                f"+  Disponível  ({len(disponiveis)})",
                bg=_HDR_COL,
                fg=_FG_MUTED,
            )
            for i, (mid, mn) in enumerate(disponiveis):
                self._membro_row(mid, mn, self.patentes[-1], False, i)

    def adicionar(self) -> None:
        dlg = SquadDialog(self, "Adicionar Time")
        if not dlg.result:
            return

        nome, _desc = dlg.result
        try:
            with session_scope() as session:
                session.add(Squad(nome=nome))
        except IntegrityError:
            messagebox.showerror("Erro", "Já existe um time com esse nome.")
            return

        messagebox.showinfo("Sucesso", f"Time '{nome}' adicionado.")
        self.atualizar_lista()

    def editar(self) -> None:
        sel = self.tree_squads.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um time.")
            return

        squad_id = sel[0]
        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            if not squad:
                messagebox.showwarning("Aviso", "Time não encontrado.")
                return

            dlg = SquadDialog(self, "Editar Time", squad.nome, "")
            if not dlg.result:
                return

            novo_nome, _nova_desc = dlg.result
            squad.nome = novo_nome

        messagebox.showinfo("Sucesso", "Time atualizado.")
        self.atualizar_lista()

    def remover(self) -> None:
        sel = self.tree_squads.selection()
        if not sel:
            return

        squad_id = sel[0]
        nome = self.tree_squads.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", f"Remover time '{nome}'?"):
            return

        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            if squad:
                session.delete(squad)

        messagebox.showinfo("Sucesso", "Time removido.")
        self.atualizar_lista()

    def salvar_membros(self) -> None:
        if not self._squad_selecionado:
            messagebox.showwarning("Aviso", "Selecione um time primeiro.")
            return
        if not self.membros_widgets:
            messagebox.showwarning("Aviso", "Nenhum membro carregado.")
            return

        squad_id = self._squad_selecionado
        try:
            with session_scope() as session:
                (
                    session.query(MemberSquad)
                    .filter(MemberSquad.squad_id == squad_id)
                    .delete(synchronize_session=False)
                )

                for membro_id, (var_check, var_patente) in self.membros_widgets.items():
                    if var_check.get():
                        session.add(
                            MemberSquad(
                                member_id=membro_id,
                                squad_id=squad_id,
                                level=_PATENTE_TO_LEVEL.get(var_patente.get(), 2),
                            )
                        )
        except IntegrityError as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
            return

        messagebox.showinfo("Sucesso", "Membros atualizados.")
        self.atualizar_lista()
        self.tree_squads.selection_set(str(squad_id))
        self._on_select()
