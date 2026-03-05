"""Helpers para interagir com dialogs modais via pyautogui.

Cada função espera que o dialog já esteja aberto (detectado via Xlib)
e interage com ele por coordenadas relativas ao dialog.
"""

import time
import pyautogui
from typing import Optional

from tests.e2e.conftest import WindowGeometry, _get_window_geometry, e2e_wait


def wait_for_dialog(title: str, timeout: float = 5.0) -> Optional[WindowGeometry]:
    """Aguarda que um dialog com o título dado apareça e o retorna."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        win = _get_window_geometry(title)
        if win is not None and win.width > 100:
            time.sleep(0.2)  # estabilizar antes de interagir
            return win
        time.sleep(0.2)
    return None


def dismiss_messagebox(wait: float = 0.4) -> None:
    """Fecha uma messagebox (showinfo/showwarning) pressionando Enter."""
    pyautogui.press("enter")
    time.sleep(wait)


def dismiss_any_dialog(wait: float = 0.4) -> None:
    """Tenta fechar qualquer dialog ativo (Enter + Escape)."""
    pyautogui.press("enter")
    time.sleep(0.1)
    pyautogui.press("escape")
    time.sleep(wait)


def fill_membro_dialog(name: str) -> bool:
    """Preenche e salva o MembroDialog ('Cadastro de Membro').

    Retorna True se o dialog foi encontrado e preenchido.
    """
    dlg = wait_for_dialog("Cadastro de Membro")
    if dlg is None:
        return False

    # O campo Nome é a 1ª Entry do formulário.
    # Posição: decoração WM (~32px) + padding frame (15px) + pady (5px) + metade entry (~11px) ≈ 63px
    nome_x = dlg.left + dlg.width // 2 + 30
    nome_y = dlg.top + 63
    pyautogui.click(nome_x, nome_y)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite(name, interval=0.05)
    e2e_wait(0.2)

    # Botão Salvar — row 5 com pady=20
    # Y ≈ decoração(32) + padding(15) + 5 linhas × 32px + pady(20) + metade botão(12) ≈ 239px
    salvar_x = dlg.left + dlg.width // 2 - 50
    salvar_y = dlg.top + 239
    pyautogui.click(salvar_x, salvar_y)
    e2e_wait(0.3)
    return True


def fill_squad_dialog(name: str) -> bool:
    """Preenche e salva o SquadDialog ('Cadastro de Squad').

    Retorna True se o dialog foi encontrado e preenchido.
    """
    dlg = wait_for_dialog("Cadastro de Squad")
    if dlg is None:
        # Tenta título alternativo (modo edição)
        dlg = wait_for_dialog("Adicionar Time")
    if dlg is None:
        return False

    # Campo Nome da Squad (row 0)
    # Y ≈ decoração(32) + padding(15) + pady(5) + metade entry(11) ≈ 63px
    nome_x = dlg.left + dlg.width // 2 + 20
    nome_y = dlg.top + 63
    pyautogui.click(nome_x, nome_y)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite(name, interval=0.05)
    e2e_wait(0.2)

    # Botão Salvar — row 2 com pady=20
    # Y ≈ 32 + 15 + 2 linhas × 32px + 20 + 12 ≈ 143px
    salvar_x = dlg.left + dlg.width // 2 - 40
    salvar_y = dlg.top + 143
    pyautogui.click(salvar_x, salvar_y)
    e2e_wait(0.3)
    return True


def fill_evento_dialog(
    name: str,
    tipo: str = "fixo",
    dia: str = "Domingo",
    horario: str = "09:00",
) -> bool:
    """Preenche e salva o EventoDialog ('Novo Evento').

    tipo: 'fixo', 'sazonal' ou 'eventual'
    dia: 'Domingo', 'Segunda-feira', etc. (usado quando tipo='fixo')
    Retorna True se o dialog foi encontrado e preenchido.
    """
    dlg = wait_for_dialog("Novo Evento")
    if dlg is None:
        dlg = wait_for_dialog("Cadastro de Evento")
    if dlg is None:
        return False

    # Layout (decoração WM ~32 + frame padding 15 + pady 5 + metade widget):
    # Row 0 Nome Entry: y ≈ 32+15+5+11 = 63
    # Row 1 Tipo Combobox: y ≈ 63+32 = 95
    # Row 2 Dia Combobox: y ≈ 95+32 = 127
    # Row 4 Horário Entry: y ≈ 127+32+32 = 191
    # Row 6 Buttons (pady=20): y ≈ 191+32+32+20+12 = 287

    # Campo Nome (row 0)
    nome_x = dlg.left + dlg.width // 2 + 30
    nome_y = dlg.top + 63
    pyautogui.click(nome_x, nome_y)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite(name, interval=0.05)
    e2e_wait(0.2)

    # Tipo Combobox (row 1)
    tipo_x = dlg.left + dlg.width // 2 + 30
    tipo_y = dlg.top + 95
    pyautogui.click(tipo_x, tipo_y)
    time.sleep(0.3)
    tipo_map = {"fixo": 0, "sazonal": 1, "eventual": 2}
    for _ in range(tipo_map.get(tipo, 0)):
        pyautogui.press("down")
        time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(0.2)

    # Dia da Semana Combobox (row 2) — só relevante para tipo=fixo
    if tipo == "fixo":
        dia_map = {
            "Domingo": 0, "Segunda-feira": 1, "Terça-feira": 2,
            "Quarta-feira": 3, "Quinta-feira": 4, "Sexta-feira": 5, "Sábado": 6,
        }
        dia_x = dlg.left + dlg.width // 2 + 30
        dia_y = dlg.top + 127
        pyautogui.click(dia_x, dia_y)
        time.sleep(0.3)
        for _ in range(dia_map.get(dia, 0)):
            pyautogui.press("down")
            time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.2)

    # Horário (row 4)
    hora_x = dlg.left + dlg.width // 2 + 30
    hora_y = dlg.top + 191
    pyautogui.click(hora_x, hora_y)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite(horario, interval=0.05)
    e2e_wait(0.2)

    # Botão Salvar (row 6, pady=20)
    salvar_x = dlg.left + dlg.width // 2 - 30
    salvar_y = dlg.top + 287
    pyautogui.click(salvar_x, salvar_y)
    e2e_wait(0.4)

    # Fecha messagebox de sucesso (eventos_orm.py mostra uma)
    dismiss_messagebox()
    return True


def fill_config_evento_dialog(squad_name: str, quantidade: int = 1) -> bool:
    """Preenche o ConfigEventoDialog selecionando um squad e definindo a quantidade.

    O dialog tem título 'Configurar: {nome_evento}'.
    Retorna True se o dialog foi encontrado.
    """
    # Busca por título parcial 'Configurar:'
    dlg = wait_for_dialog("Configurar:")
    if dlg is None:
        return False

    # O dialog exibe uma lista de squads com Checkbutton e Spinbox por linha
    # Estratégia: Tab até encontrar o campo correto ou clicar por posição estimada
    # Linha de squad: ~80px do topo + 35px por squad index
    # Para simplificar TDD-RED: pressiona Tab para navegar e Space para checar
    # Foca o dialog e usa Tab + Space para marcar o primeiro squad
    pyautogui.click(dlg.left + dlg.width // 2, dlg.top + 80)
    time.sleep(0.3)
    pyautogui.press("space")  # marca o primeiro Checkbutton
    time.sleep(0.2)

    # Tab para o Spinbox de quantidade
    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite(str(quantidade), interval=0.05)
    e2e_wait(0.2)

    # Botão Salvar
    salvar_x = dlg.left + dlg.width // 2 - 50
    salvar_y = dlg.top + dlg.height - 45
    pyautogui.click(salvar_x, salvar_y)
    e2e_wait(0.4)

    # Fecha messagebox de sucesso se aparecer
    dismiss_messagebox()
    return True
