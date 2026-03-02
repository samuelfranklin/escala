import csv
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog, messagebox, ttk

from services.visualizar_service import VisualizarService


class VisualizarFrame(tk.Frame):
    """Dashboard principal: visualizar escala gerada com dark theme."""

    # Paleta de cores (sincronizada com main_window.py)
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
        self.service = VisualizarService()  # Injetar service
        self.escala_atual = []  # armazena a última escala gerada
        self._build_widgets()

    def _build_widgets(self):
        """Constrói interface com design dark."""
        # Header
        self._build_header()

        # Frame principal da escala
        main_frame = tk.Frame(self, bg=self._BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview com dark styling
        self._setup_treeview_style()
        colunas = ("Data", "Dia", "Evento", "Horário", "Squad", "Voluntário")
        self.tree = ttk.Treeview(
            main_frame,
            columns=colunas,
            show="headings",
            height=20,
            style="Visualizar.Treeview",
        )

        for col in colunas:
            self.tree.heading(col, text=col)
            if col == "Voluntário":
                self.tree.column(col, width=300)
            elif col == "Evento":
                self.tree.column(col, width=200)
            else:
                self.tree.column(col, width=100)

        scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(
            main_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

    def _build_header(self):
        """Header com ícone, título e botões de ação à direita."""
        header = tk.Frame(self, bg=self._HDR_COL, height=50)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Título à esquerda
        title_label = tk.Label(
            header,
            text="📊  Visualizar Escala",
            font=("Segoe UI", 14, "bold"),
            bg=self._HDR_COL,
            fg=self._TXT_PRIMARY,
        )
        title_label.pack(side="left", padx=15, pady=10)

        # Frame para botões de ação à direita
        btn_frame = tk.Frame(header, bg=self._HDR_COL)
        btn_frame.pack(side="right", padx=10, pady=5)

        # Botões de ação
        buttons = [
            ("💾 TXT", self.exportar_txt),
            ("📋 CSV", self.exportar_csv),
            ("🗑️  Limpar", self.limpar),
            ("🔄", self.atualizar_treeview),
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
                padx=10,
                pady=5,
            )
            btn.pack(side="left", padx=3)

    def _setup_treeview_style(self):
        """Configura estilo dark para a Treeview."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configurar cores da Treeview para dark theme
        style.configure(
            "Visualizar.Treeview",
            background=self._BG_CARD,
            foreground=self._TXT_PRIMARY,
            fieldbackground=self._BG_CARD,
            borderwidth=0,
        )
        style.map(
            "Visualizar.Treeview",
            background=[("selected", self._ACCENT)],
            foreground=[("selected", self._TXT_PRIMARY)],
        )

        # Header da Treeview
        style.configure(
            "Visualizar.Treeview.Heading",
            background=self._HDR_COL,
            foreground=self._TXT_PRIMARY,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Visualizar.Treeview.Heading",
            background=[("active", self._ACCENT)],
        )

    def set_escala(self, escala):
        """
        Recebe a escala gerada (lista de dicionários) e atualiza a treeview.
        Cada item do dicionário deve conter:
            'data', 'dia', 'evento', 'horario', 'squad', 'membro'
        """
        self.escala_atual = escala
        self.atualizar_treeview()

    def atualizar_treeview(self):
        """Atualiza treeview com dados da escala."""
        # Limpa a treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere os itens da escala
        for item in self.escala_atual:
            self.tree.insert(
                "",
                "end",
                values=(
                    item["data"],
                    item["dia"],
                    item["evento"],
                    item["horario"],
                    item["squad"],
                    item["membro"],
                ),
            )

    def atualizar_lista(self):
        """Callback acionado por sincronização: carrega escala do banco."""
        import datetime
        
        try:
            hoje = datetime.date.today()
            schedule = self.service.get_schedule_for_period(hoje.month, hoje.year)
            # Converte dados do service para formato esperado (com 'membro')
            for item in schedule:
                item.setdefault('membro', '')  # Placeholder se não houver membro
            self.set_escala(schedule)
        except Exception as e:
            messagebox.showerror("Erro ao carregar escala", str(e))

    def filtrar_por_squad(self, squad_id: str):
        """Filtra e carrega alocações de um squad específico."""
        try:
            allocations = self.service.get_squad_allocations(squad_id)
            # Converte para formato esperado
            for item in allocations:
                item.setdefault('membro', '')
            self.set_escala(allocations)
        except Exception as e:
            messagebox.showerror("Erro ao filtrar por squad", str(e))

    def filtrar_por_membro(self, member_id: str):
        """Filtra e carrega alocações de um membro específico."""
        try:
            allocations = self.service.get_member_allocations(member_id)
            # Converte para formato esperado
            for item in allocations:
                item.setdefault('squad', '')
            self.set_escala(allocations)
        except Exception as e:
            messagebox.showerror("Erro ao filtrar por membro", str(e))

    def limpar(self):
        """Limpa a treeview e dados da escala."""
        self.escala_atual = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        messagebox.showinfo("Limpeza", "Escala limpa com sucesso.")

    def exportar_txt(self):
        """Exporta escala em formato TXT organizado por data/evento/squad."""
        if not self.escala_atual:
            messagebox.showwarning("Aviso", "Nenhuma escala para exportar.")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Arquivo de texto", "*.txt")]
        )
        if not arquivo:
            return

        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write("ESCALA DO TIME DA MÍDIA\n")
                f.write("=" * 60 + "\n\n")

                # Agrupar por data
                por_data = defaultdict(list)
                for item in self.escala_atual:
                    por_data[item["data"]].append(item)

                for data in sorted(por_data.keys()):
                    f.write(f"\n{data} - {por_data[data][0]['dia']}\n")
                    f.write("-" * 40 + "\n")

                    # Agrupar por evento
                    por_evento = defaultdict(list)
                    for item in por_data[data]:
                        por_evento[item["evento"]].append(item)

                    for evento, itens_evento in por_evento.items():
                        f.write(f"\n  Evento: {evento} ({itens_evento[0]['horario']})\n")

                        # Agrupar por squad
                        por_squad = defaultdict(list)
                        for item in itens_evento:
                            por_squad[item["squad"]].append(item.get("membro", ""))

                        for squad, membros in por_squad.items():
                            f.write(f"    {squad}:\n")
                            for membro in membros:
                                f.write(f"      • {membro}\n")

            messagebox.showinfo("Exportação", f"Escala exportada para {arquivo}")
        except IOError as e:
            messagebox.showerror("Erro de exportação", f"Não foi possível salvar o arquivo: {str(e)}")

    def exportar_csv(self):
        """Exporta escala em formato CSV."""
        if not self.escala_atual:
            messagebox.showwarning("Aviso", "Nenhuma escala para exportar.")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("Arquivo CSV", "*.csv")]
        )
        if not arquivo:
            return

        try:
            with open(arquivo, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Data", "Dia", "Evento", "Horário", "Squad", "Voluntário"])
                for item in self.escala_atual:
                    writer.writerow(
                        [
                            item.get("data", ""),
                            item.get("dia", ""),
                            item.get("evento", ""),
                            item.get("horario", ""),
                            item.get("squad", ""),
                            item.get("membro", ""),
                        ]
                    )

            messagebox.showinfo("Exportação", f"Escala exportada para {arquivo}")
        except IOError as e:
            messagebox.showerror("Erro de exportação", f"Não foi possível salvar o arquivo: {str(e)}")
