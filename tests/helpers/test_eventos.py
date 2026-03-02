"""
Testes TDD para helpers/eventos.py (cobertura 100%).

Cada teste segue padrão RED-GREEN:
1. RED: teste falha (lógica ainda não implementada)
2. GREEN: implementa lógica mínima para passar
3. REFACTOR: melhora código mantendo testes verdes
"""

import unittest
from helpers.eventos import (
    validate_event_name,
    validate_event_type,
    validate_day_of_week,
    validate_date,
    validate_time,
    validate_event_squads,
    normalize_event_name,
    normalize_time,
    normalize_date,
)


class TestValidateEventName(unittest.TestCase):
    """Testa validação de nome de evento."""

    def test_nome_valido_sem_duplicatas(self):
        """Nome válido sem duplicatas retorna (True, "")."""
        is_valid, msg = validate_event_name("Culto Domingo", [])
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_nome_vazio_retorna_erro(self):
        """Nome vazio retorna erro."""
        is_valid, msg = validate_event_name("", [])
        self.assertFalse(is_valid)
        self.assertIn("vazio", msg.lower())

    def test_nome_apenas_espacos_retorna_erro(self):
        """Nome com apenas espaços retorna erro."""
        is_valid, msg = validate_event_name("   ", [])
        self.assertFalse(is_valid)
        self.assertIn("vazio", msg.lower())

    def test_nome_duplicado_retorna_erro(self):
        """Nome duplicado retorna erro."""
        existing = ["Culto Domingo", "Culto Quarta"]
        is_valid, msg = validate_event_name("Culto Domingo", existing)
        self.assertFalse(is_valid)
        self.assertIn("Culto Domingo", msg)
        self.assertIn("já existe", msg.lower())

    def test_nome_com_espacos_extras_removidos(self):
        """Nome com espaços extras é comparado após normalização."""
        is_valid, msg = validate_event_name("  Culto Domingo  ", [])
        self.assertTrue(is_valid)

    def test_nome_none_retorna_erro(self):
        """Nome None retorna erro."""
        is_valid, msg = validate_event_name(None, [])
        self.assertFalse(is_valid)


class TestValidateEventType(unittest.TestCase):
    """Testa validação de tipo de evento."""

    def test_tipo_fixo_valido(self):
        """Tipo 'fixo' é válido."""
        is_valid, msg = validate_event_type("fixo")
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_tipo_sazonal_valido(self):
        """Tipo 'sazonal' é válido."""
        is_valid, msg = validate_event_type("sazonal")
        self.assertTrue(is_valid)

    def test_tipo_eventual_valido(self):
        """Tipo 'eventual' é válido."""
        is_valid, msg = validate_event_type("eventual")
        self.assertTrue(is_valid)

    def test_tipo_invalido_retorna_erro(self):
        """Tipo inválido retorna erro."""
        is_valid, msg = validate_event_type("invalido")
        self.assertFalse(is_valid)
        self.assertIn("inválido", msg.lower())
        self.assertIn("fixo", msg)
        self.assertIn("sazonal", msg)

    def test_tipo_vazio_retorna_erro(self):
        """Tipo vazio retorna erro."""
        is_valid, msg = validate_event_type("")
        self.assertFalse(is_valid)

    def test_tipo_none_retorna_erro(self):
        """Tipo None retorna erro."""
        is_valid, msg = validate_event_type(None)
        self.assertFalse(is_valid)


class TestValidateDayOfWeek(unittest.TestCase):
    """Testa validação de dia da semana."""

    def test_dias_em_ingles_validos(self):
        """Dias em inglês são válidos."""
        dias_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for dia in dias_en:
            is_valid, msg = validate_day_of_week(dia)
            self.assertTrue(is_valid, f"Dia '{dia}' deveria ser válido")

    def test_dias_em_portugues_validos(self):
        """Dias em português são válidos."""
        dias_pt = [
            "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
            "Sexta-feira", "Sábado", "Domingo"
        ]
        for dia in dias_pt:
            is_valid, msg = validate_day_of_week(dia)
            self.assertTrue(is_valid, f"Dia '{dia}' deveria ser válido")

    def test_dia_invalido_retorna_erro(self):
        """Dia inválido retorna erro."""
        is_valid, msg = validate_day_of_week("Segundafeira")
        self.assertFalse(is_valid)
        self.assertIn("inválido", msg.lower())

    def test_dia_vazio_retorna_erro(self):
        """Dia vazio retorna erro."""
        is_valid, msg = validate_day_of_week("")
        self.assertFalse(is_valid)

    def test_dia_none_retorna_erro(self):
        """Dia None retorna erro."""
        is_valid, msg = validate_day_of_week(None)
        self.assertFalse(is_valid)


class TestValidateDate(unittest.TestCase):
    """Testa validação de data DD/MM/YYYY."""

    def test_data_valida_padrao(self):
        """Data válida no formato DD/MM/YYYY retorna sucesso."""
        is_valid, msg = validate_date("25/12/2024")
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_data_primeira_do_mes(self):
        """Primeiro dia do mês é válido."""
        is_valid, msg = validate_date("01/01/2024")
        self.assertTrue(is_valid)

    def test_data_ultimo_dia_mes_31(self):
        """Último dia de mês com 31 dias é válido."""
        is_valid, msg = validate_date("31/01/2024")
        self.assertTrue(is_valid)

    def test_data_ultimo_dia_mes_30(self):
        """Último dia de mês com 30 dias é válido."""
        is_valid, msg = validate_date("30/04/2024")
        self.assertTrue(is_valid)

    def test_data_fevereiro_nao_bissexto(self):
        """Fevereiro sem bissexto máximo 28 dias."""
        is_valid, msg = validate_date("29/02/2023")
        self.assertFalse(is_valid)

    def test_data_fevereiro_bissexto(self):
        """Fevereiro bissexto permite 29 dias."""
        is_valid, msg = validate_date("29/02/2024")
        self.assertTrue(is_valid)

    def test_data_mes_invalido_13(self):
        """Mês 13 é inválido."""
        is_valid, msg = validate_date("15/13/2024")
        self.assertFalse(is_valid)
        self.assertIn("mês", msg.lower())

    def test_data_dia_invalido_32(self):
        """Dia 32 é inválido."""
        is_valid, msg = validate_date("32/01/2024")
        self.assertFalse(is_valid)
        self.assertIn("dia", msg.lower())

    def test_data_dia_invalido_30_fevereiro(self):
        """Fevereiro não tem 30 dias."""
        is_valid, msg = validate_date("30/02/2024")
        self.assertFalse(is_valid)
        self.assertIn("fevereiro", msg.lower())

    def test_data_ano_muito_antigo(self):
        """Ano anterior a 2000 é inválido."""
        is_valid, msg = validate_date("15/01/1999")
        self.assertFalse(is_valid)
        self.assertIn("ano", msg.lower())

    def test_data_ano_muito_futuro(self):
        """Ano posterior a 2100 é inválido."""
        is_valid, msg = validate_date("15/01/2101")
        self.assertFalse(is_valid)
        self.assertIn("ano", msg.lower())

    def test_data_formato_invalido_sem_barra(self):
        """Data sem barra retorna erro."""
        is_valid, msg = validate_date("25122024")
        self.assertFalse(is_valid)
        self.assertIn("formato", msg.lower())

    def test_data_formato_invalido_2_barras(self):
        """Data com formato errado retorna erro."""
        is_valid, msg = validate_date("2024/12/25")
        self.assertFalse(is_valid)
        self.assertIn("formato", msg.lower())

    def test_data_com_texto_retorna_erro(self):
        """Data com texto retorna erro."""
        is_valid, msg = validate_date("abc/def/ghij")
        self.assertFalse(is_valid)
        self.assertIn("inválida", msg.lower())

    def test_data_vazia_retorna_erro(self):
        """Data vazia retorna erro."""
        is_valid, msg = validate_date("")
        self.assertFalse(is_valid)

    def test_data_none_retorna_erro(self):
        """Data None retorna erro."""
        is_valid, msg = validate_date(None)
        self.assertFalse(is_valid)

    def test_data_com_espacos_extras(self):
        """Data com espaços extras é normalizada."""
        is_valid, msg = validate_date("  25/12/2024  ")
        self.assertTrue(is_valid)


class TestValidateTime(unittest.TestCase):
    """Testa validação de horário HH:MM."""

    def test_horario_valido_padrao(self):
        """Horário válido retorna sucesso."""
        is_valid, msg = validate_time("14:30")
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_horario_meia_noite(self):
        """Meia-noite é válida."""
        is_valid, msg = validate_time("00:00")
        self.assertTrue(is_valid)

    def test_horario_quase_meia_noite(self):
        """23:59 é válido."""
        is_valid, msg = validate_time("23:59")
        self.assertTrue(is_valid)

    def test_horario_hora_invalida_24(self):
        """Hora 24 é inválida."""
        is_valid, msg = validate_time("24:00")
        self.assertFalse(is_valid)
        self.assertIn("hora", msg.lower())

    def test_horario_minuto_invalido_60(self):
        """Minuto 60 é inválido."""
        is_valid, msg = validate_time("14:60")
        self.assertFalse(is_valid)
        self.assertIn("minuto", msg.lower())

    def test_horario_formato_invalido_sem_dois_pontos(self):
        """Formato sem dois pontos retorna erro."""
        is_valid, msg = validate_time("1430")
        self.assertFalse(is_valid)
        self.assertIn("formato", msg.lower())

    def test_horario_formato_invalido_com_texto(self):
        """Horário com texto retorna erro."""
        is_valid, msg = validate_time("ab:cd")
        self.assertFalse(is_valid)
        self.assertIn("inválido", msg.lower())

    def test_horario_vazio_retorna_erro(self):
        """Horário vazio retorna erro."""
        is_valid, msg = validate_time("")
        self.assertFalse(is_valid)

    def test_horario_none_retorna_erro(self):
        """Horário None retorna erro."""
        is_valid, msg = validate_time(None)
        self.assertFalse(is_valid)

    def test_horario_com_espacos_extras(self):
        """Horário com espaços extras é normalizado."""
        is_valid, msg = validate_time("  14:30  ")
        self.assertTrue(is_valid)


class TestValidateEventSquads(unittest.TestCase):
    """Testa validação de configuração de squads."""

    def test_squads_vazio_valido(self):
        """Dicionário vazio é válido."""
        is_valid, msg = validate_event_squads({})
        self.assertTrue(is_valid)

    def test_squads_valido_um_squad(self):
        """Um squad com quantidade válida."""
        is_valid, msg = validate_event_squads({"squad-1": 5})
        self.assertTrue(is_valid)

    def test_squads_valido_multiplos(self):
        """Múltiplos squads com quantidades válidas."""
        is_valid, msg = validate_event_squads({
            "squad-1": 3,
            "squad-2": 5,
            "squad-3": 0
        })
        self.assertTrue(is_valid)

    def test_squads_quantidade_zero_valido(self):
        """Quantidade zero é válida."""
        is_valid, msg = validate_event_squads({"squad-1": 0})
        self.assertTrue(is_valid)

    def test_squads_quantidade_negativa_invalido(self):
        """Quantidade negativa é inválida."""
        is_valid, msg = validate_event_squads({"squad-1": -1})
        self.assertFalse(is_valid)
        self.assertIn("squad-1", msg)
        self.assertIn("inteiro", msg.lower())

    def test_squads_quantidade_nao_inteiro_invalido(self):
        """Quantidade não inteira é inválida."""
        is_valid, msg = validate_event_squads({"squad-1": 3.5})
        self.assertFalse(is_valid)
        self.assertIn("inteiro", msg.lower())

    def test_squads_quantidade_string_invalida(self):
        """Quantidade como string é inválida."""
        is_valid, msg = validate_event_squads({"squad-1": "5"})
        self.assertFalse(is_valid)
        self.assertIn("inteiro", msg.lower())

    def test_squads_nao_dicionario_invalido(self):
        """Quando não é dicionário retorna erro."""
        is_valid, msg = validate_event_squads([("squad-1", 5)])
        self.assertFalse(is_valid)
        self.assertIn("dicionário", msg.lower())

    def test_squads_nao_dicionario_string_invalido(self):
        """Quando é string retorna erro."""
        is_valid, msg = validate_event_squads("squad-1")
        self.assertFalse(is_valid)


class TestNormalizeEventName(unittest.TestCase):
    """Testa normalização de nome."""

    def test_normalizar_remove_espacos_inicio(self):
        """Remove espaços do início."""
        result = normalize_event_name("  Culto")
        self.assertEqual(result, "Culto")

    def test_normalizar_remove_espacos_fim(self):
        """Remove espaços do fim."""
        result = normalize_event_name("Culto  ")
        self.assertEqual(result, "Culto")

    def test_normalizar_remove_espacos_ambos(self):
        """Remove espaços de ambos os lados."""
        result = normalize_event_name("  Culto Domingo  ")
        self.assertEqual(result, "Culto Domingo")

    def test_normalizar_preserva_espacos_internos(self):
        """Preserva espaços entre palavras."""
        result = normalize_event_name("  Culto   Domingo  ")
        self.assertEqual(result, "Culto   Domingo")

    def test_normalizar_vazio_retorna_vazio(self):
        """Entrada vazia retorna vazia."""
        result = normalize_event_name("")
        self.assertEqual(result, "")

    def test_normalizar_none_retorna_vazio(self):
        """None retorna vazio."""
        result = normalize_event_name(None)
        self.assertEqual(result, "")


class TestNormalizeTime(unittest.TestCase):
    """Testa normalização de horário."""

    def test_normalizar_sem_zero_padding(self):
        """Adiciona zero padding quando falta."""
        result = normalize_time("9:5")
        self.assertEqual(result, "09:05")

    def test_normalizar_com_zero_padding(self):
        """Preserva quando já tem padding."""
        result = normalize_time("09:05")
        self.assertEqual(result, "09:05")

    def test_normalizar_hora_10(self):
        """Hora 10 não recebe padding extra."""
        result = normalize_time("10:30")
        self.assertEqual(result, "10:30")

    def test_normalizar_minuto_10(self):
        """Minuto 10 não recebe padding extra."""
        result = normalize_time("9:10")
        self.assertEqual(result, "09:10")

    def test_normalizar_sem_dois_pontos_retorna_original(self):
        """Formato inválido retorna original."""
        result = normalize_time("9305")
        self.assertEqual(result, "9305")

    def test_normalizar_vazio_retorna_vazio(self):
        """Vazio retorna vazio."""
        result = normalize_time("")
        self.assertEqual(result, "")

    def test_normalizar_none_retorna_none(self):
        """None retorna None."""
        result = normalize_time(None)
        self.assertIsNone(result)


class TestNormalizeDate(unittest.TestCase):
    """Testa normalização de data para ISO."""

    def test_normalizar_dd_mm_yyyy_para_iso(self):
        """Converte DD/MM/YYYY para YYYY-MM-DD."""
        result = normalize_date("25/12/2024")
        self.assertEqual(result, "2024-12-25")

    def test_normalizar_com_espacos(self):
        """Remove espaços e converte."""
        result = normalize_date("  25/12/2024  ")
        self.assertEqual(result, "2024-12-25")

    def test_normalizar_single_digit_padroniza(self):
        """Padroniza single digits com zero padding."""
        result = normalize_date("5/3/2024")
        self.assertEqual(result, "2024-03-05")

    def test_normalizar_vazio_retorna_none(self):
        """Vazio retorna None."""
        result = normalize_date("")
        self.assertIsNone(result)

    def test_normalizar_none_retorna_none(self):
        """None retorna None."""
        result = normalize_date(None)
        self.assertIsNone(result)

    def test_normalizar_apenas_espacos_retorna_none(self):
        """Apenas espaços retorna None."""
        result = normalize_date("   ")
        self.assertIsNone(result)

    def test_normalizar_formato_invalido_retorna_none(self):
        """Formato inválido retorna None (sem raise)."""
        result = normalize_date("25-12-2024")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
