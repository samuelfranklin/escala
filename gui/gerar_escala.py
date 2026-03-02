import logging
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from services.escala_service import EscalaService

logger = logging.getLogger(__name__)


class GerarEscalaFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.service = EscalaService()
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
        """Gera escala usando EscalaService."""
        try:
            mes = int(self.mes.get())
            ano = int(self.ano.get())
        except Exception:
            messagebox.showerror("Erro", "Mês/Ano inválidos.")
            return

        # Chamada única ao serviço
        sucesso, mensagem, escala = self.service.generate_schedule(
            month=mes,
            year=ano,
            respect_couples=self.var_respeitar_casais.get(),
            balance_distribution=self.var_equilibrio.get(),
        )

        # Mostrar resultado
        if sucesso:
            # Se há aviso de conflitos, mostrar como warning
            if "Conflitos" in mensagem or "precisa" in mensagem:
                messagebox.showwarning("Aviso", mensagem)
            else:
                messagebox.showinfo("Sucesso", mensagem)
        else:
            messagebox.showerror("Erro", mensagem)
            return

        # Passar escala para visualização
        if escala:
            if hasattr(self.app, "frames") and "Visualizar" in self.app.frames:
                self.app.frames["Visualizar"].set_escala(escala)
            else:
                self.escala = escala


