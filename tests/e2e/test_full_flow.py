"""Suite E2E TDD-RED — Fluxo Completo: Membros → Times → Eventos → Config → Gerar Escala.

Esta suite documenta o comportamento ESPERADO do sistema de ponta a ponta.
Por ser TDD-RED, alguns testes irão falhar intencionalmente, sinalizando
o que precisa ser corrigido antes de chegar ao estado GREEN.

Pré-requisitos para executar:
    env -u WAYLAND_DISPLAY DISPLAY=:0 pytest tests/e2e/test_full_flow.py -v -s
    # Modo visual:
    env -u WAYLAND_DISPLAY DISPLAY=:0 pytest tests/e2e/test_full_flow.py -v -s --slow

Dados de teste:
    - 10 membros: Ana Lima até João Alves
    - 5 times: Câmera, Transmissão, Áudio, Iluminação, Apresentação
    - Cada time recebe 2 membros
    - 3 eventos fixos: Culto Domingo, Culto Quarta, Culto Sexta
    - 1 squad configurado por evento (quantidade=1)
    - Gera escala do mês atual
"""

import datetime
import time

import pyautogui
import pytest

from tests.e2e.conftest import e2e_wait, WindowGeometry
from tests.e2e.helpers.navigation import (
    navigate_to, click_add_button, click_at_offset,
    SIDEBAR_BTN_X_OFFSET, SIDEBAR_BTN_Y_START, SIDEBAR_BTN_HEIGHT,
)
from tests.e2e.helpers.dialogs import (
    wait_for_dialog, dismiss_messagebox, dismiss_any_dialog,
    fill_membro_dialog, fill_squad_dialog, fill_evento_dialog,
    fill_config_evento_dialog,
)
from tests.e2e.helpers.window import (
    count_members, count_squads, count_events,
    count_member_squads, count_event_squads,
)

# ---------------------------------------------------------------------------
# Dados de teste
# ---------------------------------------------------------------------------

MEMBROS = [
    "Ana Lima", "Bruno Souza", "Carla Mendes", "Diego Rocha", "Eva Martins",
    "Felipe Costa", "Gabi Oliveira", "Hugo Ferreira", "Iris Santos", "João Alves",
]

TIMES = ["Câmera", "Transmissão", "Áudio", "Iluminação", "Apresentação"]

# Distribuição: time → [membro index 0, membro index 1]
TIMES_MEMBROS = {
    "Câmera":       (0, 1),   # Ana Lima, Bruno Souza
    "Transmissão":  (2, 3),   # Carla Mendes, Diego Rocha
    "Áudio":        (4, 5),   # Eva Martins, Felipe Costa
    "Iluminação":   (6, 7),   # Gabi Oliveira, Hugo Ferreira
    "Apresentação": (8, 9),   # Iris Santos, João Alves
}

EVENTOS = [
    {"name": "Culto Domingo", "tipo": "fixo", "dia": "Domingo",      "horario": "09:00"},
    {"name": "Culto Quarta",  "tipo": "fixo", "dia": "Quarta-feira", "horario": "19:30"},
    {"name": "Culto Sexta",   "tipo": "fixo", "dia": "Sexta-feira",  "horario": "20:00"},
]

# Configuração EventSquad: evento → 1º squad disponível, quantidade=1
# (O teste seleciona o primeiro squad do dialog ConfigEventoDialog)

# ---------------------------------------------------------------------------
# Constantes de layout (calibradas para janela 1280×700 com sidebar 200px)
# ---------------------------------------------------------------------------

# Treeview de conteúdo: começa logo após o header (Y ~100 do topo da janela)
_TREEVIEW_FIRST_ROW_Y = 118   # Y da primeira linha da Treeview
_TREEVIEW_ROW_HEIGHT = 22     # altura de cada linha
_TREEVIEW_CENTER_X = 620      # X central da área de conteúdo (sidebar=200, total~1280)

# Painel direito de membros (squads screen)
_RIGHT_PANEL_X = 900          # centro do painel de membros (área direita)
_RIGHT_PANEL_FIRST_CHECKBOX_Y = 155  # Y do primeiro checkbox de membro
_RIGHT_PANEL_CHECKBOX_HEIGHT = 42    # altura de cada linha de membro

# Botão 💾 na barra direita de Times
_SAVE_BTN_X_OFFSET = 1230
_SAVE_BTN_Y_OFFSET = 100     # Y relativo ao topo da janela, dentro da área de Times

# Botão "Configurar Selecionado" na tela Config
_CONFIG_BTN_X_OFFSET = 250    # X relativo ao conteúdo (sidebar=200, botão ~50px do conteúdo)
_CONFIG_BTN_Y_OFFSET = 400    # Y estimado (abaixo da Treeview de eventos)

# Campos da tela Escalas
_ESCALA_MES_X_OFFSET = 450    # X do combobox de Mês
_ESCALA_MES_Y_OFFSET = 180    # Y do combobox de Mês
_ESCALA_ANO_X_OFFSET = 450    # X do campo Ano
_ESCALA_ANO_Y_OFFSET = 215    # Y do campo Ano
_GERAR_BTN_X_OFFSET = 450     # X do botão "Gerar Escala"
_GERAR_BTN_Y_OFFSET = 260     # Y do botão "Gerar Escala"


# ---------------------------------------------------------------------------
# Suite de testes
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("app_process_isolated")
class TestFluxoCompleto:
    """Fluxo completo E2E: Membros → Times → Associações → Eventos → Config → Escala."""

    # -----------------------------------------------------------------------
    # Fase 0: App inicia com banco limpo
    # -----------------------------------------------------------------------

    def test_00_app_abre_com_banco_limpo(self, app_window_isolated, e2e_db_path):
        """App inicia com banco temporário e banco começa vazio (0 membros)."""
        e2e_wait(1.0)
        n = count_members(e2e_db_path)
        assert n == 0, (
            f"Banco deveria estar vazio, mas tem {n} membros. "
            f"Verifique se DATABASE_URL={e2e_db_path} está sendo passado ao subprocesso."
        )

    # -----------------------------------------------------------------------
    # Fase 1: Criar 10 membros
    # -----------------------------------------------------------------------

    def test_01_cria_10_membros(self, app_window_isolated):
        """Cria 10 membros via tela Membros → botão '+' → MembroDialog."""
        win = app_window_isolated
        navigate_to(win, "Membros", wait=1.0)

        for name in MEMBROS:
            click_add_button(win, wait=0.8)
            ok = fill_membro_dialog(name)
            assert ok, (
                f"Dialog 'Cadastro de Membro' não abriu ao tentar criar '{name}'. "
                "Verifique a coordenada do botão '+' (ADD_BTN_X_OFFSET/Y_OFFSET)."
            )
            e2e_wait(0.3)

    def test_02_membros_aparecem_na_lista(self, app_window_isolated, e2e_db_path):
        """Após criar, banco deve conter exatamente 10 membros."""
        n = count_members(e2e_db_path)
        assert n == 10, (
            f"Esperado 10 membros no banco, encontrado: {n}. "
            "Verifique se o dialog Salvar está persistindo corretamente."
        )

    # -----------------------------------------------------------------------
    # Fase 2: Criar 5 times
    # -----------------------------------------------------------------------

    def test_03_cria_5_times(self, app_window_isolated):
        """Cria 5 times via tela Times → botão '+' → SquadDialog."""
        win = app_window_isolated
        navigate_to(win, "Times", wait=1.0)

        for squad_name in TIMES:
            click_add_button(win, wait=0.8)
            ok = fill_squad_dialog(squad_name)
            assert ok, (
                f"Dialog 'Cadastro de Squad' não abriu ao tentar criar '{squad_name}'. "
                "Verifique a coordenada do botão '+' na tela Times."
            )
            e2e_wait(0.3)

    def test_04_times_aparecem_na_lista(self, app_window_isolated, e2e_db_path):
        """Após criar, banco deve conter exatamente 5 squads."""
        n = count_squads(e2e_db_path)
        assert n == 5, (
            f"Esperado 5 squads no banco, encontrado: {n}. "
            "Verifique se SquadDialog está salvando corretamente (self.result e service.create_squad)."
        )

    # -----------------------------------------------------------------------
    # Fase 3: Associar membros aos times
    # -----------------------------------------------------------------------

    def test_05_associa_membros_aos_times(self, app_window_isolated, e2e_db_path):
        """Para cada time: seleciona o time, marca 2 membros, clica 💾.

        Layout: painel esquerdo = lista de times (Treeview), painel direito = checkboxes de membros.
        """
        win = app_window_isolated
        navigate_to(win, "Times", wait=1.0)

        for squad_index, squad_name in enumerate(TIMES):
            membro_indices = TIMES_MEMBROS[squad_name]

            # Clica na linha do squad na Treeview esquerda
            squad_row_x = win.left + _TREEVIEW_CENTER_X // 2  # metade esquerda
            squad_row_y = win.top + _TREEVIEW_FIRST_ROW_Y + squad_index * _TREEVIEW_ROW_HEIGHT
            pyautogui.click(squad_row_x, squad_row_y)
            e2e_wait(0.5)

            # Marca os 2 checkboxes correspondentes no painel direito
            for membro_idx in membro_indices:
                cb_x = win.left + _RIGHT_PANEL_X
                cb_y = win.top + _RIGHT_PANEL_FIRST_CHECKBOX_Y + membro_idx * _RIGHT_PANEL_CHECKBOX_HEIGHT
                pyautogui.click(cb_x, cb_y)
                e2e_wait(0.3)

            # Clica no botão 💾
            save_x = win.left + _SAVE_BTN_X_OFFSET
            save_y = win.top + _SAVE_BTN_Y_OFFSET
            pyautogui.click(save_x, save_y)
            e2e_wait(0.5)

            # Fecha mensagem de sucesso se aparecer
            dismiss_messagebox(wait=0.3)

        # Verifica que foram criadas ao menos 10 associações (2 por time × 5 times)
        n = count_member_squads(e2e_db_path)
        assert n >= 10, (
            f"Esperado ≥ 10 associações membro-squad, encontrado: {n}. "
            "Verifique as coordenadas dos checkboxes (_RIGHT_PANEL_FIRST_CHECKBOX_Y) "
            "e do botão 💾 (_SAVE_BTN_X/Y_OFFSET)."
        )

    # -----------------------------------------------------------------------
    # Fase 4: Criar 3 eventos
    # -----------------------------------------------------------------------

    def test_06_cria_3_eventos(self, app_window_isolated):
        """Cria 3 eventos fixos via tela Eventos → botão '+' → EventoDialog."""
        win = app_window_isolated
        navigate_to(win, "Eventos", wait=1.0)

        for ev in EVENTOS:
            click_add_button(win, wait=0.8)
            ok = fill_evento_dialog(
                name=ev["name"],
                tipo=ev["tipo"],
                dia=ev["dia"],
                horario=ev["horario"],
            )
            assert ok, (
                f"Dialog de evento não abriu ao tentar criar '{ev['name']}'. "
                "Verifique a coordenada do botão '+' na tela Eventos."
            )
            e2e_wait(0.3)

    def test_07_eventos_aparecem_na_lista(self, app_window_isolated, e2e_db_path):
        """Após criar, banco deve conter exatamente 3 eventos."""
        n = count_events(e2e_db_path)
        assert n == 3, (
            f"Esperado 3 eventos no banco, encontrado: {n}. "
            "Verifique se EventoDialog está salvando via service.create_event."
        )

    # -----------------------------------------------------------------------
    # Fase 5: Configurar EventSquad (vincular times a eventos)
    # -----------------------------------------------------------------------

    def test_08_configura_eventos_com_times(self, app_window_isolated, e2e_db_path):
        """Para cada evento: seleciona na tela Config, abre dialog, vincula 1 squad.

        Tela: Config (sidebar index 6) → lista de eventos → Configurar Selecionado
        → ConfigEventoDialog com checkboxes por squad + spinbox de quantidade.
        """
        win = app_window_isolated
        navigate_to(win, "Config", wait=1.0)

        for ev_index, ev in enumerate(EVENTOS):
            # Seleciona o evento na Treeview
            ev_row_x = win.left + _TREEVIEW_CENTER_X
            ev_row_y = win.top + _TREEVIEW_FIRST_ROW_Y + ev_index * _TREEVIEW_ROW_HEIGHT
            pyautogui.click(ev_row_x, ev_row_y)
            e2e_wait(0.4)

            # Clica em "Configurar Selecionado"
            config_btn_x = win.left + _CONFIG_BTN_X_OFFSET
            config_btn_y = win.top + _CONFIG_BTN_Y_OFFSET
            pyautogui.click(config_btn_x, config_btn_y)
            e2e_wait(0.8)

            # Preenche o dialog de configuração
            ok = fill_config_evento_dialog(squad_name=TIMES[0], quantidade=1)
            assert ok, (
                f"Dialog 'Configurar:' não abriu para o evento '{ev['name']}'. "
                "Verifique as coordenadas do botão 'Configurar Selecionado' "
                "(_CONFIG_BTN_X/Y_OFFSET)."
            )
            e2e_wait(0.5)

        # Verifica que foram criadas ao menos 3 configurações EventSquad
        n = count_event_squads(e2e_db_path)
        assert n >= 3, (
            f"Esperado ≥ 3 configurações EventSquad, encontrado: {n}. "
            "Verifique se ConfigEventoDialog está salvando corretamente."
        )

    # -----------------------------------------------------------------------
    # Fase 6: Gerar Escala
    # -----------------------------------------------------------------------

    def test_09_gera_escala_do_mes_atual(self, app_window_isolated):
        """Navega para Escalas, confirma mês/ano atual e clica 'Gerar Escala'.

        Critério de sucesso: aparece dialog de sucesso ou aviso (não erro fatal).
        """
        win = app_window_isolated
        navigate_to(win, "Escalas", wait=1.0)

        now = datetime.datetime.now()
        mes_atual = now.month
        ano_atual = now.year

        # Mês: Combobox — o valor já deve vir preenchido com o mês atual
        # Clicamos para confirmar a seleção
        mes_x = win.left + _ESCALA_MES_X_OFFSET
        mes_y = win.top + _ESCALA_MES_Y_OFFSET
        pyautogui.click(mes_x, mes_y)
        e2e_wait(0.3)
        pyautogui.press("escape")  # fecha dropdown se abriu

        # Ano: Entry — limpa e digita o ano atual
        ano_x = win.left + _ESCALA_ANO_X_OFFSET
        ano_y = win.top + _ESCALA_ANO_Y_OFFSET
        pyautogui.click(ano_x, ano_y)
        e2e_wait(0.2)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(str(ano_atual), interval=0.05)
        e2e_wait(0.2)

        # Botão "Gerar Escala"
        gerar_x = win.left + _GERAR_BTN_X_OFFSET
        gerar_y = win.top + _GERAR_BTN_Y_OFFSET
        pyautogui.click(gerar_x, gerar_y)
        e2e_wait(1.5)  # aguarda processamento

        # Verifica que apareceu algum dialog (sucesso ou aviso, não deveria travar)
        # Fecha qualquer dialog que tenha aparecido
        dialog_appeared = (
            wait_for_dialog("Sucesso", timeout=2.0) is not None
            or wait_for_dialog("Aviso", timeout=1.0) is not None
            or wait_for_dialog("Escala", timeout=1.0) is not None
        )
        dismiss_any_dialog(wait=0.5)

        assert dialog_appeared, (
            "Nenhum dialog apareceu após clicar em 'Gerar Escala'. "
            "Verifique as coordenadas dos campos de mês/ano e do botão Gerar "
            "(_ESCALA_MES/ANO/GERAR_BTN offsets) ou se a escala está sendo gerada."
        )

    # -----------------------------------------------------------------------
    # Fase 7: Visualizar escala gerada
    # -----------------------------------------------------------------------

    def test_10_visualizar_exibe_escala_gerada(self, app_window_isolated):
        """Navega para Visualizar e verifica que a tela carrega sem crash."""
        win = app_window_isolated
        navigate_to(win, "Visualizar", wait=1.0)
        e2e_wait(0.5)

        # Verifica que a janela principal ainda está de pé (não crashou)
        from tests.e2e.conftest import _get_window_geometry, APP_TITLE
        final_win = _get_window_geometry(APP_TITLE)
        assert final_win is not None, (
            "Janela principal desapareceu após navegar para Visualizar. "
            "O app pode ter crashado."
        )
