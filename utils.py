# utils.py - Utilitários e Diálogos da Aplicação

import tkinter as tk
from tkinter import messagebox, ttk

from infra.database import Member, Squad, session_scope


def center_popup(window, width=500, height=400):
    """Centraliza uma janela popup na tela."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


class MembroDialog(tk.Toplevel):
    """Diálogo para cadastro/edição de membros."""

    def __init__(self, parent, patentes):
        super().__init__(parent)
        self.title("Cadastro de Membro")
        self.patentes = patentes
        self.result = None
        center_popup(self, 450, 350)

        # Frame principal
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Nome
        ttk.Label(frame, text="Nome:").grid(row=0, column=0, sticky="w", pady=5)
        self.nome = ttk.Entry(frame, width=40)
        self.nome.grid(row=0, column=1, sticky="ew", pady=5)

        # Telefone
        ttk.Label(frame, text="Telefone:").grid(row=1, column=0, sticky="w", pady=5)
        self.phone = ttk.Entry(frame, width=40)
        self.phone.grid(row=1, column=1, sticky="ew", pady=5)

        # Email
        ttk.Label(frame, text="Email:").grid(row=2, column=0, sticky="w", pady=5)
        self.email = ttk.Entry(frame, width=40)
        self.email.grid(row=2, column=1, sticky="ew", pady=5)

        # Instagram
        ttk.Label(frame, text="Instagram:").grid(row=3, column=0, sticky="w", pady=5)
        self.instagram = ttk.Entry(frame, width=40)
        self.instagram.grid(row=3, column=1, sticky="ew", pady=5)

        # Patente
        ttk.Label(frame, text="Patente:").grid(row=4, column=0, sticky="w", pady=5)
        self.patente = ttk.Combobox(frame, values=self.patentes, state="readonly", width=37)
        self.patente.grid(row=4, column=1, sticky="ew", pady=5)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Salvar", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def save(self):
        """Salva os dados."""
        if not self.nome.get():
            messagebox.showwarning("Aviso", "Nome é obrigatório.")
            return

        data = {
            "name": self.nome.get(),
            "phone": self.phone.get() or None,
            "email": self.email.get() or None,
            "instagram": self.instagram.get() or None,
            "patente": self.patente.get() or None,
        }

        messagebox.showinfo("Sucesso", "Membro salvo com sucesso!")
        self.destroy()


class SquadDialog(tk.Toplevel):
    """Diálogo para cadastro/edição de squads."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cadastro de Squad")
        self.result = None
        center_popup(self, 450, 250)

        # Frame principal
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Nome
        ttk.Label(frame, text="Nome da Squad:").grid(row=0, column=0, sticky="w", pady=5)
        self.nome = ttk.Entry(frame, width=40)
        self.nome.grid(row=0, column=1, sticky="ew", pady=5)

        # Descrição
        ttk.Label(frame, text="Descrição:").grid(row=1, column=0, sticky="w", pady=5)
        self.descricao = ttk.Entry(frame, width=40)
        self.descricao.grid(row=1, column=1, sticky="ew", pady=5)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Salvar", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def save(self):
        """Salva os dados."""
        if not self.nome.get():
            messagebox.showwarning("Aviso", "Nome é obrigatório.")
            return

        messagebox.showinfo("Sucesso", "Squad salva com sucesso!")
        self.destroy()


class EventoDialog(tk.Toplevel):
    """Diálogo para cadastro/edição de eventos."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cadastro de Evento")
        self.result = None
        center_popup(self, 500, 350)

        # Frame principal
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Nome
        ttk.Label(frame, text="Nome:").grid(row=0, column=0, sticky="w", pady=5)
        self.nome = ttk.Entry(frame, width=40)
        self.nome.grid(row=0, column=1, sticky="ew", pady=5)

        # Tipo
        ttk.Label(frame, text="Tipo:").grid(row=1, column=0, sticky="w", pady=5)
        self.tipo = ttk.Combobox(
            frame, values=["fixo", "sazonal", "eventual"], state="readonly", width=37
        )
        self.tipo.grid(row=1, column=1, sticky="ew", pady=5)

        # Data (para sazonal/eventual)
        ttk.Label(frame, text="Data (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", pady=5)
        self.data = ttk.Entry(frame, width=40)
        self.data.grid(row=2, column=1, sticky="ew", pady=5)

        # Horário
        ttk.Label(frame, text="Horário (HH:MM):").grid(row=3, column=0, sticky="w", pady=5)
        self.horario = ttk.Entry(frame, width=40)
        self.horario.grid(row=3, column=1, sticky="ew", pady=5)

        # Detalhes
        ttk.Label(frame, text="Detalhes:").grid(row=4, column=0, sticky="w", pady=5)
        self.detalhes = ttk.Entry(frame, width=40)
        self.detalhes.grid(row=4, column=1, sticky="ew", pady=5)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Salvar", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def save(self):
        """Salva os dados."""
        if not self.nome.get():
            messagebox.showwarning("Aviso", "Nome é obrigatório.")
            return

        messagebox.showinfo("Sucesso", "Evento salvo com sucesso!")
        self.destroy()
