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

    def __init__(self, parent, patentes, nome="", email="", telefone="",
                 patente="", data_entrada="", obs="", edicao=False):
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
        if nome:
            self.nome.insert(0, nome)

        # Telefone
        ttk.Label(frame, text="Telefone:").grid(row=1, column=0, sticky="w", pady=5)
        self.phone = ttk.Entry(frame, width=40)
        self.phone.grid(row=1, column=1, sticky="ew", pady=5)
        if telefone:
            self.phone.insert(0, telefone)

        # Email
        ttk.Label(frame, text="Email:").grid(row=2, column=0, sticky="w", pady=5)
        self.email = ttk.Entry(frame, width=40)
        self.email.grid(row=2, column=1, sticky="ew", pady=5)
        if email:
            self.email.insert(0, email)

        # Instagram
        ttk.Label(frame, text="Instagram:").grid(row=3, column=0, sticky="w", pady=5)
        self.instagram = ttk.Entry(frame, width=40)
        self.instagram.grid(row=3, column=1, sticky="ew", pady=5)

        # Patente
        ttk.Label(frame, text="Patente:").grid(row=4, column=0, sticky="w", pady=5)
        self.patente = ttk.Combobox(frame, values=self.patentes, state="readonly", width=37)
        self.patente.grid(row=4, column=1, sticky="ew", pady=5)
        if patente and patente in self.patentes:
            self.patente.set(patente)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Salvar", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

        # Bloqueia o parent até o dialog fechar (comportamento modal)
        self.grab_set()
        self.wait_window(self)

    def save(self):
        """Salva os dados e fecha o dialog."""
        if not self.nome.get():
            messagebox.showwarning("Aviso", "Nome é obrigatório.")
            return

        self.result = (
            self.nome.get(),
            self.email.get(),
            self.phone.get(),
            self.patente.get() if hasattr(self, "patente") else "",
            "",  # data_entrada (não implementado)
            "",  # obs (não implementado)
        )
        self.destroy()


class SquadDialog(tk.Toplevel):
    """Diálogo para cadastro/edição de squads."""

    def __init__(self, parent, title="Cadastro de Squad", nome="", desc=""):
        super().__init__(parent)
        self.title(title)
        self.result = None
        center_popup(self, 450, 250)

        # Frame principal
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Nome
        ttk.Label(frame, text="Nome da Squad:").grid(row=0, column=0, sticky="w", pady=5)
        self.nome = ttk.Entry(frame, width=40)
        self.nome.grid(row=0, column=1, sticky="ew", pady=5)
        if nome:
            self.nome.insert(0, nome)

        # Descrição
        ttk.Label(frame, text="Descrição:").grid(row=1, column=0, sticky="w", pady=5)
        self.descricao = ttk.Entry(frame, width=40)
        self.descricao.grid(row=1, column=1, sticky="ew", pady=5)
        if desc:
            self.descricao.insert(0, desc)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Salvar", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

        # Bloqueia o parent até o dialog fechar (comportamento modal)
        self.grab_set()
        self.wait_window(self)

    def save(self):
        """Salva os dados e fecha o dialog."""
        if not self.nome.get():
            messagebox.showwarning("Aviso", "Nome é obrigatório.")
            return

        self.result = (self.nome.get(), self.descricao.get())
        self.destroy()


class EventoDialog(tk.Toplevel):
    """Diálogo para cadastro/edição de eventos."""

    def __init__(
        self,
        parent,
        title="Cadastro de Evento",
        nome="",
        tipo="",
        dia="",
        data="",
        horario="",
        descricao="",
    ):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.dialog = self
        center_popup(self, 500, 350)

        # Frame principal
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Nome
        ttk.Label(frame, text="Nome:").grid(row=0, column=0, sticky="w", pady=5)
        self.nome = ttk.Entry(frame, width=40)
        self.nome.grid(row=0, column=1, sticky="ew", pady=5)
        if nome:
            self.nome.insert(0, nome)

        # Tipo
        ttk.Label(frame, text="Tipo:").grid(row=1, column=0, sticky="w", pady=5)
        self.tipo = ttk.Combobox(
            frame, values=["fixo", "sazonal", "eventual"], state="readonly", width=37
        )
        self.tipo.grid(row=1, column=1, sticky="ew", pady=5)
        if tipo:
            self.tipo.set(tipo)

        # Dia (para fixo)
        ttk.Label(frame, text="Dia da Semana:").grid(row=2, column=0, sticky="w", pady=5)
        self.dia = ttk.Combobox(
            frame,
            values=["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", 
                   "Quinta-feira", "Sexta-feira", "Sábado"],
            state="readonly",
            width=37
        )
        self.dia.grid(row=2, column=1, sticky="ew", pady=5)
        if dia:
            self.dia.set(dia)
        else:
            self.dia.set("Domingo")

        # Data (para sazonal/eventual)
        ttk.Label(frame, text="Data (DD/MM/YYYY):").grid(row=3, column=0, sticky="w", pady=5)
        self.data = ttk.Entry(frame, width=40)
        self.data.grid(row=3, column=1, sticky="ew", pady=5)
        if data:
            self.data.insert(0, data)

        # Horário
        ttk.Label(frame, text="Horário (HH:MM):").grid(row=4, column=0, sticky="w", pady=5)
        self.horario = ttk.Entry(frame, width=40)
        self.horario.grid(row=4, column=1, sticky="ew", pady=5)
        if horario:
            self.horario.insert(0, horario)

        # Detalhes
        ttk.Label(frame, text="Detalhes:").grid(row=5, column=0, sticky="w", pady=5)
        self.detalhes = ttk.Entry(frame, width=40)
        self.detalhes.grid(row=5, column=1, sticky="ew", pady=5)
        if descricao:
            self.detalhes.insert(0, descricao)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Salvar", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def save(self):
        """Salva os dados."""
        if not self.nome.get():
            messagebox.showwarning("Aviso", "Nome é obrigatório.")
            return

        # Retornar tupla (nome, tipo, dia, data, horario, descricao)
        self.result = (
            self.nome.get(),
            self.tipo.get(),
            self.dia.get(),
            self.data.get(),
            self.horario.get(),
            self.detalhes.get(),
        )
        self.destroy()
