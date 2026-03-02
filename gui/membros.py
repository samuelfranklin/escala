# gui/membros_orm.py — Versão ORM de membros.py
import tkinter as tk
from tkinter import messagebox, ttk

from infra.database import Member, MemberSquad, Squad, session_scope
from utils import MembroDialog, center_popup

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

_ENROLL_BG = "#e8f0fe"
_ENROLL_BG_ALT = "#dde7fd"


class MembrosFrame(ttk.Frame):
    def __init__(self, parent, db=None):
        super().__init__(parent)
        self.db = db  # Não é usado em ORM, apenas para compatibilidade
        self.patentes = ["Líder", "Treinador", "Membro", "Recruta"]
        self.squads_widgets: dict[str, tuple[tk.BooleanVar, tk.StringVar]] = {}
        self._membro_selecionado: str | None = None
        self._setup_styles()
        self._build_ui()
        self.atualizar_lista()

    # ------------------------------------------------------------------
    # Estilos ttk
    # ------------------------------------------------------------------

    def _setup_styles(self) -> None:
        s = ttk.Style()
        s.configure("MContent.TFrame", background=_BG_CONT)
        s.configure("MCard.TFrame", background=_BG_CARD)

        s.configure(
            "Membros.Treeview",
            background=_BG_CARD,
            fieldbackground=_BG_CARD,
            foreground=_FG_DARK,
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        s.configure(
            "Membros.Treeview.Heading",
            background=_HDR_COL,
            foreground=_FG_DARK,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=(10, 7),
        )
        s.map(
            "Membros.Treeview",
            background=[("selected", "#dde4f8")],
            foreground=[("selected", _FG_DARK)],
        )
        s.map(
            "Membros.Treeview.Heading",
            background=[("active", "#d0d7ed")],
            relief=[("active", "flat")],
        )

    # ------------------------------------------------------------------
    # Layout raiz
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.configure(style="MContent.TFrame")

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
        paned.add(left, minsize=440, stretch="always")
        self._build_left(left)

        right = tk.Frame(paned, bg=_BG_CARD)
        paned.add(right, minsize=280, stretch="never")
        self._build_right(right)

    # ------------------------------------------------------------------
    # Painel esquerdo — lista de membros
    # ------------------------------------------------------------------

    def _build_left(self, parent: tk.Frame) -> None:
        # Cabeçalho
        hdr = tk.Frame(parent, bg=_BG, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="👥  Membros",
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

        # Botões de ação alinhados à direita do cabeçalho
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

        # Treeview
        tree_wrap = tk.Frame(parent, bg=_BG_CARD)
        tree_wrap.pack(fill="both", expand=True)

        cols = ("Membro", "Telefone", "Times")
        self.tree_membros = ttk.Treeview(
            tree_wrap,
            columns=cols,
            show="headings",
            style="Membros.Treeview",
            selectmode="browse",
        )
        widths = {"Membro": 200, "Telefone": 110, "Times": 160}
        for col in cols:
            self.tree_membros.heading(col, text=col)
            self.tree_membros.column(
                col,
                width=widths[col],
                minwidth=70,
                stretch=(col == "Membro"),
            )

        self.tree_membros.tag_configure("odd", background=_BG_CARD)
        self.tree_membros.tag_configure("even", background=_ROW_ALT)

        vsb = ttk.Scrollbar(
            tree_wrap, orient="vertical", command=self.tree_membros.yview
        )
        self.tree_membros.configure(yscrollcommand=vsb.set)
        self.tree_membros.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree_membros.bind("<<TreeviewSelect>>", self._on_select)

    # ------------------------------------------------------------------
    # Painel direito — times do membro
    # ------------------------------------------------------------------

    def _build_right(self, parent: tk.Frame) -> None:
        # Cabeçalho
        rhdr = tk.Frame(parent, bg=_BG_HDR)
        rhdr.pack(fill="x")

        tk.Label(
            rhdr,
            text="Times do Membro",
            font=("Segoe UI", 10, "bold"),
            bg=_BG_HDR,
            fg=_FG_WHITE,
            padx=14,
            pady=10,
        ).pack(side="left")

        self._lbl_nome = tk.Label(
            rhdr,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=_BG_HDR,
            fg=_ACCENT,
            padx=4,
        )
        self._lbl_nome.pack(side="left", fill="y")

        tk.Button(
            rhdr,
            text="💾",
            command=self.salvar_squads,
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

        # Canvas scrollável
        canvas_wrap = tk.Frame(parent, bg=_BG_CARD)
        canvas_wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(canvas_wrap, bg=_BG_CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(canvas_wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=_BG_CARD)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )
        self._inner.bind("<Configure>", self._sync_scroll)
        self._canvas.bind("<Configure>", self._sync_width)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._show_placeholder()

    # ------------------------------------------------------------------
    # Helpers do canvas
    # ------------------------------------------------------------------

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
            text="Selecione um membro\npara gerenciar seus times",
            font=("Segoe UI", 10),
            bg=_BG_CARD,
            fg=_FG_MUTED,
            justify="center",
            pady=40,
        ).pack(fill="x")

    # ------------------------------------------------------------------
    # Helpers do painel de times
    # ------------------------------------------------------------------

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

    def _squad_row(
        self,
        squad_id: str,
        squad_nome: str,
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
            text=squad_nome,
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

        self.squads_widgets[squad_id] = (var_check, var_patente)

    # ------------------------------------------------------------------
    # Dados — lista principal via ORM
    # ------------------------------------------------------------------

    def atualizar_lista(self) -> None:
        for item in self.tree_membros.get_children():
            self.tree_membros.delete(item)

        with session_scope() as session:
            members = session.query(Member).order_by(Member.name).all()

            for idx, member in enumerate(members):
                # Carregar times deste membro
                squads_list = [ms.squad.nome for ms in member.memberships]
                times_str = ", ".join(squads_list)

                tag = "odd" if idx % 2 == 0 else "even"
                self.tree_membros.insert(
                    "",
                    "end",
                    iid=member.id,
                    values=(member.name, member.phone_number or "", times_str),
                    tags=(tag,),
                )

            total = len(members)
            self._lbl_count.config(text=f"({total} membro{'s' if total != 1 else ''})")

        self._show_placeholder()
        self._lbl_nome.config(text="")
        self._membro_selecionado = None

    # ------------------------------------------------------------------
    # Painel direito — carrega todos os times ao selecionar membro
    # ------------------------------------------------------------------

    def _on_select(self, _event=None) -> None:
        sel = self.tree_membros.selection()
        if not sel:
            return

        membro_id = sel[0]
        self._membro_selecionado = membro_id

        with session_scope() as session:
            member = session.query(Member).filter_by(id=membro_id).first()
            if not member:
                return
            nome = member.name

        self._lbl_nome.config(text=nome)

        for w in self._inner.winfo_children():
            w.destroy()
        self.squads_widgets = {}

        with session_scope() as session:
            # Todos os times disponíveis
            todos = session.query(Squad).order_by(Squad.nome).all()

            if not todos:
                tk.Label(
                    self._inner,
                    text="Nenhum time cadastrado.\nAdicione times na aba Times.",
                    font=("Segoe UI", 10),
                    bg=_BG_CARD,
                    fg=_FG_MUTED,
                    justify="center",
                    pady=30,
                ).pack(fill="x")
                return

            # Times em que o membro já está
            member = session.query(Member).filter_by(id=membro_id).first()
            enrolled_dict = {ms.squad_id: ms.level for ms in member.memberships}

            matriculados = [(s.id, s.nome) for s in todos if s.id in enrolled_dict]
            disponiveis = [(s.id, s.nome) for s in todos if s.id not in enrolled_dict]

            # ── Seção: matriculado ────────────────────────────────────────
            if matriculados:
                self._section_label(
                    f"✓  Matriculado  ({len(matriculados)})",
                    bg=_ENROLL_BG,
                    fg=_ACCENT,
                )
                for i, (sid, sn) in enumerate(matriculados):
                    self._squad_row(sid, sn, str(enrolled_dict[sid]), True, i)

            # Divisor
            if matriculados and disponiveis:
                tk.Frame(self._inner, bg=_SEP, height=1).pack(fill="x", pady=2)

            # ── Seção: disponível para adicionar ─────────────────────────
            if disponiveis:
                self._section_label(
                    f"+  Disponível  ({len(disponiveis)})",
                    bg=_HDR_COL,
                    fg=_FG_MUTED,
                )
                for i, (sid, sn) in enumerate(disponiveis):
                    self._squad_row(sid, sn, self.patentes[-1], False, i)

    # ------------------------------------------------------------------
    # CRUD — Membros via ORM
    # ------------------------------------------------------------------

    def adicionar(self) -> None:
        dlg = MembroDialog(self, self.patentes)
        if not dlg.result:
            return

        nome, email, telefone, patente, data_entrada, obs = dlg.result
        with session_scope() as session:
            member = Member(
                name=nome,
                email=email or None,
                phone_number=telefone or None,
                status=True,
            )
            session.add(member)
            session.commit()
        self.atualizar_lista()

    def editar(self) -> None:
        sel = self.tree_membros.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um membro.")
            return

        membro_id = sel[0]

        with session_scope() as session:
            member = session.query(Member).filter_by(id=membro_id).first()
            if not member:
                messagebox.showwarning("Aviso", "Membro não encontrado.")
                return

            dlg = MembroDialog(
                self,
                self.patentes,
                nome=member.name or "",
                email=member.email or "",
                telefone=member.phone_number or "",
                patente="",  # Patente não é armazenada em Member (é em level de MemberSquad)
                data_entrada="",
                obs="",
                edicao=True,
            )

        if not dlg.result:
            return

        nome, email, telefone, patente, data_entrada, obs = dlg.result
        with session_scope() as session:
            member = session.query(Member).filter_by(id=membro_id).first()
            if member:
                member.name = nome
                member.email = email or None
                member.phone_number = telefone or None
                session.commit()
        self.atualizar_lista()

    def remover(self) -> None:
        sel = self.tree_membros.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um membro.")
            return

        membro_id = sel[0]

        with session_scope() as session:
            member = session.query(Member).filter_by(id=membro_id).first()
            if not member:
                return
            nome = member.name

        if not messagebox.askyesno("Confirmar", f"Remover membro '{nome}'?"):
            return

        with session_scope() as session:
            member = session.query(Member).filter_by(id=membro_id).first()
            if member:
                session.delete(member)
                session.commit()
        self.atualizar_lista()

    # ------------------------------------------------------------------
    # Salvar vínculo membro ↔ times
    # ------------------------------------------------------------------

    def salvar_squads(self) -> None:
        if not self._membro_selecionado:
            messagebox.showwarning("Aviso", "Selecione um membro primeiro.")
            return
        if not self.squads_widgets:
            messagebox.showwarning("Aviso", "Nenhum time carregado.")
            return

        membro_id = self._membro_selecionado

        with session_scope() as session:
            member = session.query(Member).filter_by(id=membro_id).first()
            if not member:
                return

            # Limpar todas as associações atuais
            for ms in member.memberships:
                session.delete(ms)

            # Adicionar novas associações baseado no widget
            for squad_id, (var_check, var_patente) in self.squads_widgets.items():
                if var_check.get():
                    try:
                        level = int(var_patente.get())
                    except (ValueError, TypeError):
                        level = 1
                    new_ms = MemberSquad(
                        member_id=member.id,
                        squad_id=squad_id,
                        level=level,
                    )
                    session.add(new_ms)

            session.commit()

        self.atualizar_lista()
        self.tree_membros.selection_set(membro_id)
        self._on_select()
