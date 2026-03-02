# gui/disponibilidade_orm.py

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from infra.database import Member, MemberRestrictions, session_scope


class DisponibilidadeFrame(tk.Frame):
    """Gerenciador de disponibilidade e bloqueios com dark theme."""

    # Paleta de cores
    _BG = "#1e2533"
    _BG_CARD = "#202938"
    _HDR_COL = "#0f1b2e"
    _ACCENT = "#4f7ef8"
    _ACCENT_DARK = "#3859c4"
    _TXT_PRIMARY = "#e8e8e8"
    _TXT_SECONDARY = "#a0a0a8"
    _BTN_HOVER = "#5a85ff"
    _BORDER = "#2a3647"

    def __init__(self, parent):
        super().__init__(parent, bg=self._BG)
        self.membro_atual_id = None
        self._build_widgets()
        self._load_membros()

    def _build_widgets(self):
        """Constrói interface com design dark."""
        # Header
        self._build_header()

        # Frame principal
        main_frame = tk.Frame(self, bg=self._BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Seleção de membro
        sel_frame = tk.Frame(main_frame, bg=self._BG_CARD, relief="solid", borderwidth=1)
        sel_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            sel_frame,
            text="Membro:",
            bg=self._BG_CARD,
            fg=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=15, pady=10)
        
        self.combo_membros = ttk.Combobox(sel_frame, state="readonly", width=40)
        self.combo_membros.pack(side="left", padx=0, pady=10)
        self.combo_membros.bind("<<ComboboxSelected>>", self._on_membro_selected)

        # Notebook com abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # Aba de Restrições
        self.frame_restricoes = tk.Frame(self.notebook, bg=self._BG)
        self.notebook.add(self.frame_restricoes, text="Restrições")
        self._build_tab_restricoes()

    def _build_header(self):
        """Header com ícone e título."""
        header = tk.Frame(self, bg=self._HDR_COL, height=50)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="📅  Disponibilidade",
            font=("Segoe UI", 14, "bold"),
            bg=self._HDR_COL,
            fg=self._TXT_PRIMARY,
        )
        title_label.pack(side="left", padx=15, pady=10)

    def _build_tab_restricoes(self):
        """Constrói aba de restrições."""
        frame = tk.Frame(self.frame_restricoes, bg=self._BG)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Título
        tk.Label(
            frame,
            text="Adicionar Restrição",
            font=("Segoe UI", 11, "bold"),
            bg=self._BG,
            fg=self._TXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 10))

        # Form
        form_frame = tk.Frame(frame, bg=self._BG)
        form_frame.pack(fill="x", pady=10)

        tk.Label(
            form_frame,
            text="Data (DD/MM/YYYY):",
            bg=self._BG,
            fg=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_data = tk.Entry(form_frame, width=15, bg=self._BG_CARD, fg=self._TXT_PRIMARY)
        self.entry_data.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(
            form_frame,
            text="Descrição:",
            bg=self._BG,
            fg=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_descricao = tk.Entry(form_frame, width=40, bg=self._BG_CARD, fg=self._TXT_PRIMARY)
        self.entry_descricao.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Botões
        btn_frame = tk.Frame(form_frame, bg=self._BG)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        btn_add = tk.Button(
            btn_frame,
            text="➕ Adicionar",
            command=self._add_restricao,
            bg=self._ACCENT,
            fg=self._TXT_PRIMARY,
            border=0,
            activebackground=self._BTN_HOVER,
            activeforeground=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
            cursor="hand2",
            padx=12,
            pady=5,
        )
        btn_add.pack(side="left", padx=5)

        # Lista de restrições
        tk.Label(
            frame,
            text="Restrições Cadastradas:",
            bg=self._BG,
            fg=self._TXT_PRIMARY,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(10, 5))

        self._setup_restricoes_treeview()
        tree_frame = tk.Frame(frame, bg=self._BG)
        tree_frame.pack(fill="both", expand=True, pady=10)

        cols = ("Data", "Descrição")
        self.tree_restricoes = ttk.Treeview(
            tree_frame, columns=cols, show="headings", height=10, style="Disponibilidade.Treeview"
        )
        for col in cols:
            self.tree_restricoes.heading(col, text=col)
        self.tree_restricoes.column("Data", width=120)
        self.tree_restricoes.column("Descrição", width=300)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_restricoes.yview)
        self.tree_restricoes.configure(yscrollcommand=scroll.set)
        self.tree_restricoes.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Botão remover
        btn_remove = tk.Button(
            frame,
            text="🗑️  Remover Selecionado",
            command=self._remove_restricao,
            bg=self._ACCENT,
            fg=self._TXT_PRIMARY,
            border=0,
            activebackground=self._BTN_HOVER,
            activeforeground=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
            cursor="hand2",
            padx=12,
            pady=5,
        )
        btn_remove.pack(pady=5)

    def _setup_restricoes_treeview(self):
        """Configura estilo dark para a Treeview de restrições."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Disponibilidade.Treeview",
            background=self._BG_CARD,
            foreground=self._TXT_PRIMARY,
            fieldbackground=self._BG_CARD,
            borderwidth=0,
        )
        style.map(
            "Disponibilidade.Treeview",
            background=[("selected", self._ACCENT)],
            foreground=[("selected", self._TXT_PRIMARY)],
        )

        style.configure(
            "Disponibilidade.Treeview.Heading",
            background=self._HDR_COL,
            foreground=self._TXT_PRIMARY,
            borderwidth=0,
            relief="flat",
        )

    def _load_membros(self):
        """Carrega membros para combo."""
        try:
            with session_scope() as session:
                membros = session.query(Member).order_by(Member.name).all()
                self.membros_dict = {m.name: m.id for m in membros}
                nomes = [m.name for m in membros]
                self.combo_membros["values"] = nomes
                if nomes:
                    self.combo_membros.set(nomes[0])
                    self._on_membro_selected()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar membros: {e}")

    def _on_membro_selected(self, event=None):
        """Callback quando membro é selecionado."""
        nome = self.combo_membros.get()
        if not nome:
            return
        self.membro_atual_id = self.membros_dict.get(nome)
        self._load_restricoes()

    def _load_restricoes(self):
        """Carrega restrições do membro selecionado."""
        if not self.membro_atual_id:
            return

        # Limpar treeview
        for item in self.tree_restricoes.get_children():
            self.tree_restricoes.delete(item)

        try:
            with session_scope() as session:
                restricoes = (
                    session.query(MemberRestrictions)
                    .filter(MemberRestrictions.member_id == self.membro_atual_id)
                    .order_by(MemberRestrictions.date)
                    .all()
                )
                for restricao in restricoes:
                    self.tree_restricoes.insert(
                        "",
                        "end",
                        values=(restricao.date.strftime("%d/%m/%Y"), restricao.description or ""),
                    )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar restrições: {e}")

    def _add_restricao(self):
        """Adiciona nova restrição."""
        if not self.membro_atual_id:
            messagebox.showwarning("Aviso", "Selecione um membro.")
            return

        data_str = self.entry_data.get().strip()
        descricao = self.entry_descricao.get().strip()

        if not data_str:
            messagebox.showwarning("Aviso", "Informe a data.")
            return

        try:
            data = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Erro", "Data inválida. Use DD/MM/YYYY.")
            return

        try:
            with session_scope() as session:
                restricao = MemberRestrictions(
                    member_id=self.membro_atual_id,
                    date=data,
                    description=descricao,
                )
                session.add(restricao)
                session.commit()
                messagebox.showinfo("Sucesso", "Restrição adicionada.")
                self._load_restricoes()
                self.entry_data.delete(0, tk.END)
                self.entry_descricao.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar restrição: {e}")

    def _remove_restricao(self):
        """Remove restrição selecionada."""
        sel = self.tree_restricoes.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma restrição.")
            return

        item = self.tree_restricoes.item(sel[0])
        data_str = item["values"][0]
        descricao = item["values"][1]

        if not messagebox.askyesno(
            "Confirmar", f"Remover restrição de {data_str}?"
        ):
            return

        try:
            data = datetime.strptime(data_str, "%d/%m/%Y").date()
            with session_scope() as session:
                restricao = (
                    session.query(MemberRestrictions)
                    .filter(
                        (MemberRestrictions.member_id == self.membro_atual_id)
                        & (MemberRestrictions.date == data)
                    )
                    .first()
                )
                if restricao:
                    session.delete(restricao)
                    session.commit()
                    messagebox.showinfo("Sucesso", "Restrição removida.")
                    self._load_restricoes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover restrição: {e}")

    def atualizar_lista(self):
        """Callback acionado por sincronização."""
        self._load_restricoes()
