"""Testes E2E de fumaça — verifica que o app abre e as telas principais navegam.

Estratégia:
- app_process sobe o app uma vez (scope=session)
- app_window foca a janela antes de cada teste
- pyautogui.click() com coordenadas relativas à geometria da janela
- Sidebar: 200px de largura, header ~110px, botões ~40px cada (pady=1)
"""

import time
from tests.e2e.conftest import e2e_wait

import pyautogui
import pytest


APP_TITLE = "Sistema de Escala - Time da Mídia"

# Posição Y estimada de cada botão da sidebar (relativa ao topo da janela).
# Header ocupa ~110px; cada botão tem ~40px de altura com pady=1.
_SIDEBAR_BTN_X_OFFSET = 100  # centro horizontal da sidebar (largura 200px)
_SIDEBAR_BTN_Y_START = 130    # topo do primeiro botão
_SIDEBAR_BTN_HEIGHT = 42      # altura total de cada botão

SIDEBAR_LABELS = [
    "Visualizar",
    "Membros",
    "Times",
    "Eventos",
    "Escalas",
    "Casais",
    "Config",
    "Disponibilidade",
]


class TestAppInicia:
    """O app deve iniciar e exibir a janela principal."""

    def test_janela_abre(self, app_window):
        """Janela com título correto está visível."""
        assert APP_TITLE in app_window.title

    def test_janela_tem_tamanho_minimo(self, app_window):
        """Janela respeita o tamanho mínimo configurado (900x550)."""
        assert app_window.width >= 900
        assert app_window.height >= 550


class TestNavegacaoSidebar:
    """Clicar nos botões da sidebar deve trocar de tela sem travar."""

    def test_navegacao_completa(self, app_window):
        """Percorre todos os botões da sidebar sem que o app trave ou feche."""
        for index in range(len(SIDEBAR_LABELS)):
            _click_sidebar_button_by_index(app_window, index)
            e2e_wait(0.4)
        assert _app_window_still_open(), "App fechou inesperadamente durante navegação"

    def test_volta_para_primeira_tela(self, app_window):
        """Após navegar para o fim da lista, consegue voltar ao início."""
        last = len(SIDEBAR_LABELS) - 1
        _click_sidebar_button_by_index(app_window, last)
        e2e_wait(0.3)
        _click_sidebar_button_by_index(app_window, 0)
        e2e_wait(0.3)
        assert _app_window_still_open()

    def test_screenshot_capturado_apos_navegacao(self, app_window):
        """Após navegar para Membros, a janela deve continuar visível e com dimensões corretas."""
        _click_sidebar_button_by_index(app_window, 1)  # "Membros"
        e2e_wait(0.5)
        from tests.e2e.conftest import _get_window_geometry
        win = _get_window_geometry(APP_TITLE)
        assert win is not None, "App fechou ao navegar para Membros"
        assert win.width >= 900 and win.height >= 550


# ---------------------------------------------------------------------------
# Helpers de interação
# ---------------------------------------------------------------------------

def _click_sidebar_button_by_index(app_window, index: int) -> None:
    """Clica no botão da sidebar pelo índice (0 = primeiro item).

    Calcula as coordenadas absolutas baseando-se na posição atual da janela
    e no layout fixo da sidebar (200px largura, botões ~42px).
    """
    x = app_window.left + _SIDEBAR_BTN_X_OFFSET
    y = app_window.top + _SIDEBAR_BTN_Y_START + index * _SIDEBAR_BTN_HEIGHT
    pyautogui.click(x, y)


def _app_window_still_open() -> bool:
    """Retorna True se a janela principal ainda estiver aberta."""
    from tests.e2e.conftest import _get_window_geometry
    return _get_window_geometry(APP_TITLE) is not None
