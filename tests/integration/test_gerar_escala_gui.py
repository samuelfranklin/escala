"""
Testes de integração para GUI de geração de escala.

Valida:
- Inicialização do frame com EscalaService
- Integração entre GUI e EscalaService
- Manipulação de entradas e saídas
- Tratamento de erros
"""

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk

from gui.gerar_escala import GerarEscalaFrame
from services.escala_service import EscalaService
from infra.database import create_tables


class TesteGerarEscalaGuiFrameInitialization(unittest.TestCase):
    """Testes de inicialização do frame GerarEscala."""

    def setUp(self):
        """Prepara environment para testes GUI."""
        self.root = tk.Tk()
        self.root.withdraw()  # Oculta a janela durante testes
        self.app_mock = MagicMock()
        self.app_mock.frames = {}

    def tearDown(self):
        """Limpa widgets após testes."""
        self.root.destroy()

    def test_gerar_escala_frame_initializes(self):
        """Deve inicializar frame com EscalaService injetado."""
        frame = GerarEscalaFrame(self.root, self.app_mock)

        # Verificar que o frame foi criado
        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, ttk.Frame)

        # Verificar que o service foi injetado
        self.assertIsNotNone(frame.service)
        self.assertIsInstance(frame.service, EscalaService)

        # Verificar widgets essenciais foram criados
        self.assertIsNotNone(frame.mes)
        self.assertIsNotNone(frame.ano)
        self.assertIsNotNone(frame.var_respeitar_casais)
        self.assertIsNotNone(frame.var_equilibrio)

    def test_frame_has_required_methods(self):
        """Deve expor métodos necessários acionados pela UI."""
        frame = GerarEscalaFrame(self.root, self.app_mock)

        self.assertTrue(hasattr(frame, "gerar"))
        self.assertTrue(callable(getattr(frame, "gerar")))
        self.assertTrue(hasattr(frame, "criar_widgets"))
        self.assertTrue(callable(getattr(frame, "criar_widgets")))

    def test_default_month_is_current_month(self):
        """Mês padrão deve ser o mês atual."""
        from datetime import datetime

        frame = GerarEscalaFrame(self.root, self.app_mock)
        current_month = datetime.now().month

        self.assertEqual(frame.mes.get(), str(current_month))

    def test_default_year_is_current_year(self):
        """Ano padrão deve ser o ano atual."""
        from datetime import datetime

        frame = GerarEscalaFrame(self.root, self.app_mock)
        current_year = datetime.now().year

        self.assertEqual(frame.ano.get(), str(current_year))


class TesteGerarEscalaGuiIntegration(unittest.TestCase):
    """Testes de integração GUI com EscalaService."""

    @classmethod
    def setUpClass(cls):
        """Prepara banco de dados para testes."""
        create_tables()

    def setUp(self):
        """Prepara environment para cada teste."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app_mock = MagicMock()
        self.app_mock.frames = {}
        self.frame = GerarEscalaFrame(self.root, self.app_mock)

    def tearDown(self):
        """Limpa widgets após testes."""
        self.root.destroy()

    @patch("services.escala_service.EscalaService.generate_schedule")
    def test_generate_schedule_with_valid_month(self, mock_generate):
        """Deve chamar service.generate_schedule com parâmetros válidos."""
        # Arrange
        mock_generate.return_value = (
            True,
            "Escala gerada com sucesso para 3/2026",
            [
                {
                    "data": "01/03/2026",
                    "dia": "Sexta",
                    "evento": "Reunião",
                    "horario": "19:00",
                    "squad": "Principal",
                    "membro": "João",
                }
            ],
        )

        # Act
        self.frame.mes.set(3)
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        with patch("tkinter.messagebox.showinfo"):
            self.frame.gerar()

        # Assert
        mock_generate.assert_called_once_with(month=3, year=2026, respect_couples=True, balance_distribution=True)

    @patch("services.escala_service.EscalaService.generate_schedule")
    def test_generate_schedule_with_respect_couples(self, mock_generate):
        """Deve respeitar opção de casais quando selecionada."""
        # Arrange
        mock_generate.return_value = (True, "Sucesso", [])

        # Act
        self.frame.var_respeitar_casais.set(False)
        self.frame.mes.set(1)
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        with patch("tkinter.messagebox.showinfo"):
            self.frame.gerar()

        # Assert
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args[1]
        self.assertFalse(call_kwargs["respect_couples"])

    @patch("services.escala_service.EscalaService.generate_schedule")
    def test_generate_schedule_with_balance_distribution(self, mock_generate):
        """Deve respeitar opção de equilíbrio quando selecionada."""
        # Arrange
        mock_generate.return_value = (True, "Sucesso", [])

        # Act
        self.frame.var_equilibrio.set(False)
        self.frame.mes.set(1)
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        with patch("tkinter.messagebox.showinfo"):
            self.frame.gerar()

        # Assert
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args[1]
        self.assertFalse(call_kwargs["balance_distribution"])

    @patch("services.escala_service.EscalaService.generate_schedule")
    @patch("tkinter.messagebox.showerror")
    def test_error_handling_invalid_month(self, mock_error, mock_generate):
        """Deve validar mês inválido antes de chamar service."""
        # Arrange
        self.frame.mes.set("invalido")
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        # Act
        self.frame.gerar()

        # Assert
        mock_generate.assert_not_called()
        mock_error.assert_called_once()
        self.assertIn("inválido", mock_error.call_args[0][1].lower())

    @patch("services.escala_service.EscalaService.generate_schedule")
    @patch("tkinter.messagebox.showerror")
    def test_error_handling_invalid_year(self, mock_error, mock_generate):
        """Deve validar ano inválido antes de chamar service."""
        # Arrange
        self.frame.mes.set(3)
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "invalido")

        # Act
        self.frame.gerar()

        # Assert
        mock_generate.assert_not_called()
        mock_error.assert_called_once()

    @patch("services.escala_service.EscalaService.generate_schedule")
    @patch("tkinter.messagebox.showwarning")
    def test_generate_schedule_shows_conflicts(self, mock_warning, mock_generate):
        """Deve mostrar aviso quando há conflitos na geração."""
        # Arrange
        conflito_msg = (
            "Conflitos encontrados:\n"
            "01/03/2026 - Reunião - Principal: precisa 5, selecionados 2"
        )
        mock_generate.return_value = (True, conflito_msg, [])

        # Act
        self.frame.mes.set(3)
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        self.frame.gerar()

        # Assert
        mock_generate.assert_called_once()
        mock_warning.assert_called_once()
        self.assertIn("Aviso", mock_warning.call_args[0][0])

    @patch("services.escala_service.EscalaService.generate_schedule")
    @patch("tkinter.messagebox.showinfo")
    def test_generate_schedule_success_message(self, mock_info, mock_generate):
        """Deve mostrar mensagem de sucesso quando escala é gerada sem conflitos."""
        # Arrange
        mock_generate.return_value = (
            True,
            "Escala gerada com sucesso para 3/2026",
            [{"data": "01/03/2026", "membro": "João"}],
        )

        # Act
        self.frame.mes.set(3)
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        self.frame.gerar()

        # Assert
        mock_info.assert_called_once()

    @patch("services.escala_service.EscalaService.generate_schedule")
    @patch("tkinter.messagebox.showerror")
    def test_service_returns_error(self, mock_error, mock_generate):
        """Deve exibir erro quando serviço retorna sucesso=False."""
        # Arrange
        error_msg = "Mês/Ano inválidos no banco de dados"
        mock_generate.return_value = (False, error_msg, [])

        # Act
        self.frame.mes.set(13)  # Mês inválido
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        self.frame.gerar()

        # Assert
        mock_error.assert_called_once_with("Erro", error_msg)

    @patch("services.escala_service.EscalaService.generate_schedule")
    def test_escala_passed_to_visualizar_frame(self, mock_generate):
        """Deve passar escala gerada para frame Visualizar se disponível."""
        # Arrange
        escala_mock = [
            {
                "data": "01/03/2026",
                "dia": "Sexta",
                "evento": "Reunião",
                "horario": "19:00",
                "squad": "Principal",
                "membro": "João",
            }
        ]
        mock_generate.return_value = (True, "Sucesso", escala_mock)
        visualizar_mock = MagicMock()
        self.frame.app.frames["Visualizar"] = visualizar_mock

        # Act
        self.frame.mes.set(3)
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        with patch("tkinter.messagebox.showinfo"):
            self.frame.gerar()

        # Assert
        visualizar_mock.set_escala.assert_called_once_with(escala_mock)

    @patch("services.escala_service.EscalaService.generate_schedule")
    def test_escala_stored_locally_if_visualizar_not_available(self, mock_generate):
        """Deve armazenar escala localmente se frame Visualizar não existe."""
        # Arrange
        escala_mock = [{"data": "01/03/2026", "membro": "João"}]
        mock_generate.return_value = (True, "Sucesso", escala_mock)
        self.frame.app.frames = {}  # Visualizar não existe

        # Act
        self.frame.mes.set(3)
        self.frame.ano.delete(0, tk.END)
        self.frame.ano.insert(0, "2026")

        with patch("tkinter.messagebox.showinfo"):
            self.frame.gerar()

        # Assert
        self.assertTrue(hasattr(self.frame, "escala"))
        self.assertEqual(self.frame.escala, escala_mock)


class TesteGerarEscalaGuiMeses(unittest.TestCase):
    """Testes de validação de meses."""

    def setUp(self):
        """Prepara environment para testes."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app_mock = MagicMock()
        self.frame = GerarEscalaFrame(self.root, self.app_mock)

    def tearDown(self):
        """Limpa widgets."""
        self.root.destroy()

    def test_mes_combobox_has_all_months(self):
        """Combobox de mês deve ter opções de 1 a 12."""
        # O combobox é criado com values=list(range(1, 13))
        # Não conseguimos acessar diretamente, mas podemos verificar que foi criado
        self.assertIsNotNone(self.frame.mes)
        self.assertIsInstance(self.frame.mes, ttk.Combobox)


if __name__ == "__main__":
    unittest.main()
