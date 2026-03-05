"""Testes E2E para o fluxo de gerenciamento de membros.

Estratégia de coordenadas:
- Janela Tkinter: 1200x700 client area + ~32px decoração = altura real ~732px
- Sidebar: 200px de largura  
- Content area: começa em x=200, ocupa ~1000px horizontalmente
- Header da tela Membros: ~45px de altura, botões alinhados à direita
- Botão "＋": último à direita, estimado em x_offset=1150, y_offset=80
"""

import time
from tests.e2e.conftest import e2e_wait

import pyautogui
import pytest

from tests.e2e.conftest import _get_window_geometry, _dismiss_dialogs

APP_TITLE = "Sistema de Escala - Time da Mídia"
DIALOG_TITLE = "Cadastro de Membro"

# Offsets relativos ao canto superior esquerdo da janela (inclui decoração ~32px)
_MEMBROS_BTN_INDEX = 1          # "Membros" é o 2º botão na sidebar (index 1)
_ADD_BTN_X_OFFSET = 1165        # botão "＋" está à direita do content area (30px da borda)
_ADD_BTN_Y_OFFSET = 75          # window decoration(32) + menu(21) + header_mid(22)


class TestMembrosCRUD:
    """Testa o fluxo completo de adição de membro via UI."""

    def test_navega_para_membros(self, app_window):
        """Deve navegar para a tela Membros sem travar."""
        _click_sidebar_by_index(app_window, _MEMBROS_BTN_INDEX)
        e2e_wait(0.5)
        win = _get_window_geometry(APP_TITLE)
        assert win is not None, "App fechou ao navegar para Membros"

    def test_abre_dialog_adicionar(self, app_window):
        """Clicar no botão '＋' deve abrir o diálogo de cadastro."""
        _click_sidebar_by_index(app_window, _MEMBROS_BTN_INDEX)
        e2e_wait(0.5)

        _click_content_btn(app_window, _ADD_BTN_X_OFFSET, _ADD_BTN_Y_OFFSET)
        e2e_wait(0.7)

        # O diálogo de cadastro deve aparecer
        dialog = _get_window_geometry(DIALOG_TITLE)
        assert dialog is not None, (
            f"Diálogo '{DIALOG_TITLE}' não abriu após clicar em ＋. "
            "Verifique os offsets _ADD_BTN_X_OFFSET/_ADD_BTN_Y_OFFSET."
        )

        # Fecha o diálogo para não poluir outros testes
        pyautogui.press("escape")
        e2e_wait(0.3)

    def test_cria_membro_completo(self, app_window):
        """Preenche o formulário e salva — verifica sucesso sem crash."""
        _click_sidebar_by_index(app_window, _MEMBROS_BTN_INDEX)
        e2e_wait(0.5)

        _click_content_btn(app_window, _ADD_BTN_X_OFFSET, _ADD_BTN_Y_OFFSET)
        e2e_wait(0.7)

        dialog = _get_window_geometry(DIALOG_TITLE)
        if dialog is None:
            pytest.skip("Diálogo de cadastro não abriu — ajuste os offsets de coordenada")

        # Clica no primeiro campo (Nome) e digita
        campo_nome_x = dialog.left + dialog.width // 2 + 30
        campo_nome_y = dialog.top + 80  # primeiro campo do formulário
        pyautogui.click(campo_nome_x, campo_nome_y)
        e2e_wait(0.2)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write("Membro E2E Teste", interval=0.03)

        # Clica em Salvar (botão no rodapé do diálogo)
        salvar_x = dialog.left + dialog.width // 2 - 40
        salvar_y = dialog.top + dialog.height - 50
        pyautogui.click(salvar_x, salvar_y)
        e2e_wait(0.5)

        # Fecha qualquer messagebox de sucesso
        _dismiss_dialogs()
        e2e_wait(0.3)

        # App deve continuar aberto após salvar
        assert _get_window_geometry(APP_TITLE) is not None, "App fechou ao salvar membro"

    def test_app_nao_trava_apos_multiplas_acoes(self, app_window):
        """O app deve permanecer responsivo após várias interações na tela Membros."""
        _click_sidebar_by_index(app_window, _MEMBROS_BTN_INDEX)
        e2e_wait(0.4)

        # Navega para outras telas e volta
        for idx in [2, 3, 1]:
            _click_sidebar_by_index(app_window, idx)
            e2e_wait(0.3)

        win = _get_window_geometry(APP_TITLE)
        assert win is not None
        assert win.width >= 900


# ---------------------------------------------------------------------------
# Helpers locais
# ---------------------------------------------------------------------------

def _click_sidebar_by_index(app_window, index: int) -> None:
    """Clica no botão da sidebar pelo índice (reutiliza a lógica do smoke test)."""
    from tests.e2e.test_app_smoke import (
        _SIDEBAR_BTN_X_OFFSET,
        _SIDEBAR_BTN_Y_START,
        _SIDEBAR_BTN_HEIGHT,
    )
    x = app_window.left + _SIDEBAR_BTN_X_OFFSET
    y = app_window.top + _SIDEBAR_BTN_Y_START + index * _SIDEBAR_BTN_HEIGHT
    pyautogui.click(x, y)


def _click_content_btn(app_window, x_offset: int, y_offset: int) -> None:
    """Clica em um botão na content area usando offsets relativos à janela."""
    x = app_window.left + x_offset
    y = app_window.top + y_offset
    pyautogui.click(x, y)
