"""Tests for Member helpers - 100% coverage target."""

import pytest

from helpers.membros import (
    count_member_schedules,
    validate_member_name,
    validate_member_rank,
)


class TestValidateMemberName:
    """Validate member name without database."""

    def test_empty_name_returns_false(self):
        """Empty string should fail validation."""
        valid, error = validate_member_name("", existing_names=[])
        assert valid is False
        assert error == "Nome é obrigatório"

    def test_whitespace_only_name_returns_false(self):
        """Whitespace-only name should fail validation."""
        valid, error = validate_member_name("   ", existing_names=[])
        assert valid is False
        assert error == "Nome é obrigatório"

    def test_none_name_returns_false(self):
        """None name should fail validation."""
        valid, error = validate_member_name(None, existing_names=[])
        assert valid is False
        assert error == "Nome é obrigatório"

    def test_unique_name_returns_true(self):
        """Valid unique name should pass."""
        valid, error = validate_member_name("João", existing_names=["Maria", "Pedro"])
        assert valid is True
        assert error is None

    def test_duplicate_name_returns_false(self):
        """Duplicate name should fail validation."""
        valid, error = validate_member_name(
            "João", existing_names=["João", "Maria", "Pedro"]
        )
        assert valid is False
        assert error == "Membro com este nome já existe"

    def test_duplicate_name_case_sensitive(self):
        """Name validation should be case-sensitive."""
        valid, error = validate_member_name(
            "João", existing_names=["joão", "Maria"]
        )
        assert valid is True
        assert error is None

    def test_name_with_whitespace_trimmed(self):
        """Name should be trimmed before checking duplicates."""
        valid, error = validate_member_name(
            "  João  ", existing_names=["João"]
        )
        assert valid is False
        assert error == "Membro com este nome já existe"

    def test_empty_existing_names_list(self):
        """Should work with empty existing names list."""
        valid, error = validate_member_name("João", existing_names=[])
        assert valid is True
        assert error is None

    def test_valid_name_with_special_characters(self):
        """Name with special characters should pass if unique."""
        valid, error = validate_member_name(
            "João da Silva-Santos", existing_names=["Maria"]
        )
        assert valid is True
        assert error is None

    def test_valid_name_with_numbers(self):
        """Name with numbers should pass if unique."""
        valid, error = validate_member_name("João123", existing_names=[])
        assert valid is True
        assert error is None


class TestValidateMemberRank:
    """Validate member rank against allowed values."""

    def test_all_valid_ranks(self):
        """All standard ranks should be valid."""
        valid_ranks = ["Líder", "Treinador", "Membro", "Recruta"]
        for rank in valid_ranks:
            valid, error = validate_member_rank(rank)
            assert valid is True, f"{rank} should be valid"
            assert error is None, f"No error for {rank}"

    def test_invalid_rank_returns_false(self):
        """Invalid rank should fail validation."""
        valid, error = validate_member_rank("Soldado")
        assert valid is False
        assert "Patente inválida" in error
        assert "Soldado" in error

    def test_empty_rank_returns_false(self):
        """Empty rank should fail validation."""
        valid, error = validate_member_rank("")
        assert valid is False
        assert "Patente inválida" in error

    def test_none_rank_returns_false(self):
        """None rank should fail validation."""
        valid, error = validate_member_rank(None)
        assert valid is False
        assert "Patente inválida" in error

    def test_rank_case_sensitive(self):
        """Rank validation should be case-sensitive."""
        valid, error = validate_member_rank("líder")  # lowercase
        assert valid is False
        assert "Patente inválida" in error

    def test_rank_with_whitespace_fails(self):
        """Rank with whitespace should fail."""
        valid, error = validate_member_rank("  Líder  ")
        assert valid is False
        assert "Patente inválida" in error

    def test_rank_with_accents_respected(self):
        """Accents in rank names should be respected."""
        # "Líder" has accent, "Lider" without should fail
        valid, error = validate_member_rank("Lider")
        assert valid is False
        assert "Patente inválida" in error


class TestCountMemberSchedules:
    """Count number of schedules (MemberSquad associations) for a member."""

    def test_member_with_no_schedules(self):
        """Member with no squad associations should return 0."""
        count = count_member_schedules([])
        assert count == 0

    def test_member_with_one_schedule(self):
        """Member with one squad should return 1."""
        memberships = [{"squad_id": "squad-1"}]
        count = count_member_schedules(memberships)
        assert count == 1

    def test_member_with_multiple_schedules(self):
        """Member with multiple squads should return correct count."""
        memberships = [
            {"squad_id": "squad-1"},
            {"squad_id": "squad-2"},
            {"squad_id": "squad-3"},
        ]
        count = count_member_schedules(memberships)
        assert count == 3

    def test_count_schedules_accepts_object_list(self):
        """Should handle list of objects with squad_id."""
        class FakeMembership:
            def __init__(self, squad_id):
                self.squad_id = squad_id

        memberships = [
            FakeMembership("squad-1"),
            FakeMembership("squad-2"),
        ]
        count = count_member_schedules(memberships)
        assert count == 2

    def test_count_schedules_large_list(self):
        """Should handle large membership lists."""
        memberships = [{"squad_id": f"squad-{i}"} for i in range(100)]
        count = count_member_schedules(memberships)
        assert count == 100

    def test_count_schedules_ignores_extra_fields(self):
        """Should count even if memberships have extra fields."""
        memberships = [
            {"squad_id": "squad-1", "level": 1, "extra": "data"},
            {"squad_id": "squad-2", "level": 2},
        ]
        count = count_member_schedules(memberships)
        assert count == 2


class TestValidateMemberNameEdgeCases:
    """Edge cases for name validation."""

    def test_single_character_name(self):
        """Single character name should be valid if unique."""
        valid, error = validate_member_name("A", existing_names=[])
        assert valid is True
        assert error is None

    def test_very_long_name(self):
        """Very long name should be valid if unique."""
        long_name = "A" * 1000
        valid, error = validate_member_name(long_name, existing_names=[])
        assert valid is True
        assert error is None

    def test_unicode_characters_in_name(self):
        """Unicode characters should be handled correctly."""
        valid, error = validate_member_name("北京", existing_names=["Москва"])
        assert valid is True
        assert error is None

    def test_name_with_leading_trailing_spaces_in_existing(self):
        """Should treat literal strings - input is trimmed, existing names are not."""
        # This tests the trimming behavior
        valid, error = validate_member_name(
            "João", existing_names=["  João  "]
        )
        # Input "João" is trimmed to "João"
        # Existing list contains "  João  " which is different string
        # So they don't match literally and should be valid
        assert valid is True
        assert error is None

    def test_multiple_duplicate_names_in_list(self):
        """Should catch duplicate even if it appears multiple times in list."""
        valid, error = validate_member_name(
            "João", existing_names=["Maria", "João", "João", "Pedro"]
        )
        assert valid is False
        assert error == "Membro com este nome já existe"


class TestValidateMemberRankEdgeCases:
    """Edge cases for rank validation."""

    def test_rank_similar_but_wrong(self):
        """Similar but incorrect rank should fail."""
        valid, error = validate_member_rank("Lider")  # Missing accent
        assert valid is False

    def test_rank_with_extra_whitespace(self):
        """Rank with extra spaces should fail."""
        valid, error = validate_member_rank("Líder ")  # trailing space
        assert valid is False

    def test_rank_numeric_string(self):
        """Numeric rank string should fail."""
        valid, error = validate_member_rank("1")
        assert valid is False
