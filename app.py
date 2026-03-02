# app.py - Ponto de entrada da aplicação
import tkinter as tk

from gui.main_window import SistemaEscalaApp
from gui.membros import MembrosFrame
from gui.squads import SquadsFrame
from gui.eventos_orm import EventosFrame
from gui.gerar_escala import GerarEscalaFrame
from gui.visualizar import VisualizarFrame
from gui.casais_orm import CasaisFrame
from gui.config_escala_orm import ConfigEscalaFrame
from gui.disponibilidade_orm import DisponibilidadeFrame

from infra.database import create_tables

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaEscalaApp(root)

    create_tables()

    # Visualizar primeiro (dashboard)
    app.register_frame("Visualizar", VisualizarFrame(app.content))
    app.register_frame("Membros", MembrosFrame(app.content))
    app.register_frame("Times", SquadsFrame(app.content))
    app.register_frame("Eventos", EventosFrame(app.content))
    app.register_frame("Escalas", GerarEscalaFrame(app.content, app))
    app.register_frame("Casais", CasaisFrame(app.content))
    app.register_frame("Config", ConfigEscalaFrame(app.content))
    app.register_frame("Disponibilidade", DisponibilidadeFrame(app.content))

    app.sincronizar()
    root.mainloop()
