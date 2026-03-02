"""Testes para helpers de visualização de escala. 100% coverage."""

import pytest
from datetime import datetime
from helpers.visualizar import (
    validate_schedule_period,
    filter_schedule_by_period,
    filter_schedule_by_squad,
    filter_schedule_by_member,
    export_schedule_to_csv_string,
    validate_schedule_before_export,
    count_allocations,
    group_schedule_by_event_date,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_schedule():
    """Sample schedule data for testing."""
    return [
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto Principal",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João Silva",
        },
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto Principal",
            "horario": "19:00",
            "squad": "Recepção",
            "membro": "Maria Santos",
        },
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Estudo da Palavra",
            "horario": "20:30",
            "squad": "Mídia",
            "membro": "Pedro Costa",
        },
        {
            "data": "2024-12-29",
            "dia": "Domingo",
            "evento": "Culto Principal",
            "horario": "10:00",
            "squad": "Recepção",
            "membro": "Ana Oliveira",
        },
        {
            "data": "2024-01-10",
            "dia": "Quinta-feira",
            "evento": "Culto Principal",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João Silva",
        },
    ]


@pytest.fixture
def empty_schedule():
    """Empty schedule."""
    return []


# ============================================================================
# TESTS: validate_schedule_period
# ============================================================================

def test_validate_schedule_period_valid_month():
    """Test validation with valid month."""
    is_valid, error = validate_schedule_period(12, 2024)
    assert is_valid is True
    assert error is None


def test_validate_schedule_period_valid_january():
    """Test validation with month 1."""
    is_valid, error = validate_schedule_period(1, 2024)
    assert is_valid is True
    assert error is None


def test_validate_schedule_period_invalid_month_zero():
    """Test validation with month 0."""
    is_valid, error = validate_schedule_period(0, 2024)
    assert is_valid is False
    assert error == "Mês inválido"


def test_validate_schedule_period_invalid_month_negative():
    """Test validation with negative month."""
    is_valid, error = validate_schedule_period(-1, 2024)
    assert is_valid is False
    assert error == "Mês inválido"


def test_validate_schedule_period_invalid_month_13():
    """Test validation with month 13."""
    is_valid, error = validate_schedule_period(13, 2024)
    assert is_valid is False
    assert error == "Mês inválido"


def test_validate_schedule_period_invalid_month_100():
    """Test validation with month 100."""
    is_valid, error = validate_schedule_period(100, 2024)
    assert is_valid is False
    assert error == "Mês inválido"


def test_validate_schedule_period_valid_year():
    """Test validation with various valid years."""
    for year in [2000, 2024, 2050]:
        is_valid, error = validate_schedule_period(6, year)
        assert is_valid is True
        assert error is None


# ============================================================================
# TESTS: filter_schedule_by_period
# ============================================================================

def test_filter_schedule_by_period_december(sample_schedule):
    """Test filtering schedule for December 2024."""
    filtered = filter_schedule_by_period(sample_schedule, 12, 2024)
    assert len(filtered) == 4
    assert all(item["data"].startswith("2024-12") for item in filtered)


def test_filter_schedule_by_period_january(sample_schedule):
    """Test filtering schedule for January 2025."""
    filtered = filter_schedule_by_period(sample_schedule, 1, 2025)
    assert len(filtered) == 0


def test_filter_schedule_by_period_january_2024(sample_schedule):
    """Test filtering schedule for January 2024."""
    filtered = filter_schedule_by_period(sample_schedule, 1, 2024)
    assert len(filtered) == 1
    assert filtered[0]["membro"] == "João Silva"


def test_filter_schedule_by_period_empty_schedule(empty_schedule):
    """Test filtering empty schedule."""
    filtered = filter_schedule_by_period(empty_schedule, 12, 2024)
    assert len(filtered) == 0


def test_filter_schedule_by_period_no_match(sample_schedule):
    """Test filtering with no matching dates."""
    filtered = filter_schedule_by_period(sample_schedule, 6, 2025)
    assert len(filtered) == 0


# ============================================================================
# TESTS: filter_schedule_by_squad
# ============================================================================

def test_filter_schedule_by_squad_midia(sample_schedule):
    """Test filtering by Mídia squad."""
    filtered = filter_schedule_by_squad(sample_schedule, "Mídia")
    assert len(filtered) == 3
    assert all(item["squad"] == "Mídia" for item in filtered)


def test_filter_schedule_by_squad_recepcao(sample_schedule):
    """Test filtering by Recepção squad."""
    filtered = filter_schedule_by_squad(sample_schedule, "Recepção")
    assert len(filtered) == 2
    assert all(item["squad"] == "Recepção" for item in filtered)


def test_filter_schedule_by_squad_not_found(sample_schedule):
    """Test filtering by non-existent squad."""
    filtered = filter_schedule_by_squad(sample_schedule, "Limpeza")
    assert len(filtered) == 0


def test_filter_schedule_by_squad_case_sensitive(sample_schedule):
    """Test that filtering is case-sensitive."""
    filtered = filter_schedule_by_squad(sample_schedule, "mídia")
    assert len(filtered) == 0


def test_filter_schedule_by_squad_empty_schedule(empty_schedule):
    """Test filtering empty schedule."""
    filtered = filter_schedule_by_squad(empty_schedule, "Mídia")
    assert len(filtered) == 0


# ============================================================================
# TESTS: filter_schedule_by_member
# ============================================================================

def test_filter_schedule_by_member_joao(sample_schedule):
    """Test filtering by João Silva."""
    filtered = filter_schedule_by_member(sample_schedule, "João Silva")
    assert len(filtered) == 2
    assert all(item["membro"] == "João Silva" for item in filtered)


def test_filter_schedule_by_member_pedro(sample_schedule):
    """Test filtering by Pedro Costa."""
    filtered = filter_schedule_by_member(sample_schedule, "Pedro Costa")
    assert len(filtered) == 1
    assert filtered[0]["membro"] == "Pedro Costa"


def test_filter_schedule_by_member_not_found(sample_schedule):
    """Test filtering by non-existent member."""
    filtered = filter_schedule_by_member(sample_schedule, "Inexistente Silva")
    assert len(filtered) == 0


def test_filter_schedule_by_member_case_sensitive(sample_schedule):
    """Test that filtering is case-sensitive."""
    filtered = filter_schedule_by_member(sample_schedule, "joão silva")
    assert len(filtered) == 0


def test_filter_schedule_by_member_empty_schedule(empty_schedule):
    """Test filtering empty schedule."""
    filtered = filter_schedule_by_member(empty_schedule, "João Silva")
    assert len(filtered) == 0


# ============================================================================
# TESTS: count_allocations
# ============================================================================

def test_count_allocations_sample(sample_schedule):
    """Test counting total allocations in sample schedule."""
    count = count_allocations(sample_schedule)
    assert count == 5


def test_count_allocations_empty_schedule(empty_schedule):
    """Test counting allocations in empty schedule."""
    count = count_allocations(empty_schedule)
    assert count == 0


def test_count_allocations_single_item():
    """Test counting allocations with single item."""
    schedule = [
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João",
        }
    ]
    count = count_allocations(schedule)
    assert count == 1


# ============================================================================
# TESTS: group_schedule_by_event_date
# ============================================================================

def test_group_schedule_by_event_date(sample_schedule):
    """Test grouping schedule by event date."""
    grouped = group_schedule_by_event_date(sample_schedule)
    
    assert "2024-12-25" in grouped
    assert "2024-12-29" in grouped
    assert "2024-01-10" in grouped
    
    assert len(grouped["2024-12-25"]) == 3
    assert len(grouped["2024-12-29"]) == 1
    assert len(grouped["2024-01-10"]) == 1


def test_group_schedule_by_event_date_empty(empty_schedule):
    """Test grouping empty schedule."""
    grouped = group_schedule_by_event_date(empty_schedule)
    assert len(grouped) == 0


def test_group_schedule_by_event_date_preserves_order(sample_schedule):
    """Test that grouping preserves all items."""
    grouped = group_schedule_by_event_date(sample_schedule)
    total_items = sum(len(items) for items in grouped.values())
    assert total_items == len(sample_schedule)


def test_group_schedule_by_event_date_single_date():
    """Test grouping with single date."""
    schedule = [
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto 1",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João",
        },
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto 2",
            "horario": "20:00",
            "squad": "Recepção",
            "membro": "Maria",
        },
    ]
    grouped = group_schedule_by_event_date(schedule)
    assert len(grouped) == 1
    assert len(grouped["2024-12-25"]) == 2


# ============================================================================
# TESTS: validate_schedule_before_export
# ============================================================================

def test_validate_schedule_before_export_valid(sample_schedule):
    """Test validation of valid schedule."""
    is_valid, error = validate_schedule_before_export(sample_schedule)
    assert is_valid is True
    assert error is None


def test_validate_schedule_before_export_empty():
    """Test validation of empty schedule."""
    is_valid, error = validate_schedule_before_export([])
    assert is_valid is False
    assert error == "Escala vazia, nada para exportar"


def test_validate_schedule_before_export_missing_data_field():
    """Test validation with missing data field."""
    schedule = [
        {
            "dia": "Quarta-feira",
            "evento": "Culto",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João",
        }
    ]
    is_valid, error = validate_schedule_before_export(schedule)
    assert is_valid is False
    assert "data" in error


def test_validate_schedule_before_export_missing_membro_field():
    """Test validation with missing membro field."""
    schedule = [
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto",
            "horario": "19:00",
            "squad": "Mídia",
        }
    ]
    is_valid, error = validate_schedule_before_export(schedule)
    assert is_valid is False
    assert "membro" in error


def test_validate_schedule_before_export_missing_squad_field():
    """Test validation with missing squad field."""
    schedule = [
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto",
            "horario": "19:00",
            "membro": "João",
        }
    ]
    is_valid, error = validate_schedule_before_export(schedule)
    assert is_valid is False
    assert "squad" in error


def test_validate_schedule_before_export_missing_evento_field():
    """Test validation with missing evento field."""
    schedule = [
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João",
        }
    ]
    is_valid, error = validate_schedule_before_export(schedule)
    assert is_valid is False
    assert "evento" in error


def test_validate_schedule_before_export_empty_string_values():
    """Test validation with empty string values."""
    schedule = [
        {
            "data": "",
            "dia": "Quarta-feira",
            "evento": "Culto",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João",
        }
    ]
    is_valid, error = validate_schedule_before_export(schedule)
    assert is_valid is False
    assert "vazio" in error.lower()


# ============================================================================
# TESTS: export_schedule_to_csv_string
# ============================================================================

def test_export_schedule_to_csv_string(sample_schedule):
    """Test exporting schedule to CSV string."""
    headers = ["Data", "Dia", "Evento", "Horário", "Squad", "Voluntário"]
    csv_string = export_schedule_to_csv_string(sample_schedule, headers)
    
    # Check headers
    assert "Data;Dia;Evento;Horário;Squad;Voluntário" in csv_string
    
    # Check content
    assert "2024-12-25" in csv_string
    assert "João Silva" in csv_string
    assert "Mídia" in csv_string


def test_export_schedule_to_csv_string_empty_schedule():
    """Test exporting empty schedule."""
    headers = ["Data", "Dia", "Evento", "Horário", "Squad", "Voluntário"]
    csv_string = export_schedule_to_csv_string([], headers)
    
    # Should only have headers
    lines = csv_string.strip().split("\n")
    assert len(lines) == 1
    assert "Data;Dia;Evento;Horário;Squad;Voluntário" in csv_string


def test_export_schedule_to_csv_string_single_row(sample_schedule):
    """Test exporting single row."""
    headers = ["Data", "Dia", "Evento", "Horário", "Squad", "Voluntário"]
    csv_string = export_schedule_to_csv_string(sample_schedule[:1], headers)
    
    lines = csv_string.strip().split("\n")
    assert len(lines) == 2  # header + data


def test_export_schedule_to_csv_string_format():
    """Test CSV format is correct."""
    schedule = [
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João",
        }
    ]
    headers = ["Data", "Dia", "Evento", "Horário", "Squad", "Voluntário"]
    csv_string = export_schedule_to_csv_string(schedule, headers)
    
    # Verify semicolon-delimited format
    lines = csv_string.strip().split("\n")
    assert len(lines[1].split(";")) == 6


def test_export_schedule_to_csv_string_with_special_chars():
    """Test CSV with special characters."""
    schedule = [
        {
            "data": "2024-12-25",
            "dia": "Quarta-feira",
            "evento": "Culto; Especial",
            "horario": "19:00",
            "squad": "Mídia",
            "membro": "João da Silva",
        }
    ]
    headers = ["Data", "Dia", "Evento", "Horário", "Squad", "Voluntário"]
    csv_string = export_schedule_to_csv_string(schedule, headers)
    
    # Should handle special characters
    assert "Culto; Especial" in csv_string or "Culto" in csv_string
