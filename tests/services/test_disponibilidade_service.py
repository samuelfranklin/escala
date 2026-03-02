"""
Testes de integração para DisponibilidadeService.

Testa orquestra de helpers + BD via session_scope.
"""

from datetime import date, timedelta
import pytest

from infra.database import Member, MemberRestrictions, session_scope, create_tables
from services.disponibilidade_service import DisponibilidadeService
from helpers.disponibilidade import MemberRestrictionError


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Cria tabelas frescas para cada teste."""
    create_tables()
    yield
    # Limpeza (opcional: pode ser feita via session delete)


@pytest.fixture
def test_member():
    """Cria um membro de teste."""
    with session_scope() as session:
        member = Member(id="test-member-1", name="João Teste", status=True)
        session.add(member)
        session.flush()
        member_id = member.id
    return member_id


class TestCreateRestriction:
    """Testes para crear restrição de disponibilidade."""

    def test_create_restriction_with_valid_date(self, test_member):
        """Deve criar restrição com data valida e futura."""
        future_date_str = (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")

        result = DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str=future_date_str,
            description="Férias",
        )

        assert result["success"] is True
        assert "criada" in result["message"].lower()
        assert result["restriction_id"] is not None

        # Verificar que foi persistido
        with session_scope() as session:
            restriction = (
                session.query(MemberRestrictions)
                .filter(MemberRestrictions.id == result["restriction_id"])
                .first()
            )
            assert restriction is not None
            assert restriction.member_id == test_member
            assert restriction.description == "Férias"

    def test_create_restriction_with_today_date(self, test_member):
        """Deve permitir criar restrição com data de hoje."""
        today_str = date.today().strftime("%d/%m/%Y")

        result = DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str=today_str,
            description="Bloqueio hoje",
        )

        assert result["success"] is True

    def test_create_restriction_with_past_date_fails(self, test_member):
        """Deve falhar ao criar restrição com data no passado."""
        past_date_str = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

        result = DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str=past_date_str,
            description="Passado",
        )

        assert result["success"] is False
        assert "passado" in result["message"].lower() or "past" in result["message"].lower()

    def test_create_restriction_with_invalid_date_format_fails(self, test_member):
        """Deve falhar com formato de data invalido."""
        result = DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str="2025-01-01",  # ISO, nao DD/MM/YYYY
            description="Invalido",
        )

        assert result["success"] is False
        assert "formato" in result["message"].lower() or "format" in result["message"].lower()

    def test_create_restriction_for_nonexistent_member_fails(self):
        """Deve falhar ao criar restrição para membro inexistente."""
        result = DisponibilidadeService.create_restriction(
            member_id="nonexistent-id",
            date_str=(date.today() + timedelta(days=1)).strftime("%d/%m/%Y"),
            description="Teste",
        )

        assert result["success"] is False
        assert "não encontrado" in result["message"].lower()

    def test_create_restriction_without_description(self, test_member):
        """Deve criar restrição sem descrição (campo opcional)."""
        future_date_str = (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")

        result = DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str=future_date_str,
            description="",
        )

        assert result["success"] is True


class TestRemoveRestriction:
    """Testes para remover restrição."""

    def test_remove_existing_restriction(self, test_member):
        """Deve remover restrição existente."""
        # Criar restrição
        future_date_str = (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")
        create_result = DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str=future_date_str,
            description="A remover",
        )
        assert create_result["success"] is True

        # Remover
        result = DisponibilidadeService.remove_restriction(
            member_id=test_member,
            date_str=future_date_str,
        )

        assert result["success"] is True
        assert "removida" in result["message"].lower()

    def test_remove_nonexistent_restriction_fails(self, test_member):
        """Deve falhar ao remover restrição que nao existe."""
        some_date_str = (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")

        result = DisponibilidadeService.remove_restriction(
            member_id=test_member,
            date_str=some_date_str,
        )

        assert result["success"] is False
        assert "não encontrada" in result["message"].lower()


class TestGetRestrictionsByMember:
    """Testes para listar restrições de um membro."""

    def test_get_restrictions_for_member_with_multiple_restrictions(self, test_member):
        """Deve retornar todas as restrições de um membro em ordem crescente."""
        # Criar varias restrições
        dates = [
            date.today() + timedelta(days=i) for i in [1, 5, 3, 10]
        ]
        for d in dates:
            date_str = d.strftime("%d/%m/%Y")
            DisponibilidadeService.create_restriction(
                member_id=test_member,
                date_str=date_str,
                description=f"Restrição {d}",
            )

        # Listar
        restrictions = DisponibilidadeService.get_restrictions_by_member(test_member)

        assert len(restrictions) == 4
        # Verificar ordem crescente de datas
        dates_from_result = [r["date"] for r in restrictions]
        assert dates_from_result == sorted(dates_from_result)

    def test_get_restrictions_for_member_with_no_restrictions(self, test_member):
        """Deve retornar lista vazia para membro sem restrições."""
        restrictions = DisponibilidadeService.get_restrictions_by_member(test_member)

        assert restrictions == []

    def test_restriction_dict_has_required_fields(self, test_member):
        """Cada restrição deve ter campos: id, date, date_display, description."""
        future_date = date.today() + timedelta(days=5)
        date_str = future_date.strftime("%d/%m/%Y")

        DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str=date_str,
            description="Teste",
        )

        restrictions = DisponibilidadeService.get_restrictions_by_member(test_member)

        assert len(restrictions) == 1
        restriction = restrictions[0]

        assert "id" in restriction
        assert "date" in restriction
        assert "date_display" in restriction
        assert "description" in restriction
        assert isinstance(restriction["date"], date)
        assert restriction["date_display"] == date_str


class TestIsMemberAvailableOnDate:
    """Testes para verificar disponibilidade de membro em data."""

    def test_member_available_without_restriction(self, test_member):
        """Membro sem restrição deve estar disponível."""
        check_date = date.today() + timedelta(days=1)

        is_available = DisponibilidadeService.is_member_available_on_date(
            member_id=test_member,
            check_date=check_date,
        )

        assert is_available is True

    def test_member_not_available_with_restriction(self, test_member):
        """Membro com restrição na data deve estar indisponível."""
        restricted_date = date.today() + timedelta(days=1)
        date_str = restricted_date.strftime("%d/%m/%Y")

        # Criar restrição
        DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str=date_str,
            description="Indisponível",
        )

        # Verificar indisponibilidade
        is_available = DisponibilidadeService.is_member_available_on_date(
            member_id=test_member,
            check_date=restricted_date,
        )

        assert is_available is False

    def test_member_available_on_different_date_than_restriction(self, test_member):
        """Membro disponível em data diferente da restrição."""
        restricted_date = date.today() + timedelta(days=1)
        check_date = date.today() + timedelta(days=5)

        date_str = restricted_date.strftime("%d/%m/%Y")
        DisponibilidadeService.create_restriction(
            member_id=test_member,
            date_str=date_str,
            description="Bloqueio em dia 1",
        )

        is_available = DisponibilidadeService.is_member_available_on_date(
            member_id=test_member,
            check_date=check_date,
        )

        assert is_available is True
