"""Fixtures para testes E2E — inicia o app real em subprocesso e fornece helpers
pyautogui para interação com a janela.

Requisitos de ambiente:
- DISPLAY deve estar definido (ex.: :0)
- python3-Xlib está instalado (dependência do pyautogui)

Modo visual (para acompanhar o teste na tela):
    env -u WAYLAND_DISPLAY pytest tests/e2e/ -v -s --slow
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Generator, NamedTuple, Optional

import pyautogui
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_TITLE = "Sistema de Escala - Time da Mídia"

# Desabilita failsafe em testes (mover mouse para canto não aborta o teste)
pyautogui.FAILSAFE = False
# Pausa mínima entre ações para a UI ter tempo de reagir
pyautogui.PAUSE = 0.1


def pytest_addoption(parser):
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Modo visual: aumenta pyautogui.PAUSE para 0.6s e adiciona esperas extras "
             "para que você consiga acompanhar o teste na tela.",
    )


@pytest.fixture(scope="session", autouse=True)
def _apply_speed(request):
    """Ajusta velocidade do pyautogui conforme --slow."""
    if request.config.getoption("--slow"):
        pyautogui.PAUSE = 0.6


def e2e_wait(seconds: float) -> None:
    """sleep que respeita o modo --slow (multiplica por 3 se ativo)."""
    multiplier = 3.0 if pyautogui.PAUSE >= 0.5 else 1.0
    time.sleep(seconds * multiplier)


class WindowGeometry(NamedTuple):
    title: str
    left: int
    top: int
    width: int
    height: int


@pytest.fixture(scope="session")
def app_process() -> Generator[subprocess.Popen, None, None]:
    """Inicia o app em subprocesso e aguarda a janela ficar visível.

    Escopo 'session': o app sobe uma vez e é reaproveitado por todos os
    testes da sessão E2E.
    """
    env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
    env.pop("WAYLAND_DISPLAY", None)  # forçar X11/XWayland em vez de Wayland nativo

    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _wait_for_window(APP_TITLE, timeout=15):
        proc.terminate()
        pytest.fail(f"Janela '{APP_TITLE}' não apareceu em 15 segundos.")

    # Fecha qualquer diálogo de erro que o app possa abrir na inicialização
    time.sleep(0.5)
    _dismiss_dialogs()

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def e2e_db_path(tmp_path_factory) -> Generator[str, None, None]:
    """Cria um banco SQLite temporário e isolado para a sessão de testes E2E.

    O arquivo é removido automaticamente ao final da sessão.
    """
    db_dir = tmp_path_factory.mktemp("escala_e2e")
    db_file = db_dir / "test_full_flow.db"
    yield str(db_file)
    # Limpeza: remove o arquivo ao final da sessão
    try:
        db_file.unlink(missing_ok=True)
    except Exception:
        pass


@pytest.fixture(scope="session")
def app_process_isolated(e2e_db_path) -> Generator[subprocess.Popen, None, None]:
    """Inicia o app com um banco de dados temporário e isolado.

    Use este fixture para testes que precisam de estado limpo (full-flow E2E).
    """
    env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
    env.pop("WAYLAND_DISPLAY", None)  # forçar X11/XWayland
    env["DATABASE_URL"] = f"sqlite:///{e2e_db_path}"

    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _wait_for_window(APP_TITLE, timeout=15):
        proc.terminate()
        pytest.fail(f"Janela '{APP_TITLE}' não apareceu em 15 segundos (modo isolado).")

    time.sleep(0.5)
    _dismiss_dialogs()

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="function")
def app_window_isolated(app_process_isolated) -> WindowGeometry:
    """Retorna a geometria da janela principal (instância isolada) e traz para o foco."""
    win = _get_window_geometry(APP_TITLE)
    assert win is not None, f"Janela '{APP_TITLE}' não encontrada"
    pyautogui.click(win.left + win.width // 2, win.top + 15)
    time.sleep(0.2)
    return win


@pytest.fixture(scope="function")
def app_window(app_process) -> WindowGeometry:
    """Retorna a geometria da janela principal e traz ela para o foco."""
    win = _get_window_geometry(APP_TITLE)
    assert win is not None, f"Janela '{APP_TITLE}' não encontrada"

    # Ativa/foca a janela clicando na barra de título
    title_bar_x = win.left + win.width // 2
    title_bar_y = win.top + 15
    pyautogui.click(title_bar_x, title_bar_y)
    time.sleep(0.2)
    return win


# ---------------------------------------------------------------------------
# Helpers internos — busca de janela via python-Xlib
# ---------------------------------------------------------------------------

def _wait_for_window(title: str, timeout: int = 10) -> bool:
    """Aguarda até que uma janela com o título dado apareça no desktop."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _get_window_geometry(title) is not None:
            return True
        time.sleep(0.5)
    return False


def _get_window_geometry(title: str) -> Optional[WindowGeometry]:
    """Encontra janela por título (busca parcial) e retorna sua geometria.

    Usa python-Xlib para varrer a árvore de janelas do display atual.
    Compatível com Linux/X11.
    """
    try:
        from Xlib import display as xdisplay, X, Xatom

        d = xdisplay.Display()
        root = d.screen().root

        # Percorre toda a árvore de janelas
        win = _find_window_by_title(root, title, d)
        if win is None:
            return None

        # Pega geometria absoluta
        geom = win.get_geometry()
        coords = win.translate_coords(root, 0, 0)
        return WindowGeometry(
            title=title,
            left=-coords.x,
            top=-coords.y,
            width=geom.width,
            height=geom.height,
        )
    except Exception:
        return None


def _find_window_by_title(window, title: str, display):
    """Busca recursiva por uma janela que contenha `title` no nome."""
    try:
        name = window.get_wm_name()
        if name and title in name:
            return window
    except Exception:
        pass

    try:
        children = window.query_tree().children
    except Exception:
        return None

    for child in children:
        result = _find_window_by_title(child, title, display)
        if result is not None:
            return result
    return None


def _dismiss_dialogs() -> None:
    """Fecha dialogs modais (messagebox) pressionando Enter/Escape."""
    pyautogui.press("escape")
    time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(0.1)
