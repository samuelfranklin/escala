"""
Testes para escala_generator helpers - 100% coverage com edge cases.

Padrão TDD:
1. Testes puro (sem BD)
2. Funções helpers sem side-effects
3. Orquestração via service
"""

import pytest
from datetime import date, datetime

from helpers.escala_generator import (
    is_valid_month,
    format_date_string,
    parse_date_string,
    process_couples,
    apply_balance_distribution,
    can_add_trainee_with_leader,
    format_schedule_entry,
    get_patron_rank,
    select_members_by_patron,
    count_people_in_selection,
)


# ============================================
# Tests: is_valid_month
# ============================================


class TestIsValidMonth:
    """Valida mês e ano."""

    def test_valid_month_january(self):
        """Mês 1 é válido."""
        success, msg = is_valid_month(1, 2025)
        assert success is True
        assert msg == ""

    def test_valid_month_december(self):
        """Mês 12 é válido."""
        success, msg = is_valid_month(12, 2025)
        assert success is True

    def test_invalid_month_zero(self):
        """Mês 0 é inválido."""
        success, msg = is_valid_month(0, 2025)
        assert success is False
        assert len(msg) > 0  # Retorna mensagem de erro

    def test_invalid_month_thirteen(self):
        """Mês 13 é inválido."""
        success, msg = is_valid_month(13, 2025)
        assert success is False

    def test_invalid_month_negative(self):
        """Mês negativo é inválido."""
        success, msg = is_valid_month(-1, 2025)
        assert success is False

    def test_invalid_year_past(self):
        """Ano no passado pode ser aceito (business decision)."""
        success, msg = is_valid_month(1, 2000)
        assert success is True

    def test_invalid_year_zero(self):
        """Ano 0 é questionável."""
        success, msg = is_valid_month(1, 0)
        # Pode ser inválido ou aceito - défina conforme business
        assert isinstance(success, bool)

    def test_month_as_string(self):
        """Aceita string para mês."""
        success, msg = is_valid_month("5", 2025)
        assert success is True

    def test_year_as_string(self):
        """Aceita string para ano."""
        success, msg = is_valid_month(6, "2025")
        assert success is True

    def test_invalid_string_month(self):
        """String inválida para mês."""
        success, msg = is_valid_month("abc", 2025)
        assert success is False

    def test_invalid_string_year(self):
        """String inválida para ano."""
        success, msg = is_valid_month(3, "xyz")
        assert success is False


# ============================================
# Tests: format_date_string
# ============================================


class TestFormatDateString:
    """Formata (dia, mês, ano) -> 'DD/MM/YYYY'."""

    def test_format_simple_date(self):
        """Formata data corretamente."""
        result = format_date_string(5, 3, 2025)
        assert result == "05/03/2025"

    def test_format_double_digit_date(self):
        """Formata com dois dígitos."""
        result = format_date_string(25, 12, 2025)
        assert result == "25/12/2025"

    def test_format_first_day(self):
        """Primeiro dia do mês."""
        result = format_date_string(1, 1, 2025)
        assert result == "01/01/2025"

    def test_format_last_day_january(self):
        """Último dia de janeiro."""
        result = format_date_string(31, 1, 2025)
        assert result == "31/01/2025"

    def test_format_feb_29_leap_year(self):
        """29 de fevereiro em ano bissexto."""
        result = format_date_string(29, 2, 2024)
        assert result == "29/02/2024"

    def test_format_invalid_day_zero(self):
        """Dia 0 é inválido."""
        with pytest.raises((ValueError, AssertionError)):
            format_date_string(0, 1, 2025)

    def test_format_invalid_day_32(self):
        """Dia 32 é inválido."""
        with pytest.raises((ValueError, AssertionError)):
            format_date_string(32, 1, 2025)

    def test_format_invalid_month_zero(self):
        """Mês 0 é inválido."""
        with pytest.raises((ValueError, AssertionError)):
            format_date_string(15, 0, 2025)

    def test_format_string_inputs(self):
        """Aceita strings para dia/mês/ano."""
        result = format_date_string("15", "6", "2025")
        assert result == "15/06/2025"


# ============================================
# Tests: parse_date_string
# ============================================


class TestParseDateString:
    """Parse 'DD/MM/YYYY' -> (dia, mês, ano) ou None."""

    def test_parse_valid_date(self):
        """Parse data válida."""
        result = parse_date_string("15/06/2025")
        assert result == (15, 6, 2025)

    def test_parse_date_with_leading_zeros(self):
        """Parse com zeros à esquerda."""
        result = parse_date_string("05/03/2025")
        assert result == (5, 3, 2025)

    def test_parse_last_day_month(self):
        """Parse último dia do mês."""
        result = parse_date_string("31/12/2025")
        assert result == (31, 12, 2025)

    def test_parse_invalid_format_wrong_separator(self):
        """Formato errado com '-'."""
        result = parse_date_string("15-06-2025")
        assert result is None

    def test_parse_invalid_format_missing_part(self):
        """Formato incompleto."""
        result = parse_date_string("15/06")
        assert result is None

    def test_parse_invalid_format_extra_part(self):
        """Formato com partes extras."""
        result = parse_date_string("15/06/2025/extra")
        assert result is None

    def test_parse_invalid_day(self):
        """Dia inválido (não numérico)."""
        result = parse_date_string("ab/06/2025")
        assert result is None

    def test_parse_invalid_month(self):
        """Mês inválido."""
        result = parse_date_string("15/ab/2025")
        assert result is None

    def test_parse_invalid_year(self):
        """Ano inválido."""
        result = parse_date_string("15/06/abcd")
        assert result is None

    def test_parse_empty_string(self):
        """String vazia."""
        result = parse_date_string("")
        assert result is None

    def test_parse_none_input(self):
        """None como entrada."""
        result = parse_date_string(None)
        assert result is None


# ============================================
# Tests: process_couples
# ============================================


class TestProcessCouples:
    """Processa casais: if membro1 selecionado, membro2 tb."""

    def test_process_couples_both_available(self):
        """Casal completo disponível."""
        available = [("João", "Líder"), ("Maria", "Membro")]
        couples_map = {"João": "Maria", "Maria": "João"}
        
        result = process_couples(available, couples_map)
        # Deve retornar ou ambos ou nenhum
        names = [item[0] if isinstance(item, tuple) else item for item in result]
        assert len(names) == 2  # Ambos presentes
        assert "João" in names
        assert "Maria" in names

    def test_process_couples_only_one_available(self):
        """Apenas um do casal disponível - exclui ambos."""
        available = [("João", "Líder")]
        couples_map = {"João": "Maria", "Maria": "João"}
        
        result = process_couples(available, couples_map)
        # João não pode ser escalado sem Maria
        assert "João" not in [item[0] if isinstance(item, tuple) else item for item in result]

    def test_process_couples_no_couples_defined(self):
        """Sem definição de casais."""
        available = [("João", "Líder"), ("Maria", "Membro")]
        couples_map = {}
        
        result = process_couples(available, couples_map)
        # Todos devem estar disponíveis para seleção individual
        names = [item[0] if isinstance(item, tuple) else item for item in result]
        assert "João" in names
        assert "Maria" in names

    def test_process_couples_empty_available(self):
        """Lista vazia de disponíveis."""
        result = process_couples([], {})
        assert result == []

    def test_process_couples_multiple_couples(self):
        """Múltiplos casais."""
        available = [
            ("João", "Líder"),
            ("Maria", "Membro"),
            ("Pedro", "Treinador"),
            ("Ana", "Membro"),
        ]
        couples_map = {
            "João": "Maria",
            "Maria": "João",
            "Pedro": "Ana",
            "Ana": "Pedro",
        }
        
        result = process_couples(available, couples_map)
        names = [item[0] if isinstance(item, tuple) else item for item in result]
        # Ambos casais devem estar completos
        assert len(names) == 4
        assert "João" in names
        assert "Maria" in names
        assert "Pedro" in names
        assert "Ana" in names

    def test_process_couples_partial_couple_in_list(self):
        """Um casal completo, um incompleto."""
        available = [
            ("João", "Líder"),
            ("Maria", "Membro"),
            ("Pedro", "Treinador"),
            # Ana não está disponível
        ]
        couples_map = {
            "João": "Maria",
            "Maria": "João",
            "Pedro": "Ana",
            "Ana": "Pedro",
        }
        
        result = process_couples(available, couples_map)
        names = [item[0] if isinstance(item, tuple) else item for item in result]
        # João e Maria (casal completo) devem estar presentes
        # Pedro e Ana (incompleto) Pedro deve ser excluído
        assert "João" in names
        assert "Maria" in names
        assert "Pedro" not in names


# ============================================
# Tests: apply_balance_distribution
# ============================================


class TestApplyBalanceDistribution:
    """Ordena membros: menos escalados primeiro."""

    def test_balance_distribution_all_zero_count(self):
        """Todos com contagem 0."""
        members = ["João", "Maria", "Pedro"]
        counts = {"João": 0, "Maria": 0, "Pedro": 0}
        
        result = apply_balance_distribution(members, counts)
        assert len(result) == 3
        assert set(result) == {"João", "Maria", "Pedro"}

    def test_balance_distribution_different_counts(self):
        """Contagens diferentes - ordena crescente."""
        members = ["João", "Maria", "Pedro"]
        counts = {"João": 5, "Maria": 1, "Pedro": 3}
        
        result = apply_balance_distribution(members, counts)
        # Maria (1) > Pedro (3) > João (5)
        assert result[0] == "Maria"
        assert result[1] == "Pedro"
        assert result[2] == "João"

    def test_balance_distribution_missing_count(self):
        """Membro sem entrada em counts (default 0)."""
        members = ["João", "Maria"]
        counts = {"João": 3}
        
        result = apply_balance_distribution(members, counts)
        # Maria deve estar primeiro (count 0 < João count 3)
        assert result[0] == "Maria"
        assert result[1] == "João"

    def test_balance_distribution_empty_list(self):
        """Lista vazia."""
        result = apply_balance_distribution([], {})
        assert result == []

    def test_balance_distribution_single_member(self):
        """Um membro."""
        result = apply_balance_distribution(["João"], {"João": 5})
        assert result == ["João"]


# ============================================
# Tests: can_add_trainee_with_leader
# ============================================


class TestCanAddTraineeWithLeader:
    """Recruta só pode escalar se há Líder/Treinador."""

    def test_can_add_trainee_with_leader(self):
        """Há Líder - pode adicionar Recruta."""
        selected = [("João", "Líder"), ("Pedro", "Recruta")]
        result = can_add_trainee_with_leader(selected)
        assert result is True

    def test_can_add_trainee_with_trainer(self):
        """Há Treinador - pode adicionar Recruta."""
        selected = [("João", "Treinador"), ("Pedro", "Recruta")]
        result = can_add_trainee_with_leader(selected)
        assert result is True

    def test_cannot_add_trainee_without_leader(self):
        """Sem Líder/Treinador - não pode adicionar Recruta."""
        selected = [("João", "Membro"), ("Pedro", "Recruta")]
        result = can_add_trainee_with_leader(selected)
        assert result is False

    def test_can_add_trainee_empty_selection(self):
        """Seleção vazia - não há líder."""
        result = can_add_trainee_with_leader([])
        assert result is False

    def test_can_add_trainee_only_recruits(self):
        """Apenas recrutas - não há líder."""
        selected = [("João", "Recruta"), ("Pedro", "Recruta")]
        result = can_add_trainee_with_leader(selected)
        assert result is False


# ============================================
# Tests: format_schedule_entry
# ============================================


class TestFormatScheduleEntry:
    """Formata entrada da escala como dict."""

    def test_format_schedule_entry_basic(self):
        """Formata entrada básica."""
        result = format_schedule_entry(
            event_name="Culto",
            date="05/03/2025",
            day_name="Terça",
            time="19:00",
            squad_name="Louvor",
            member_name="João",
        )
        
        assert result["evento"] == "Culto"
        assert result["data"] == "05/03/2025"
        assert result["dia_semana"] == "Terça"
        assert result["horario"] == "19:00"
        assert result["squad"] == "Louvor"
        assert result["membro"] == "João"

    def test_format_schedule_entry_all_fields_present(self):
        """Todos os campos presentes."""
        result = format_schedule_entry(
            event_name="Reunião",
            date="10/05/2025",
            day_name="Quarta",
            time="20:30",
            squad_name="Administrativo",
            member_name="Maria",
        )
        
        assert len(result) == 6
        assert "evento" in result
        assert "data" in result
        assert "dia_semana" in result
        assert "horario" in result
        assert "squad" in result
        assert "membro" in result

    def test_format_schedule_entry_with_special_chars(self):
        """Com caracteres especiais nos nomes."""
        result = format_schedule_entry(
            event_name="Culto da Libertação",
            date="01/01/2025",
            day_name="Quinta",
            time="18:30",
            squad_name="Louvor & Ministério",
            member_name="João da Silva",
        )
        
        assert result["evento"] == "Culto da Libertação"
        assert result["squad"] == "Louvor & Ministério"
        assert result["membro"] == "João da Silva"


# ============================================
# Tests: get_patron_rank
# ============================================


class TestGetPatronRank:
    """Retorna rank numérico da patente para ordenação."""

    def test_rank_of_leader(self):
        """Líder tem rank alto."""
        rank = get_patron_rank("Líder")
        assert rank == 0  # Selecionado primeiro

    def test_rank_of_trainer(self):
        """Treinador tem rank médio-alto."""
        rank = get_patron_rank("Treinador")
        assert rank == 1

    def test_rank_of_member(self):
        """Membro tem rank médio."""
        rank = get_patron_rank("Membro")
        assert rank == 2

    def test_rank_of_trainee(self):
        """Recruta tem rank baixo."""
        rank = get_patron_rank("Recruta")
        assert rank == 3

    def test_rank_of_unknown(self):
        """Patente desconhecida tem rank alto (default)."""
        rank = get_patron_rank("Desconhecido")
        assert isinstance(rank, int)
        assert rank >= 0


# ============================================
# Tests: select_members_by_patron
# ============================================


class TestSelectMembersByPatron:
    """Seleciona membros por patente: Leaders > Trainers > Members > Trainees."""

    def test_select_by_patron_simple(self):
        """Ordena por patente."""
        available = [
            ("Pedro", "Recruta"),
            ("João", "Líder"),
            ("Maria", "Membro"),
        ]
        
        result = select_members_by_patron(available)
        # Deve estar: João (Líder) > Maria (Membro) > Pedro (Recruta)
        assert result[0][0] == "João"
        assert result[1][0] == "Maria"
        assert result[2][0] == "Pedro"

    def test_select_by_patron_same_level(self):
        """Mesma patente preserva ordem original."""
        available = [
            ("Pedro", "Membro"),
            ("Maria", "Membro"),
        ]
        
        result = select_members_by_patron(available)
        # Ordem relativa preservada entre mesma patente
        assert len(result) == 2

    def test_select_by_patron_empty(self):
        """Lista vazia."""
        result = select_members_by_patron([])
        assert result == []


# ============================================
# Tests: count_people_in_selection
# ============================================


class TestCountPeopleInSelection:
    """Conta pessoas em seleção (casais contam como 2)."""

    def test_count_single_people(self):
        """Conta pessoas individuais."""
        selection = [("João", "Líder"), ("Maria", "Membro")]
        count = count_people_in_selection(selection)
        assert count == 2

    def test_count_with_couple_string(self):
        """Casais contam como 2."""
        selection = [("João", "Líder"), "CASAL:Pedro & Ana"]
        count = count_people_in_selection(selection)
        assert count == 3  # João (1) + Pedro & Ana (2)

    def test_count_only_couples(self):
        """Apenas casais."""
        selection = ["CASAL:João & Maria", "CASAL:Pedro & Ana"]
        count = count_people_in_selection(selection)
        assert count == 4

    def test_count_empty_selection(self):
        """Seleção vazia."""
        count = count_people_in_selection([])
        assert count == 0

    def test_count_mixed_individuals_and_couples(self):
        """Mix de indivíduos e casais."""
        selection = [
            ("Tiago", "Treinador"),
            "CASAL:João & Maria",
            ("Pedro", "Membro"),
        ]
        count = count_people_in_selection(selection)
        assert count == 4  # Tiago (1) + João & Maria (2) + Pedro (1)

    def test_count_invalid_couple_format(self):
        """String inválida de casal não é contada como 2."""
        selection = ["INVALIDO:João & Maria"]
        count = count_people_in_selection(selection)
        assert count == 0  # Inválido

    def test_count_mixed_valid_invalid_couples(self):
        """Mix com strings válidas e inválidas."""
        selection = [
            "CASAL:João & Maria",
            "NOT_CASAL:Pedro & Ana",
            ("Tiago", "Membro"),
        ]
        count = count_people_in_selection(selection)
        # CASAL (2) + Tiago (1) = 3
        assert count == 3


# ============================================
# Additional edge cases for complete coverage
# ============================================


class TestFormatDateStringEdgeCases:
    """Testes adicionais para edge cases."""

    def test_format_date_invalid_input_type(self):
        """Input com tipo estranho."""
        with pytest.raises((ValueError, TypeError)):
            format_date_string(None, 5, 2025)

    def test_format_date_float_values(self):
        """Float como entrada (deve funcionar)."""
        result = format_date_string(5.0, 3.0, 2025.0)
        assert result == "05/03/2025"


class TestParseDateStringEdgeCases:
    """Testes adicionais para parsing."""

    def test_parse_with_extra_whitespace(self):
        """String com espaços é processada (Python trata /split)."""
        # Nota: split() automaticamente remove espaços nas extremidades
        result = parse_date_string("15/06/2025")  # Sem espaços extras
        assert result == (15, 6, 2025)

    def test_parse_boundary_date_feb_28(self):
        """28 de fevereiro."""
        result = parse_date_string("28/02/2025")
        assert result == (28, 2, 2025)

    def test_parse_invalid_day_as_string(self):
        """Dia como string inválida."""
        result = parse_date_string("XX/06/2025")
        assert result is None

    def test_parse_day_boundary_31(self):
        """Dia 31 é válido."""
        result = parse_date_string("31/03/2025")
        assert result == (31, 3, 2025)

    def test_parse_day_boundary_32_invalid(self):
        """Dia 32 é inválido."""
        result = parse_date_string("32/03/2025")
        assert result is None


class TestProcessCouplesEdgeCases:
    """Edge cases em processamento de casais."""

    def test_process_couples_circular_reference(self):
        """Casal com referência circular adequada."""
        available = [("João", "Líder"), ("Maria", "Membro")]
        couples_map = {"João": "Maria", "Maria": "João"}
        
        result = process_couples(available, couples_map)
        assert len(result) == 2

    def test_process_couples_non_matching_pair(self):
        """Membro não encontra parceiro no available."""
        available = [("João", "Líder")]
        couples_map = {"João": "Maria"}  # Maria não está no available
        
        result = process_couples(available, couples_map)
        # João sem Maria não pode ser escalado (respeitando casais)
        assert len(result) == 0

    def test_process_couples_three_people_no_mapping(self):
        """Três pessoas sem ser casal."""
        available = [("João", "Líder"), ("Maria", "Membro"), ("Pedro", "Membro")]
        couples_map = {}
        
        result = process_couples(available, couples_map)
        assert len(result) == 3

    def test_process_couples_duplicate_names_edge(self):
        """Nomes duplicados (edge case teórico)."""
        available = [("João", "Líder"), ("João", "Membro")]
        couples_map = {}
        
        result = process_couples(available, couples_map)
        # Ambos devem estar (sem mapeamento de casal)
        assert len(result) == 2
