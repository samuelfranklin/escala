"""Helpers de navegação para testes E2E.

Extrai os helpers de sidebar/conteúdo usados nos smoke tests para reutilização.
"""

import time
import pyautogui

from tests.e2e.conftest import WindowGeometry

# Sidebar
SIDEBAR_BTN_X_OFFSET = 100   # centro horizontal da sidebar (largura 200px)
SIDEBAR_BTN_Y_START = 130    # topo do primeiro botão
SIDEBAR_BTN_HEIGHT = 42      # altura de cada botão

# Mapeamento de nome de tela → índice na sidebar
SIDEBAR_INDEX = {
    "Visualizar": 0,
    "Membros": 1,
    "Times": 2,
    "Eventos": 3,
    "Escalas": 4,
    "Casais": 5,
    "Config": 6,
    "Disponibilidade": 7,
}

# Botão "+" na área de conteúdo (header da tela)
# O botão ＋ é o mais à esquerda do grupo de botões alinhados à direita.
# Calculado como win.width - 130 para se adaptar ao tamanho real da janela.
_ADD_BTN_RIGHT_MARGIN = 130  # distância do botão ＋ ao lado direito da janela
ADD_BTN_Y_OFFSET = 75        # Y: decoração WM (~32) + menu (~21) + metade do header (~22)


def click_sidebar(win: WindowGeometry, index: int, wait: float = 0.5) -> None:
    """Clica no botão da sidebar no índice dado."""
    x = win.left + SIDEBAR_BTN_X_OFFSET
    y = win.top + SIDEBAR_BTN_Y_START + index * SIDEBAR_BTN_HEIGHT
    pyautogui.click(x, y)
    time.sleep(wait)


def navigate_to(win: WindowGeometry, screen_name: str, wait: float = 0.5) -> None:
    """Navega para uma tela pelo nome (ex.: 'Membros', 'Times')."""
    index = SIDEBAR_INDEX[screen_name]
    click_sidebar(win, index, wait=wait)


def click_add_button(win: WindowGeometry, wait: float = 0.6) -> None:
    """Clica no botão '+' da área de conteúdo da tela atual."""
    x = win.left + win.width - _ADD_BTN_RIGHT_MARGIN
    y = win.top + ADD_BTN_Y_OFFSET
    pyautogui.click(x, y)
    time.sleep(wait)


def click_at_offset(win: WindowGeometry, x_offset: int, y_offset: int,
                    wait: float = 0.3) -> None:
    """Clica em uma posição relativa ao canto superior esquerdo da janela."""
    x = win.left + x_offset
    y = win.top + y_offset
    pyautogui.click(x, y)
    time.sleep(wait)
