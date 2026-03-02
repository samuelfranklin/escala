"""Tests for Squad helper functions (100% coverage).

All tests in this module test pure functions (no database, no side-effects).
"""

import pytest

from helpers.squads import (
    ALL_PATENTES,
    LEVEL_TO_PATENTE,
    PATENTE_TO_LEVEL,
    count_members_in_squad,
    get_all_patentes,
    get_member_rank_in_squad,
    get_rank_level,
    is_valid_patente,
    rank_members_by_level,
    validate_member_not_duplicate_in_squad,
    validate_squad_name,
)


# ── Rank/Patente Mapping Tests ───────────────────────────────────
class TestRankPatenteMappings:
    """Test rank/patente conversion mappings."""

    def test_patente_to_level_has_four_entries(self):
        """PATENTE_TO_LEVEL should have 4 patentes."""
        assert len(PATENTE_TO_LEVEL) == 4

    def test_patente_to_level_values(self):
        """PATENTE_TO_LEVEL should map correctly."""
        assert PATENTE_TO_LEVEL["Líder"] == 4
        assert PATENTE_TO_LEVEL["Treinador"] == 3
        assert PATENTE_TO_LEVEL["Membro"] == 2
        assert PATENTE_TO_LEVEL["Recruta"] == 1

    def test_level_to_patente_is_inverse(self):
        """LEVEL_TO_PATENTE should be inverse of PATENTE_TO_LEVEL."""
        assert LEVEL_TO_PATENTE[4] == "Líder"
        assert LEVEL_TO_PATENTE[3] == "Treinador"
        assert LEVEL_TO_PATENTE[2] == "Membro"
        assert LEVEL_TO_PATENTE[1] == "Recruta"

    def test_all_patentes_constant(self):
        """ALL_PATENTES should have all 4 patentes."""
        assert len(ALL_PATENTES) == 4
        assert "Líder" in ALL_PATENTES
        assert "Treinador" in ALL_PATENTES
        assert "Membro" in ALL_PATENTES
        assert "Recruta" in ALL_PATENTES


# ── Squad Name Validation Tests ──────────────────────────────────
class TestValidateSquadName:
    """Test squad name validation logic."""

    def test_valid_name(self):
        """Valid name should return (True, None)."""
        is_valid, error = validate_squad_name("Guerreiros", [])
        assert is_valid is True
        assert error is None

    def test_empty_name(self):
        """Empty name should fail."""
        is_valid, error = validate_squad_name("", [])
        assert is_valid is False
        assert "obrigatório" in error

    def test_whitespace_only_name(self):
        """Whitespace-only name should fail."""
        is_valid, error = validate_squad_name("   ", [])
        assert is_valid is False
        assert "obrigatório" in error

    def test_none_name(self):
        """None name should fail."""
        is_valid, error = validate_squad_name(None, [])
        assert is_valid is False
        assert "obrigatório" in error

    def test_duplicate_name_exact_match(self):
        """Exact duplicate name should fail."""
        is_valid, error = validate_squad_name("Guerreiros", ["Guerreiros"])
        assert is_valid is False
        assert "já existe" in error

    def test_duplicate_name_in_list(self):
        """Name in existing list should fail."""
        existing = ["Alfa", "Bravo", "Charlie"]
        is_valid, error = validate_squad_name("Bravo", existing)
        assert is_valid is False

    def test_name_with_whitespace_stripped(self):
        """Name with leading/trailing whitespace should be stripped."""
        is_valid, error = validate_squad_name("  Guerreiros  ", [])
        assert is_valid is True

    def test_duplicate_name_after_whitespace_strip(self):
        """Whitespace shouldn't prevent duplicate detection."""
        is_valid, error = validate_squad_name("  Guerreiros  ", ["Guerreiros"])
        assert is_valid is False

    def test_unique_name_among_many(self):
        """Name not in existing list should pass."""
        existing = ["Alfa", "Bravo", "Charlie", "Delta"]
        is_valid, error = validate_squad_name("Echo", existing)
        assert is_valid is True
        assert error is None

    def test_case_sensitive(self):
        """Names should be case-sensitive (different case = different name)."""
        is_valid, error = validate_squad_name("guerreiros", ["Guerreiros"])
        assert is_valid is True  # Different case

    def test_empty_existing_names_list(self):
        """Empty existing names list should allow any valid name."""
        is_valid, error = validate_squad_name("New Squad", [])
        assert is_valid is True


# ── Member Duplicate in Squad Tests ──────────────────────────────
class TestValidateMemberNotDuplicateInSquad:
    """Test member duplicate detection in squad."""

    def test_member_not_in_squad(self):
        """Member not in squad should return True."""
        result = validate_member_not_duplicate_in_squad(
            "member-123", ["member-001", "member-002"]
        )
        assert result is True

    def test_member_already_in_squad(self):
        """Member in squad should return False."""
        result = validate_member_not_duplicate_in_squad(
            "member-001", ["member-001", "member-002"]
        )
        assert result is False

    def test_empty_squad(self):
        """Empty squad should allow any member."""
        result = validate_member_not_duplicate_in_squad("member-123", [])
        assert result is True

    def test_member_position_in_list(self):
        """Member position in list shouldn't matter."""
        members = ["a", "b", "c", "d"]
        assert validate_member_not_duplicate_in_squad("b", members) is False
        assert validate_member_not_duplicate_in_squad("d", members) is False
        assert validate_member_not_duplicate_in_squad("e", members) is True

    def test_case_sensitive_member_id(self):
        """Member IDs should be case-sensitive."""
        result = validate_member_not_duplicate_in_squad(
            "Member-001", ["member-001"]
        )
        assert result is True  # Different case


# ── Rank Conversion Tests ────────────────────────────────────────
class TestGetMemberRankInSquad:
    """Test converting level to patente."""

    def test_level_to_patente_all_valid_levels(self):
        """All valid levels should convert correctly."""
        assert get_member_rank_in_squad(4) == "Líder"
        assert get_member_rank_in_squad(3) == "Treinador"
        assert get_member_rank_in_squad(2) == "Membro"
        assert get_member_rank_in_squad(1) == "Recruta"

    def test_level_invalid_fallback_to_membro(self):
        """Invalid level should fallback to Membro."""
        assert get_member_rank_in_squad(0) == "Membro"
        assert get_member_rank_in_squad(5) == "Membro"
        assert get_member_rank_in_squad(99) == "Membro"
        assert get_member_rank_in_squad(-1) == "Membro"

    def test_level_none_fallback(self):
        """None level should fallback to Membro."""
        assert get_member_rank_in_squad(None) == "Membro"


class TestGetRankLevel:
    """Test converting patente to level."""

    def test_patente_to_level_all_valid(self):
        """All valid patentes should convert correctly."""
        assert get_rank_level("Líder") == 4
        assert get_rank_level("Treinador") == 3
        assert get_rank_level("Membro") == 2
        assert get_rank_level("Recruta") == 1

    def test_patente_invalid_fallback_to_membro(self):
        """Invalid patente should fallback to Membro (level 2)."""
        assert get_rank_level("Soldado") == 2
        assert get_rank_level("Unknown") == 2
        assert get_rank_level("") == 2
        assert get_rank_level("liDER") == 2  # case-sensitive

    def test_patente_none_fallback(self):
        """None patente should fallback to Membro (level 2)."""
        assert get_rank_level(None) == 2


# ── Member Count Tests ───────────────────────────────────────────
class TestCountMembersInSquad:
    """Test member counting in squad."""

    def test_count_empty_squad(self):
        """Empty squad should have 0 members."""
        assert count_members_in_squad([]) == 0

    def test_count_single_member(self):
        """Squad with 1 member should count to 1."""
        assert count_members_in_squad(["member-1"]) == 1

    def test_count_multiple_members(self):
        """Squad with multiple members should count correctly."""
        assert count_members_in_squad(["m1", "m2", "m3"]) == 3

    def test_count_many_members(self):
        """Squad with many members should count correctly."""
        members = [f"member-{i}" for i in range(100)]
        assert count_members_in_squad(members) == 100


# ── Patente Validation Tests ────────────────────────────────────
class TestIsValidPatente:
    """Test patente validation."""

    def test_all_valid_patentes(self):
        """All 4 patentes should be valid."""
        assert is_valid_patente("Líder") is True
        assert is_valid_patente("Treinador") is True
        assert is_valid_patente("Membro") is True
        assert is_valid_patente("Recruta") is True

    def test_invalid_patentes(self):
        """Invalid patentes should return False."""
        assert is_valid_patente("Soldado") is False
        assert is_valid_patente("Capitão") is False
        assert is_valid_patente("liDER") is False  # case-sensitive
        assert is_valid_patente("") is False
        assert is_valid_patente("Unknown") is False

    def test_none_patente(self):
        """None should return False."""
        assert is_valid_patente(None) is False


# ── Get All Patentes Tests ──────────────────────────────────────
class TestGetAllPatentes:
    """Test getting list of all patentes."""

    def test_returns_all_four(self):
        """Should return all 4 patentes."""
        patentes = get_all_patentes()
        assert len(patentes) == 4

    def test_returns_in_order(self):
        """Should return patentes in correct order."""
        patentes = get_all_patentes()
        assert patentes == ["Líder", "Treinador", "Membro", "Recruta"]

    def test_returns_copy(self):
        """Should return a copy, not the original list."""
        patentes1 = get_all_patentes()
        patentes2 = get_all_patentes()
        assert patentes1 == patentes2
        # Modify one and check the other isn't affected
        patentes1.append("Fake")
        assert len(get_all_patentes()) == 4


# ── Rank Members by Level Tests ──────────────────────────────────
class TestRankMembersByLevel:
    """Test partitioning members into enrolled and available."""

    def test_empty_list(self):
        """Empty list should return two empty lists."""
        enrolled, available = rank_members_by_level([])
        assert enrolled == []
        assert available == []

    def test_all_enrolled(self):
        """List with all enrolled should return all in enrolled, empty available."""
        members = [
            ("id1", "Alice", 4),
            ("id2", "Bob", 3),
            ("id3", "Charlie", 1),
        ]
        enrolled, available = rank_members_by_level(members)
        assert len(enrolled) == 3
        assert len(available) == 0

    def test_all_available(self):
        """List with all level=0 should return all in available, empty enrolled."""
        members = [
            ("id1", "Alice", 0),
            ("id2", "Bob", 0),
            ("id3", "Charlie", 0),
        ]
        enrolled, available = rank_members_by_level(members)
        assert len(enrolled) == 0
        assert len(available) == 3

    def test_mixed_enrolled_and_available(self):
        """Mixed list should partition correctly."""
        members = [
            ("id1", "Alice", 4),
            ("id2", "Bob", 0),
            ("id3", "Charlie", 2),
            ("id4", "Diana", 0),
            ("id5", "Eve", 3),
        ]
        enrolled, available = rank_members_by_level(members)
        assert len(enrolled) == 3
        assert len(available) == 2
        # Check content
        enrolled_ids = [m[0] for m in enrolled]
        available_ids = [m[0] for m in available]
        assert "id1" in enrolled_ids
        assert "id3" in enrolled_ids
        assert "id5" in enrolled_ids
        assert "id2" in available_ids
        assert "id4" in available_ids

    def test_order_preserved(self):
        """Partitioning should preserve original order within partitions."""
        members = [
            ("id1", "A", 1),
            ("id2", "B", 0),
            ("id3", "C", 1),
            ("id4", "D", 0),
        ]
        enrolled, available = rank_members_by_level(members)
        assert enrolled[0][0] == "id1"
        assert enrolled[1][0] == "id3"
        assert available[0][0] == "id2"
        assert available[1][0] == "id4"

    def test_single_member_enrolled(self):
        """Single enrolled member."""
        members = [("id1", "Alice", 3)]
        enrolled, available = rank_members_by_level(members)
        assert len(enrolled) == 1
        assert len(available) == 0
        assert enrolled[0] == ("id1", "Alice", 3)

    def test_single_member_available(self):
        """Single available member."""
        members = [("id1", "Alice", 0)]
        enrolled, available = rank_members_by_level(members)
        assert len(enrolled) == 0
        assert len(available) == 1
        assert available[0] == ("id1", "Alice", 0)

    def test_level_boundary_just_above_zero(self):
        """Level 1 should be enrolled, not available."""
        members = [("id1", "Alice", 1)]
        enrolled, available = rank_members_by_level(members)
        assert len(enrolled) == 1
        assert len(available) == 0

    def test_level_boundary_zero(self):
        """Level 0 should be available, not enrolled."""
        members = [("id1", "Alice", 0)]
        enrolled, available = rank_members_by_level(members)
        assert len(enrolled) == 0
        assert len(available) == 1


# ── Edge Cases and Integration ───────────────────────────────────
class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_validate_squad_name_with_special_chars(self):
        """Squad names with special characters should validate."""
        is_valid, error = validate_squad_name("Times@123", [])
        assert is_valid is True

    def test_validate_squad_name_with_unicode(self):
        """Squad names with unicode should validate."""
        is_valid, error = validate_squad_name("Guerreiros São José", [])
        assert is_valid is True

    def test_validate_squad_name_very_long(self):
        """Very long squad names should validate (validation doesn't check length)."""
        long_name = "A" * 500
        is_valid, error = validate_squad_name(long_name, [])
        assert is_valid is True

    def test_member_id_format_agnostic(self):
        """Member ID validation should work with any format."""
        result = validate_member_not_duplicate_in_squad(
            "uuid-like-id-12345", ["uuid-like-id-00000"]
        )
        assert result is True
