"""Tests for Squad service layer (database integration).

Tests squadservice functions that interact with the database.
"""

import pytest

from infra.database import Member, MemberSquad, Squad, session_scope
from services.squads_service import (
    add_member_to_squad,
    bulk_update_squad_memberships,
    create_squad,
    delete_squad,
    get_all_squads,
    get_squad_by_id,
    get_squad_members,
    remove_member_from_squad,
    update_member_rank_in_squad,
    update_squad_name,
)


@pytest.fixture
def clean_db():
    """Ensure clean database before each test."""
    with session_scope() as session:
        session.query(MemberSquad).delete(synchronize_session=False)
        session.query(Squad).delete(synchronize_session=False)
        session.query(Member).delete(synchronize_session=False)
    yield
    # Cleanup after test
    with session_scope() as session:
        session.query(MemberSquad).delete(synchronize_session=False)
        session.query(Squad).delete(synchronize_session=False)
        session.query(Member).delete(synchronize_session=False)


@pytest.fixture
def sample_squad(clean_db):
    """Create a sample squad for testing."""
    success, error, squad_id = create_squad("Guerreiros")
    assert success is True
    return squad_id


@pytest.fixture
def sample_members(clean_db):
    """Create sample members for testing."""
    with session_scope() as session:
        members = [
            Member(name="Alice"),
            Member(name="Bob"),
            Member(name="Charlie"),
        ]
        session.add_all(members)
        session.flush()
        ids = [m.id for m in members]
    return ids


# ── Create Squad Tests ───────────────────────────────────────────
class TestCreateSquad:
    """Test squad creation."""

    def test_create_squad_success(self, clean_db):
        """Create squad successfully."""
        success, error, squad_id = create_squad("Guerreiros")
        assert success is True
        assert error is None
        assert squad_id is not None

        # Verify in DB
        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            assert squad is not None
            assert squad.nome == "Guerreiros"

    def test_create_squad_empty_name(self, clean_db):
        """Create squad with empty name should fail."""
        success, error, squad_id = create_squad("")
        assert success is False
        assert error is not None
        assert "obrigatório" in error
        assert squad_id is None

    def test_create_squad_whitespace_name(self, clean_db):
        """Create squad with whitespace name should fail."""
        success, error, squad_id = create_squad("   ")
        assert success is False
        assert error is not None
        assert squad_id is None

    def test_create_squad_duplicate_name(self, clean_db):
        """Create squad with duplicate name should fail."""
        # Create first
        create_squad("Guerreiros")

        # Try duplicate
        success, error, squad_id = create_squad("Guerreiros")
        assert success is False
        assert "já existe" in error
        assert squad_id is None

    def test_create_squad_name_stripped(self, clean_db):
        """Squad name should be stripped of whitespace."""
        success, error, squad_id = create_squad("  Guerreiros  ")
        assert success is True

        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == squad_id).first()
            assert squad.nome == "Guerreiros"

    def test_create_multiple_squads(self, clean_db):
        """Create multiple different squads."""
        s1, _, id1 = create_squad("Guerreiros")
        s2, _, id2 = create_squad("Vigilantes")
        s3, _, id3 = create_squad("Proteção")

        assert s1 is True
        assert s2 is True
        assert s3 is True
        assert id1 != id2 != id3


# ── Update Squad Name Tests ──────────────────────────────────────
class TestUpdateSquadName:
    """Test updating squad name."""

    def test_update_squad_name_success(self, sample_squad):
        """Update squad name successfully."""
        success, error = update_squad_name(sample_squad, "Vigilantes")
        assert success is True
        assert error is None

        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == sample_squad).first()
            assert squad.nome == "Vigilantes"

    def test_update_squad_nonexistent(self, clean_db):
        """Update nonexistent squad should fail."""
        success, error = update_squad_name("nonexistent-id", "NewName")
        assert success is False
        assert "não encontrada" in error

    def test_update_squad_to_empty_name(self, sample_squad):
        """Update to empty name should fail."""
        success, error = update_squad_name(sample_squad, "")
        assert success is False
        assert "obrigatório" in error

    def test_update_squad_to_duplicate_name(self, clean_db):
        """Update to existing name should fail."""
        _, _, id1 = create_squad("Guerreiros")
        _, _, id2 = create_squad("Vigilantes")

        success, error = update_squad_name(id2, "Guerreiros")
        assert success is False
        assert "já existe" in error

    def test_update_squad_name_stripped(self, sample_squad):
        """Updated name should be stripped."""
        success, error = update_squad_name(sample_squad, "  NewName  ")
        assert success is True

        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == sample_squad).first()
            assert squad.nome == "NewName"


# ── Delete Squad Tests ───────────────────────────────────────────
class TestDeleteSquad:
    """Test squad deletion."""

    def test_delete_squad_success(self, sample_squad):
        """Delete squad successfully."""
        success, error = delete_squad(sample_squad)
        assert success is True
        assert error is None

        with session_scope() as session:
            squad = session.query(Squad).filter(Squad.id == sample_squad).first()
            assert squad is None

    def test_delete_squad_nonexistent(self, clean_db):
        """Delete nonexistent squad should fail."""
        success, error = delete_squad("nonexistent-id")
        assert success is False
        assert "não encontrada" in error

    def test_delete_squad_cascades_memberships(self, sample_squad, sample_members):
        """Deleting squad should delete its memberships."""
        member_id = sample_members[0]
        add_member_to_squad(sample_squad, member_id, "Líder")

        # Verify membership exists
        with session_scope() as session:
            count = (
                session.query(MemberSquad)
                .filter(MemberSquad.squad_id == sample_squad)
                .count()
            )
            assert count == 1

        # Delete squad
        delete_squad(sample_squad)

        # Verify membership is gone
        with session_scope() as session:
            count = (
                session.query(MemberSquad)
                .filter(MemberSquad.squad_id == sample_squad)
                .count()
            )
            assert count == 0


# ── Add Member to Squad Tests ────────────────────────────────────
class TestAddMemberToSquad:
    """Test adding member to squad."""

    def test_add_member_success(self, sample_squad, sample_members):
        """Add member to squad successfully."""
        member_id = sample_members[0]
        success, error = add_member_to_squad(sample_squad, member_id, "Líder")
        assert success is True
        assert error is None

        with session_scope() as session:
            membership = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == sample_squad,
                    MemberSquad.member_id == member_id,
                )
                .first()
            )
            assert membership is not None
            assert membership.level == 4  # Líder = 4

    def test_add_member_nonexistent_squad(self, sample_members):
        """Add to nonexistent squad should fail."""
        member_id = sample_members[0]
        success, error = add_member_to_squad("nonexistent-squad", member_id, "Membro")
        assert success is False
        assert "não encontrada" in error

    def test_add_nonexistent_member(self, sample_squad):
        """Add nonexistent member should fail."""
        success, error = add_member_to_squad(sample_squad, "nonexistent-member", "Membro")
        assert success is False
        assert "não encontrado" in error

    def test_add_duplicate_member(self, sample_squad, sample_members):
        """Adding same member twice should fail."""
        member_id = sample_members[0]
        add_member_to_squad(sample_squad, member_id, "Líder")

        success, error = add_member_to_squad(sample_squad, member_id, "Membro")
        assert success is False
        assert "já está neste time" in error

    def test_add_member_different_ranks(self, sample_squad, sample_members):
        """Add members with different ranks."""
        ids = sample_members
        add_member_to_squad(sample_squad, ids[0], "Líder")
        add_member_to_squad(sample_squad, ids[1], "Treinador")
        add_member_to_squad(sample_squad, ids[2], "Recruta")

        with session_scope() as session:
            m1 = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == sample_squad,
                    MemberSquad.member_id == ids[0],
                )
                .first()
            )
            m2 = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == sample_squad,
                    MemberSquad.member_id == ids[1],
                )
                .first()
            )
            m3 = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == sample_squad,
                    MemberSquad.member_id == ids[2],
                )
                .first()
            )
            assert m1.level == 4  # Líder
            assert m2.level == 3  # Treinador
            assert m3.level == 1  # Recruta

    def test_add_member_invalid_rank(self, sample_squad, sample_members):
        """Invalid rank should default to Membro (level 2)."""
        member_id = sample_members[0]
        success, error = add_member_to_squad(sample_squad, member_id, "Soldado")
        assert success is True

        with session_scope() as session:
            membership = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == sample_squad,
                    MemberSquad.member_id == member_id,
                )
                .first()
            )
            assert membership.level == 2  # Membro fallback


# ── Remove Member from Squad Tests ───────────────────────────────
class TestRemoveMemberFromSquad:
    """Test removing member from squad."""

    def test_remove_member_success(self, sample_squad, sample_members):
        """Remove member from squad successfully."""
        member_id = sample_members[0]
        add_member_to_squad(sample_squad, member_id, "Líder")

        success, error = remove_member_from_squad(sample_squad, member_id)
        assert success is True
        assert error is None

        with session_scope() as session:
            membership = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == sample_squad,
                    MemberSquad.member_id == member_id,
                )
                .first()
            )
            assert membership is None

    def test_remove_nonexistent_membership(self, sample_squad, sample_members):
        """Remove member not in squad should fail."""
        member_id = sample_members[0]
        success, error = remove_member_from_squad(sample_squad, member_id)
        assert success is False
        assert "não está neste time" in error


# ── Update Member Rank Tests ─────────────────────────────────────
class TestUpdateMemberRankInSquad:
    """Test updating member rank in squad."""

    def test_update_rank_success(self, sample_squad, sample_members):
        """Update member rank successfully."""
        member_id = sample_members[0]
        add_member_to_squad(sample_squad, member_id, "Recruta")

        success, error = update_member_rank_in_squad(sample_squad, member_id, "Líder")
        assert success is True
        assert error is None

        with session_scope() as session:
            membership = (
                session.query(MemberSquad)
                .filter(
                    MemberSquad.squad_id == sample_squad,
                    MemberSquad.member_id == member_id,
                )
                .first()
            )
            assert membership.level == 4  # Líder

    def test_update_rank_nonexistent_membership(self, sample_squad):
        """Update rank of member not in squad should fail."""
        success, error = update_member_rank_in_squad(sample_squad, "nonexistent", "Membro")
        assert success is False
        assert "não está neste time" in error

    def test_update_rank_all_transitions(self, sample_squad, sample_members):
        """Test all rank transitions."""
        member_id = sample_members[0]
        add_member_to_squad(sample_squad, member_id, "Recruta")

        for patente, expected_level in [
            ("Recruta", 1),
            ("Membro", 2),
            ("Treinador", 3),
            ("Líder", 4),
        ]:
            update_member_rank_in_squad(sample_squad, member_id, patente)
            with session_scope() as session:
                m = (
                    session.query(MemberSquad)
                    .filter(
                        MemberSquad.squad_id == sample_squad,
                        MemberSquad.member_id == member_id,
                    )
                    .first()
                )
                assert m.level == expected_level


# ── Get Squad by ID Tests ────────────────────────────────────────
class TestGetSquadById:
    """Test retrieving squad by ID."""

    def test_get_squad_success(self, sample_squad, sample_members):
        """Retrieve squad successfully."""
        add_member_to_squad(sample_squad, sample_members[0], "Líder")
        add_member_to_squad(sample_squad, sample_members[1], "Membro")

        squad = get_squad_by_id(sample_squad)
        assert squad is not None
        assert squad['id'] == sample_squad
        assert squad['nome'] == "Guerreiros"
        assert squad['member_count'] == 2
        assert len(squad['memberships']) == 2

    def test_get_squad_nonexistent(self, clean_db):
        """Get nonexistent squad should return None."""
        squad = get_squad_by_id("nonexistent-id")
        assert squad is None

    def test_get_squad_empty(self, sample_squad):
        """Get squad with no members."""
        squad = get_squad_by_id(sample_squad)
        assert squad is not None
        assert squad['member_count'] == 0
        assert squad['memberships'] == []


# ── Get All Squads Tests ─────────────────────────────────────────
class TestGetAllSquads:
    """Test retrieving all squads."""

    def test_get_all_squads_empty(self, clean_db):
        """Get all squads when none exist."""
        squads = get_all_squads()
        assert squads == []

    def test_get_all_squads_ordered(self, clean_db):
        """Get all squads in alphabetical order."""
        create_squad("Zebras")
        create_squad("Albatrozes")
        create_squad("Chiguires")

        squads = get_all_squads()
        assert len(squads) == 3
        assert squads[0]['nome'] == "Albatrozes"
        assert squads[1]['nome'] == "Chiguires"
        assert squads[2]['nome'] == "Zebras"

    def test_get_all_squads_with_member_counts(self, clean_db, sample_members):
        """Get all squads with correct member counts."""
        _, _, id1 = create_squad("Squad 1")
        _, _, id2 = create_squad("Squad 2")

        add_member_to_squad(id1, sample_members[0], "Líder")
        add_member_to_squad(id1, sample_members[1], "Membro")
        add_member_to_squad(id2, sample_members[2], "Recruta")

        squads = get_all_squads()
        assert len(squads) == 2
        assert squads[0]['member_count'] == 2
        assert squads[1]['member_count'] == 1


# ── Get Squad Members Tests ──────────────────────────────────────
class TestGetSquadMembers:
    """Test retrieving squad members."""

    def test_get_squad_members_empty(self, sample_squad):
        """Get members from empty squad."""
        members = get_squad_members(sample_squad)
        assert members == []

    def test_get_squad_members_success(self, sample_squad, sample_members):
        """Get members from squad."""
        add_member_to_squad(sample_squad, sample_members[0], "Líder")
        add_member_to_squad(sample_squad, sample_members[1], "Membro")

        members = get_squad_members(sample_squad)
        assert len(members) == 2

        # Check names are included
        names = [m['name'] for m in members]
        assert "Alice" in names
        assert "Bob" in names

    def test_get_squad_members_with_levels(self, sample_squad, sample_members):
        """Get members with correct levels."""
        add_member_to_squad(sample_squad, sample_members[0], "Líder")
        add_member_to_squad(sample_squad, sample_members[1], "Recruta")

        members = get_squad_members(sample_squad)
        levels = {m['member_id']: m['level'] for m in members}
        assert levels[sample_members[0]] == 4
        assert levels[sample_members[1]] == 1


# ── Bulk Update Memberships Tests ────────────────────────────────
class TestBulkUpdateSquadMemberships:
    """Test bulk updating squad memberships."""

    def test_bulk_update_success(self, sample_squad, sample_members):
        """Bulk update memberships successfully."""
        memberships = [
            (sample_members[0], 4),  # Líder
            (sample_members[1], 2),  # Membro
        ]
        success, error = bulk_update_squad_memberships(sample_squad, memberships)
        assert success is True
        assert error is None

        members = get_squad_members(sample_squad)
        assert len(members) == 2

    def test_bulk_update_replaces_existing(self, sample_squad, sample_members):
        """Bulk update should replace existing memberships."""
        # Add initial
        add_member_to_squad(sample_squad, sample_members[0], "Líder")
        add_member_to_squad(sample_squad, sample_members[1], "Membro")

        # Bulk update with different data
        memberships = [(sample_members[2], 1)]
        success, error = bulk_update_squad_memberships(sample_squad, memberships)
        assert success is True

        members = get_squad_members(sample_squad)
        assert len(members) == 1
        assert members[0]['member_id'] == sample_members[2]

    def test_bulk_update_empty_list(self, sample_squad, sample_members):
        """Bulk update with empty list should clear squad."""
        add_member_to_squad(sample_squad, sample_members[0], "Líder")

        success, error = bulk_update_squad_memberships(sample_squad, [])
        assert success is True

        members = get_squad_members(sample_squad)
        assert len(members) == 0

    def test_bulk_update_nonexistent_squad(self, clean_db, sample_members):
        """Bulk update nonexistent squad should fail."""
        memberships = [(sample_members[0], 2)]
        success, error = bulk_update_squad_memberships("nonexistent", memberships)
        assert success is False
        assert "não encontrada" in error

    def test_bulk_update_nonexistent_member(self, sample_squad):
        """Bulk update with nonexistent member should fail."""
        memberships = [("nonexistent-member", 2)]
        success, error = bulk_update_squad_memberships(sample_squad, memberships)
        assert success is False
        assert "não encontrado" in error
