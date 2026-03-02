"""
Testes TDD para helpers de disponibilidade.

RED → GREEN → REFACTOR workflow.
Todos os testes começam VERMELHOS (funções não existem).
"""

from datetime import date, datetime, timedelta
import pytest

from helpers.disponibilidade import (
    parse_date_string,
    format_date_to_display,
    is_date_in_future,
    validate_restriction_date,
    MemberRestrictionError,
)


class TestParseDateString:
    """Testes para parse_date_string: converte 'DD/MM/YYYY' para date."""

    def test_parse_valid_date_returns_date_object(self):
        """Deve converter '01/01/2025' em date(2025, 1, 1)."""
        result = parse_date_string("01/01/2025")
        assert result == date(2025, 1, 1)
        assert isinstance(result, date)

    def test_parse_valid_date_different_month(self):
        """Deve converter '25/12/2024' em date(2024, 12, 25)."""
        result = parse_date_string("25/12/2024")
        assert result == date(2024, 12, 25)

    def test_parse_invalid_format_raises_error(self):
        """Deve lancar MemberRestrictionError para formato invalido."""
        with pytest.raises(MemberRestrictionError) as exc_info:
            parse_date_string("2025-01-01")  # Formato ISO
        assert "DD/MM/YYYY" in str(exc_info.value)

    def test_parse_invalid_date_raises_error(self):
        """Deve lancar MemberRestrictionError para data invalida (ex: 31/02)."""
        with pytest.raises(MemberRestrictionError) as exc_info:
            parse_date_string("31/02/2025")
        # Mensagem contém "inválido" ou "formato inválido"
        error_msg = str(exc_info.value).lower()
        assert "inválido" in error_msg or "formato" in error_msg

    def test_parse_empty_string_raises_error(self):
        """Deve lancar MemberRestrictionError para string vazia."""
        with pytest.raises(MemberRestrictionError):
            parse_date_string("")

    def test_parse_none_raises_error(self):
        """Deve lancar MemberRestrictionError para None."""
        with pytest.raises((MemberRestrictionError, TypeError)):
            parse_date_string(None)

    def test_parse_leading_trailing_spaces_should_work(self):
        """Deve aceitar strings com espaços nas pontas."""
        result = parse_date_string("  01/01/2025  ")
        assert result == date(2025, 1, 1)


class TestFormatDateToDisplay:
    """Testes para format_date_to_display: converte date para 'DD/MM/YYYY'."""

    def test_format_date_object_to_string(self):
        """Deve converter date(2025, 1, 1) em '01/01/2025'."""
        d = date(2025, 1, 1)
        result = format_date_to_display(d)
        assert result == "01/01/2025"

    def test_format_date_with_single_digit_day_is_padded(self):
        """Dia 1 deve ser '01', não '1'."""
        d = date(2025, 1, 5)
        result = format_date_to_display(d)
        assert result == "05/01/2025"

    def test_format_date_with_single_digit_month_is_padded(self):
        """Mês 1 deve ser '01', não '1'."""
        d = date(2025, 3, 15)
        result = format_date_to_display(d)
        assert result == "15/03/2025"

    def test_format_different_dates(self):
        """Testa conversão de varias datas."""
        cases = [
            (date(2024, 12, 25), "25/12/2024"),
            (date(2025, 6, 10), "10/06/2025"),
            (date(2023, 1, 31), "31/01/2023"),
        ]
        for d, expected in cases:
            assert format_date_to_display(d) == expected


class TestIsDateInFuture:
    """Testes para is_date_in_future: verifica se data nao esta no passado."""

    def test_future_date_returns_true(self):
        """Data amanha retorna True."""
        tomorrow = date.today() + timedelta(days=1)
        assert is_date_in_future(tomorrow) is True

    def test_today_returns_true(self):
        """Data de hoje retorna True (pode usar hoje)."""
        today = date.today()
        assert is_date_in_future(today) is True

    def test_yesterday_returns_false(self):
        """Data ontem retorna False."""
        yesterday = date.today() - timedelta(days=1)
        assert is_date_in_future(yesterday) is False

    def test_far_future_returns_true(self):
        """Data muito distante no futuro retorna True."""
        far_future = date.today() + timedelta(days=365)
        assert is_date_in_future(far_future) is True

    def test_far_past_returns_false(self):
        """Data distante no passado retorna False."""
        far_past = date.today() - timedelta(days=365)
        assert is_date_in_future(far_past) is False


class TestValidateRestrictionDate:
    """Testes para validate_restriction_date: validacao combinada."""

    def test_valid_future_date_returns_date(self):
        """Data valida e futura retorna o date object."""
        date_str = (date.today() + timedelta(days=1)).strftime("%d/%m/%Y")
        result = validate_restriction_date(date_str)
        assert isinstance(result, date)

    def test_valid_today_returns_date(self):
        """Data de hoje retorna date object."""
        date_str = date.today().strftime("%d/%m/%Y")
        result = validate_restriction_date(date_str)
        assert isinstance(result, date)

    def test_invalid_format_raises_error(self):
        """Formato invalido lanca MemberRestrictionError."""
        with pytest.raises(MemberRestrictionError) as exc_info:
            validate_restriction_date("invalid-date")
        assert "Formato" in str(exc_info.value) or "formato" in str(exc_info.value).lower()

    def test_past_date_raises_error(self):
        """Data no passado lanca MemberRestrictionError."""
        past_date_str = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        with pytest.raises(MemberRestrictionError) as exc_info:
            validate_restriction_date(past_date_str)
        assert "passado" in str(exc_info.value).lower() or "past" in str(exc_info.value).lower()

    def test_error_message_references_date_value(self):
        """Mensagem de erro inclui a data que foi rejeitada."""
        with pytest.raises(MemberRestrictionError) as exc_info:
            validate_restriction_date("99/99/9999")
        # Verifica que alguma informacao sobre a data invalida esta na msg
        error_msg = str(exc_info.value).lower()
        assert "99" in error_msg or "invalida" in error_msg or "invalid" in error_msg
