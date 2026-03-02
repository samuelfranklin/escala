import tkinter as tk
from tkinter import messagebox, ttk

from infra.database import create_tables


class SistemaEscalaApp:
    # ------------------------------------------------------------------
    # Paleta de cores
    # ------------------------------------------------------------------
    _CLR_SIDEBAR_BG = "#1e2533"
    _CLR_SIDEBAR_HDR = "#151b27"
    _CLR_BTN_NORMAL = "#1e2533"
    _CLR_BTN_HOVER = "#2a3347"
    _CLR_BTN_ACTIVE = "#4f7ef8"
    _CLR_BTN_FG = "#a8b2c8"
    _CLR_BTN_ACTIVE_FG = "#ffffff"
    _CLR_CONTENT_BG = "#f0f2f7"
    _CLR_SEPARATOR = "#2e3650"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sistema de Escala - Time da Mídia")
        self.root.geometry("1200x700")
        self.root.minsize(900, 550)
        self.root.resizable(True, True)

        create_tables()

        self._active_label: str | None = None
        self.frames: dict[str, ttk.Frame] = {}
        self._buttons: dict[str, tk.Button] = {}

        self._build_menu()
        self._build_layout()

    # ------------------------------------------------------------------
    # Menu superior
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        arquivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=arquivo_menu)
        arquivo_menu.add_command(label="Backup Banco", command=self._backup_banco)
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label="Sair", command=self.root.quit)

        menubar.add_command(label="Sincronizar", command=self.sincronizar)

    # ------------------------------------------------------------------
    # Layout principal: sidebar + área de conteúdo
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        # Container raiz
        self._main = tk.Frame(self.root, bg=self._CLR_CONTENT_BG)
        self._main.pack(fill="both", expand=True)

        # ── Sidebar ──────────────────────────────────────────────────
        self._sidebar = tk.Frame(
            self._main,
            bg=self._CLR_SIDEBAR_BG,
            width=200,
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Cabeçalho / logo texto
        header = tk.Frame(self._sidebar, bg=self._CLR_SIDEBAR_HDR)
        header.pack(fill="x")

        tk.Label(
            header,
            text="🎬",
            font=("Segoe UI Emoji", 28),
            bg=self._CLR_SIDEBAR_HDR,
            fg="#ffffff",
            pady=14,
        ).pack()

        tk.Label(
            header,
            text="ESCALA MÍDIA",
            font=("Segoe UI", 10, "bold"),
            bg=self._CLR_SIDEBAR_HDR,
            fg="#4f7ef8",
            pady=0,
            padx=12,
        ).pack(fill="x")

        tk.Label(
            header,
            text="Time da Mídia",
            font=("Segoe UI", 8),
            bg=self._CLR_SIDEBAR_HDR,
            fg="#6b7a99",
            pady=8,
        ).pack()

        # Linha separadora
        tk.Frame(self._sidebar, bg=self._CLR_SEPARATOR, height=1).pack(
            fill="x", padx=0, pady=0
        )

        # Área de botões de navegação (scrollable se necessário)
        self._nav_frame = tk.Frame(self._sidebar, bg=self._CLR_SIDEBAR_BG)
        self._nav_frame.pack(fill="both", expand=True, pady=8)

        # Rodapé da sidebar
        tk.Frame(self._sidebar, bg=self._CLR_SEPARATOR, height=1).pack(fill="x")
        tk.Label(
            self._sidebar,
            text="v1.0",
            font=("Segoe UI", 8),
            bg=self._CLR_SIDEBAR_BG,
            fg="#3a4460",
            pady=8,
        ).pack()

        # ── Área de conteúdo ─────────────────────────────────────────
        self.content = tk.Frame(self._main, bg=self._CLR_CONTENT_BG)
        self.content.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------------
    # Registro de frames (interface pública)
    # ------------------------------------------------------------------

    def register_frame(
        self, label: str, frame: ttk.Frame, *, sidebar: bool = True
    ) -> None:
        """Registra um frame na área de conteúdo e, opcionalmente, na sidebar.

        O ``frame`` deve ter ``self.content`` como widget pai para que
        o posicionamento via ``place`` funcione corretamente.

        Args:
            label: Chave/texto do frame. Quando ``sidebar=True`` também é o
                   texto exibido no botão de navegação.
            frame: Instância do frame já construída.
            sidebar: Se ``True`` (padrão), cria um botão de navegação na
                     sidebar. Se ``False``, o frame fica acessível via
                     ``self.frames[label]`` mas não aparece no menu lateral
                     (útil para frames auxiliares como o de visualização de
                     escala).
        """
        # Empilha o frame na área de conteúdo
        frame.place(in_=self.content, x=0, y=0, relwidth=1, relheight=1)
        self.frames[label] = frame

        if not sidebar:
            return

        # Cria o botão na sidebar
        btn = tk.Button(
            self._nav_frame,
            text=f"  {label}",
            font=("Segoe UI", 10),
            bg=self._CLR_BTN_NORMAL,
            fg=self._CLR_BTN_FG,
            activebackground=self._CLR_BTN_HOVER,
            activeforeground=self._CLR_BTN_ACTIVE_FG,
            relief="flat",
            bd=0,
            padx=16,
            pady=10,
            anchor="w",
            cursor="hand2",
            command=lambda lbl=label: self._show_frame(lbl),
        )
        btn.pack(fill="x", padx=6, pady=1)

        # Efeitos de hover
        btn.bind("<Enter>", lambda e, b=btn, lbl=label: self._on_hover(b, lbl))
        btn.bind("<Leave>", lambda e, b=btn, lbl=label: self._on_leave(b, lbl))

        self._buttons[label] = btn

        # Exibe o primeiro frame registrado automaticamente
        if self._active_label is None:
            self._show_frame(label)

    # ------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------

    def _show_frame(self, label: str) -> None:
        """Traz o frame correspondente ao label para frente."""
        # Remove destaque do botão anterior
        if self._active_label and self._active_label in self._buttons:
            prev = self._buttons[self._active_label]
            prev.config(bg=self._CLR_BTN_NORMAL, fg=self._CLR_BTN_FG)

        # Levanta o frame
        self.frames[label].tkraise()
        self._active_label = label

        # Destaca o botão ativo com borda esquerda colorida via indicador
        self._buttons[label].config(
            bg=self._CLR_BTN_ACTIVE,
            fg=self._CLR_BTN_ACTIVE_FG,
        )

    def _on_hover(self, btn: tk.Button, label: str) -> None:
        if label != self._active_label:
            btn.config(bg=self._CLR_BTN_HOVER, fg=self._CLR_BTN_ACTIVE_FG)

    def _on_leave(self, btn: tk.Button, label: str) -> None:
        if label != self._active_label:
            btn.config(bg=self._CLR_BTN_NORMAL, fg=self._CLR_BTN_FG)

    # ------------------------------------------------------------------
    # Ações de menu
    # ------------------------------------------------------------------

    def _backup_banco(self) -> None:
        import os
        import shutil
        from datetime import datetime

        from infra.database import DATABASE_URL

        if not DATABASE_URL.startswith("sqlite:///"):
            messagebox.showwarning(
                "Backup",
                "Backup automático só é suportado para bancos SQLite locais.",
            )
            return

        db_path = DATABASE_URL.replace("sqlite:///", "", 1)
        if not os.path.exists(db_path):
            messagebox.showwarning(
                "Backup", "Arquivo de banco de dados não encontrado."
            )
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backup_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        messagebox.showinfo("Backup", f"Backup salvo em: {backup_path}")

    def sincronizar(self) -> None:
        """Atualiza todos os frames que implementem ``atualizar_lista``."""
        for frame in self.frames.values():
            if hasattr(frame, "atualizar_lista"):
                frame.atualizar_lista()  # type: ignore[union-attr]
