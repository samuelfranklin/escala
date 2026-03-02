# gui/config_escala_orm.py - Configuração de Eventos com dark theme

import tkinter as tk
from tkinter import messagebox, ttk

from infra.database import Event, EventSquad, Squad, session_scope


class ConfigEventoDialog(tk.Toplevel):
    """Diálogo para selecionar squads necessários e quantidade de voluntários por squad para um evento."""

    # Paleta de cores
    _BG = "#1e2533"
    _BG_CARD = "#202938"
    _HDR_COL = "#0f1b2e"
    _ACCENT = "#4f7ef8"
    _TXT_PRIMARY = "#e8e8e8"
    _TXT_SECONDARY = "#a0a0a8"
    _BTN_HOVER = "#5a85ff"

    def __init__(self, parent, evento_id: str, evento_nome: str):
        super().__init__(parent)
        self.event_id = evento_id
        self.event_name = evento_nome
        self.squad_configs = {}  # squad_id -> {"var": BooleanVar, "spinbox": Spinbox}

        self.title(f"Configurar: {evento_nome}")
        self.geometry("600x500")
        self.resizable(False, False)
        self.configure(bg=self._BG)

        # Centralizar janela
        self.transient(parent)
        self.grab_set()

        try:
            self._build_widgets()
            self._load_configurations()
        except Exception as e:
            messagebox.showerror("Erro ao construir interface", str(e))
            self.destroy()

    def _build_widgets(self):
        """Construir interface do diálogo."""
        # Header
        header = tk.Frame(self, bg=self._HDR_COL, height=50)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text=f"⚙️  {self.event_name}",
            font=("Segoe UI", 12, "bold"),
            bg=self._HDR_COL,
            fg=self._TXT_PRIMARY,
        )
        title.pack(side="left", padx=15, pady=10)

        # Carregar squads primeiro
        squads_data = []
        try:
            with session_scope() as session:
                squads = session.query(Squad).order_by(Squad.nome).all()
                for squad in squads:
                    squads_data.append({"id": squad.id, "nome": squad.nome})
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar equipes: {e}")
            return

        # Frame principal com scroll
        main_frame = tk.Frame(self, bg=self._BG)
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Cabeçalho de instrução
        header_lbl = tk.Frame(main_frame, bg=self._BG)
        header_lbl.pack(fill="x", padx=10, pady=10)

        tk.Label(
            header_lbl,
            text="Equipes necessárias para este evento:",
            font=("Segoe UI", 10, "bold"),
            bg=self._BG,
            fg=self._TXT_PRIMARY,
        ).pack(anchor="w")

        tk.Label(
            header_lbl,
            text="Marque a equipe se necessária. Quantidade padrão: 1",
            font=("Segoe UI", 8),
            bg=self._BG,
            fg=self._TXT_SECONDARY,
        ).pack(anchor="w")

        # Container para squads
        squads_container = tk.Frame(main_frame, bg=self._BG)
        squads_container.pack(fill="both", expand=True, padx=10, pady=0)

        # Populaar squads
        if squads_data:
            for squad_info in squads_data:
                self._create_squad_row(squads_container, squad_info)
        else:
            tk.Label(
                squads_container,
                text="Nenhuma equipe cadastrada.",
                font=("Segoe UI", 9),
                bg=self._BG,
                fg=self._TXT_SECONDARY,
            ).pack(pady=20)

        # Botões na base
        btn_frame = tk.Frame(self, bg=self._BG)
        btn_frame.pack(fill="x", padx=10, pady=10)

        # Botões
        btn_frame = tk.Frame(self, bg=self._BG)
        btn_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="💾 Salvar",
            command=self._save_configurations,
            bg=self._ACCENT,
            fg=self._TXT_PRIMARY,
            border=0,
            activebackground=self._BTN_HOVER,
            activeforeground=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
            cursor="hand2",
            padx=15,
            pady=6,
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=self.destroy,
            bg="#555555",
            fg=self._TXT_PRIMARY,
            border=0,
            activebackground="#666666",
            activeforeground=self._TXT_PRIMARY,
            font=("Segoe UI", 9),
            cursor="hand2",
            padx=15,
            pady=6,
        ).pack(side="left", padx=5)

    def _create_squad_row(self, parent, squad_info):
        """Cria uma linha para um squad no diálogo."""
        frame = tk.Frame(parent, bg=self._BG_CARD, relief="solid", bd=1)
        frame.pack(fill="x", pady=3, padx=0)

        # Checkbox para marcar se squad é necessário
        var = tk.BooleanVar(value=False)
        checkbox = tk.Checkbutton(
            frame,
            text=squad_info["nome"],
            variable=var,
            font=("Segoe UI", 9, "bold"),
            bg=self._BG_CARD,
            fg=self._TXT_PRIMARY,
            selectcolor=self._ACCENT,
            activebackground=self._BG_CARD,
            activeforeground=self._ACCENT,
            command=lambda squad_id=squad_info["id"]: self._on_squad_toggled(squad_id),
        )
        checkbox.pack(side="left", padx=10, pady=8)

        # Label e Spinbox para quantidade (desabilitado por padrão)
        qty_label = tk.Label(
            frame,
            text="Qtd:",
            font=("Segoe UI", 8),
            bg=self._BG_CARD,
            fg=self._TXT_SECONDARY,
        )
        qty_label.pack(side="left", padx=(15, 5))

        spinbox = tk.Spinbox(
            frame,
            from_=1,
            to=10,
            width=4,
            font=("Segoe UI", 9),
            bg=self._BG,
            fg=self._TXT_PRIMARY,
            state="disabled",
        )
        spinbox.delete(0, tk.END)
        spinbox.insert(0, "1")
        spinbox.pack(side="left", padx=5, pady=8)

        self.squad_configs[squad_info["id"]] = {
            "var": var,
            "checkbox": checkbox,
            "spinbox": spinbox,
            "label": qty_label,
            "squad_nome": squad_info["nome"],
        }

    def _on_squad_toggled(self, squad_id: str):
        """Ativa/desativa spinbox quando checkbox é marcado/desmarcado."""
        is_checked = self.squad_configs[squad_id]["var"].get()
        spinbox = self.squad_configs[squad_id]["spinbox"]
        label = self.squad_configs[squad_id]["label"]
        
        if is_checked:
            spinbox.config(state="normal")
            label.config(fg=self._TXT_PRIMARY)
        else:
            spinbox.config(state="disabled")
            label.config(fg=self._TXT_SECONDARY)

    def _load_configurations(self):
        """Carrega configurações atuais do evento."""
        try:
            with session_scope() as session:
                configs = (
                    session.query(EventSquad)
                    .filter(EventSquad.event_id == self.event_id)
                    .all()
                )

                for config in configs:
                    if config.squad_id in self.squad_configs:
                        self.squad_configs[config.squad_id]["var"].set(True)
                        spinbox = self.squad_configs[config.squad_id]["spinbox"]
                        spinbox.config(state="normal")
                        spinbox.delete(0, tk.END)
                        spinbox.insert(0, str(config.quantity or 1))
                        self.squad_configs[config.squad_id]["label"].config(fg=self._TXT_PRIMARY)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar configurações: {e}")

    def _save_configurations(self):
        """Salva as configurações editadas."""
        try:
            with session_scope() as session:
                # Remover configurações antigas
                session.query(EventSquad).filter(
                    EventSquad.event_id == self.event_id
                ).delete()

                # Inserir novas configurações apenas dos squads selecionados
                for squad_id, config_data in self.squad_configs.items():
                    if config_data["var"].get():  # Se checkbox está marcado
                        try:
                            qty = int(config_data["spinbox"].get())
                            if qty > 0:
                                config = EventSquad(
                                    event_id=self.event_id,
                                    squad_id=squad_id,
                                    quantity=qty,
                                    level=3,  # nível padrão
                                )
                                session.add(config)
                        except ValueError:
                            messagebox.showwarning(
                                "Aviso",
                                f"Valor inválido de quantidade para {config_data['squad_nome']}.",
                            )
                            return

                session.commit()
                messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
                self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")


class ConfigEscalaFrame(tk.Frame):
    """Gerenciador de configuração de eventos com dark theme."""

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
        self._load_eventos()

    def _build_widgets(self):
        """Constrói interface com design dark."""
        # Header
        self._build_header()

        # Frame principal
        main_frame = tk.Frame(self, bg=self._BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview com dark styling
        self._setup_treeview_style()
        colunas = ("Evento", "Tipo", "Configurações")
        self.tree = ttk.Treeview(
            main_frame, columns=colunas, show="headings", height=15, style="ConfigEscala.Treeview"
        )
        self.tree.heading("Evento", text="Evento")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Configurações", text="Configurações")
        self.tree.column("Evento", width=250)
        self.tree.column("Tipo", width=120)
        self.tree.column("Configurações", width=250)

        scroll = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Botões
        self._build_buttons()

    def _build_header(self):
        """Header com ícone e título."""
        header = tk.Frame(self, bg=self._HDR_COL, height=50)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="⚙️  Configuração de Eventos",
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
            "ConfigEscala.Treeview",
            background=self._BG_CARD,
            foreground=self._TXT_PRIMARY,
            fieldbackground=self._BG_CARD,
            borderwidth=0,
        )
        style.map(
            "ConfigEscala.Treeview",
            background=[("selected", self._ACCENT)],
            foreground=[("selected", self._TXT_PRIMARY)],
        )

        style.configure(
            "ConfigEscala.Treeview.Heading",
            background=self._HDR_COL,
            foreground=self._TXT_PRIMARY,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "ConfigEscala.Treeview.Heading",
            background=[("active", self._ACCENT)],
        )

    def _build_buttons(self):
        """Botões de ação com dark theme."""
        btn_frame = tk.Frame(self, bg=self._BG)
        btn_frame.pack(fill="x", padx=10, pady=10)

        buttons = [
            ("⚙️  Configurar Selecionado", self._configure_evento),
            ("🔄 Atualizar", self._load_eventos),
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

    def _load_eventos(self):
        """Carrega lista de eventos."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with session_scope() as session:
                eventos = session.query(Event).order_by(Event.name).all()
                self.eventos_dict = {e.id: e for e in eventos}
                
                for evento in eventos:
                    # Contar configurações (EventSquad)
                    config_count = (
                        session.query(EventSquad)
                        .filter(EventSquad.event_id == evento.id)
                        .count()
                    )
                    config_label = f"{config_count} time(s)"
                    
                    self.tree.insert(
                        "",
                        "end",
                        iid=str(evento.id),
                        values=(evento.name, evento.type.capitalize(), config_label),
                    )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar eventos: {e}")

    def _configure_evento(self):
        """Abre configuração do evento selecionado."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um evento.")
            return

        evento_id = sel[0]  # É uma string UUID
        evento = self.eventos_dict.get(evento_id)
        
        if not evento:
            messagebox.showerror("Erro", "Evento não encontrado.")
            return

        # Abrir diálogo de configuração
        ConfigEventoDialog(self, evento_id, evento.name)
        # Após fechar o diálogo, recarregar para mostrar as atualizações
        self._load_eventos()

    def atualizar_lista(self):
        """Callback acionado por sincronização."""
        self._load_eventos()
