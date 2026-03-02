# gui/casais_orm.py

import tkinter as tk
from tkinter import messagebox, ttk

from infra.database import FamilyCouple, Member, session_scope


class CasaisFrame(tk.Frame):
    """Gerenciador de casais/famílias com dark theme."""

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
        self._build_widgets()
        self._refresh_data()

    def _build_widgets(self):
        """Constrói interface com design dark."""
        # Header
        self._build_header()

        # Frame principal
        main_frame = tk.Frame(self, bg=self._BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview com dark styling
        self._setup_treeview_style()
        colunas = ("Cônjuge 1", "Cônjuge 2")
        self.tree = ttk.Treeview(
            main_frame, columns=colunas, show="headings", height=12, style="Casais.Treeview"
        )
        self.tree.heading("Cônjuge 1", text="Cônjuge 1")
        self.tree.heading("Cônjuge 2", text="Cônjuge 2")
        self.tree.column("Cônjuge 1", width=300)
        self.tree.column("Cônjuge 2", width=300)

        scroll = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Frame de cadastro
        self._build_form()

    def _build_header(self):
        """Header com ícone e título."""
        header = tk.Frame(self, bg=self._HDR_COL, height=50)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="💑  Casais",
            font=("Segoe UI", 14, "bold"),
            bg=self._HDR_COL,
            fg=self._TXT_PRIMARY,
        )
        title_label.pack(side="left", padx=15, pady=10)

    def _setup_treeview_style(self):
        """Configura estilo dark para a Treeview."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Casais.Treeview",
            background=self._BG_CARD,
            foreground=self._TXT_PRIMARY,
            fieldbackground=self._BG_CARD,
            borderwidth=0,
        )
        style.map(
            "Casais.Treeview",
            background=[("selected", self._ACCENT)],
            foreground=[("selected", self._TXT_PRIMARY)],
        )

        style.configure(
            "Casais.Treeview.Heading",
            background=self._HDR_COL,
            foreground=self._TXT_PRIMARY,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Casais.Treeview.Heading",
            background=[("active", self._ACCENT)],
        )

    def _build_form(self):
        """Frame de cadastro com dark theme."""
        form_frame = tk.Frame(self, bg=self._BG_CARD, relief="solid", borderwidth=1, bd=1)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Título do formulário
        title = tk.Label(
            form_frame,
            text="Cadastrar Casal",
            font=("Segoe UI", 11, "bold"),
            bg=self._BG_CARD,
            fg=self._TXT_PRIMARY,
        )
        title.pack(anchor="w", padx=15, pady=(10, 5))

        # Labels e inputs
        inner_frame = tk.Frame(form_frame, bg=self._BG_CARD)
        inner_frame.pack(fill="x", padx=15, pady=(5, 15))

        tk.Label(
            inner_frame,
            text="Cônjuge 1:",
            bg=self._BG_CARD,
            fg=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.combo1 = ttk.Combobox(inner_frame, state="readonly", width=35)
        self.combo1.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(
            inner_frame,
            text="Cônjuge 2:",
            bg=self._BG_CARD,
            fg=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.combo2 = ttk.Combobox(inner_frame, state="readonly", width=35)
        self.combo2.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Botões
        btn_frame = tk.Frame(form_frame, bg=self._BG_CARD)
        btn_frame.pack(fill="x", padx=15, pady=(0, 10))

        buttons = [
            ("➕ Cadastrar", self.cadastrar),
            ("🗑️  Remover", self.remover),
            ("🔄 Atualizar", self._refresh_data),
        ]

        for text, command in buttons:
            btn = tk.Button(
                btn_frame,
                text=text,
                command=command,
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
            btn.pack(side="left", padx=5)

    def _refresh_data(self):
        """Atualiza lista de casais e comboboxes."""
        self._load_casais()
        self._load_membros_combo()

    def _load_membros_combo(self):
        """Carrega membros para os comboboxes."""
        try:
            with session_scope() as session:
                membros = session.query(Member).order_by(Member.name).all()
                self.membros_dict = {m.name: m.id for m in membros}
                nomes = [m.name for m in membros]
                self.combo1["values"] = nomes
                self.combo2["values"] = nomes
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar membros: {e}")

    def _load_casais(self):
        """Carrega lista de casais da base."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with session_scope() as session:
                casais = session.query(FamilyCouple).order_by(FamilyCouple.member1_id).all()
                for casal in casais:
                    nome1 = casal.member1.name if casal.member1 else "N/A"
                    nome2 = casal.member2.name if casal.member2 else "N/A"
                    self.tree.insert("", "end", values=(nome1, nome2))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar casais: {e}")

    def atualizar_lista(self):
        """Callback acionado por sincronização."""
        self._load_casais()

    def cadastrar(self):
        """Cadastra novo casal."""
        nome1 = self.combo1.get()
        nome2 = self.combo2.get()

        if not nome1 or not nome2:
            messagebox.showwarning("Aviso", "Selecione os dois cônjuges.")
            return
        if nome1 == nome2:
            messagebox.showwarning("Aviso", "Os cônjuges devem ser pessoas diferentes.")
            return

        id1 = self.membros_dict.get(nome1)
        id2 = self.membros_dict.get(nome2)
        if not id1 or not id2:
            messagebox.showerror("Erro", "Membros não encontrados.")
            return

        try:
            with session_scope() as session:
                # Verifica se casal já existe
                existe = (
                    session.query(FamilyCouple)
                    .filter(
                        ((FamilyCouple.member1_id == id1) & (FamilyCouple.member2_id == id2))
                        | ((FamilyCouple.member1_id == id2) & (FamilyCouple.member2_id == id1))
                    )
                    .first()
                )
                if existe:
                    messagebox.showerror("Erro", "Este casal já existe.")
                    return

                novo_casal = FamilyCouple(member1_id=id1, member2_id=id2)
                session.add(novo_casal)
                session.commit()
                messagebox.showinfo("Sucesso", "Casal cadastrado.")
                self._load_casais()
                self.combo1.set("")
                self.combo2.set("")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar casal: {e}")

    def remover(self):
        """Remove casal selecionado."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um casal na lista.")
            return

        item = self.tree.item(sel[0])
        nome1, nome2 = item["values"]

        if not messagebox.askyesno(
            "Confirmar", f"Remover casal: {nome1} e {nome2}?"
        ):
            return

        id1 = self.membros_dict.get(nome1)
        id2 = self.membros_dict.get(nome2)
        if not id1 or not id2:
            messagebox.showerror("Erro", "Membros não encontrados.")
            return

        try:
            with session_scope() as session:
                casal = (
                    session.query(FamilyCouple)
                    .filter(
                        ((FamilyCouple.member1_id == id1) & (FamilyCouple.member2_id == id2))
                        | ((FamilyCouple.member1_id == id2) & (FamilyCouple.member2_id == id1))
                    )
                    .first()
                )
                if casal:
                    session.delete(casal)
                    session.commit()
                    messagebox.showinfo("Sucesso", "Casal removido.")
                    self._load_casais()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover casal: {e}")
