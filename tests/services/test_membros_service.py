"""Tests for MembrosService - Service layer with database mocking."""

from unittest.mock import MagicMock, patch, call
import pytest

from infra.database import Member, MemberSquad, Squad
from services.membros_service import MembrosService


@pytest.fixture
def mock_session():
    """Create a mock session for database operations."""
    return MagicMock()


class TestMembrosServiceGetAllMembers:
    """Test fetching all members from database."""

    @patch("services.membros_service.session_scope")
    def test_get_all_members_success(self, mock_session_scope, mock_session):
        """Get all active members ordered by name."""
        # Setup mock members
        member1 = Member(id="1", name="Alice", phone_number="111", email="alice@test.com", status=True)
        member2 = Member(id="2", name="Bob", phone_number="222", email="bob@test.com", status=True)
        
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [member1, member2]
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_all_members()
        
        assert len(result) == 2
        assert result[0].name == "Alice"
        assert result[1].name == "Bob"

    @patch("services.membros_service.session_scope")
    def test_get_all_members_empty_list(self, mock_session_scope, mock_session):
        """Get empty list when no members exist."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_all_members()
        
        assert result == []

    @patch("services.membros_service.session_scope")
    def test_get_all_members_exception_handling(self, mock_session_scope, mock_session):
        """Handle exception and return empty list."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.side_effect = Exception("DB Error")
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_all_members()
        
        assert result == []


class TestMembrosServiceGetMemberById:
    """Test fetching a single member by ID."""

    @patch("services.membros_service.session_scope")
    def test_get_member_by_id_found(self, mock_session_scope, mock_session):
        """Get member when it exists."""
        member = Member(id="1", name="Alice", phone_number="111", status=True)
        
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = member
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_member_by_id("1")
        
        assert result == member
        assert result.name == "Alice"

    @patch("services.membros_service.session_scope")
    def test_get_member_by_id_not_found(self, mock_session_scope, mock_session):
        """Return None when member doesn't exist."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_member_by_id("999")
        
        assert result is None

    @patch("services.membros_service.session_scope")
    def test_get_member_by_id_only_returns_active(self, mock_session_scope):
        """Only return members with status=True."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        MembrosService.get_member_by_id("1")
        
        # Verify filter_by was called with status=True
        mock_session.query.return_value.filter_by.assert_called_with(id="1", status=True)


class TestMembrosServiceCreateMember:
    """Test creating a new member with validation."""

    @patch("services.membros_service.session_scope")
    def test_create_member_success(self, mock_session_scope, mock_session):
        """Create member with valid data."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.create_member(
            name="João",
            phone_number="12345",
            email="joao@test.com"
        )
        
        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("services.membros_service.session_scope")
    def test_create_member_empty_name_fails(self, mock_session_scope, mock_session):
        """Creating member with empty name should fail."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.create_member(name="", phone_number="123")
        
        assert result is None
        mock_session.add.assert_not_called()

    @patch("services.membros_service.session_scope")
    def test_create_member_duplicate_name_fails(self, mock_session_scope, mock_session):
        """Creating member with duplicate name should fail."""
        existing_member = Member(id="1", name="João")
        
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_member
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.create_member(name="João")
        
        assert result is None
        mock_session.add.assert_not_called()

    @patch("services.membros_service.session_scope")
    def test_create_member_name_trimmed(self, mock_session_scope, mock_session):
        """Name should be trimmed before storing."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        MembrosService.create_member(name="  João  ")
        
        # Verify that the added member has trimmed name
        call_args = mock_session.add.call_args[0][0]
        assert call_args.name == "João"


class TestMembrosServiceUpdateMember:
    """Test updating member data with validation."""

    @patch("services.membros_service.session_scope")
    def test_update_member_success(self, mock_session_scope, mock_session):
        """Update member with valid data."""
        existing_member = Member(id="1", name="João")
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_member
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.update_member("1", name="João Silva")
        
        assert result == existing_member
        assert existing_member.name == "João Silva"
        mock_session.commit.assert_called_once()

    @patch("services.membros_service.session_scope")
    def test_update_member_not_found(self, mock_session_scope, mock_session):
        """Update non-existent member should fail."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.update_member("999", name="João")
        
        assert result is None
        mock_session.commit.assert_not_called()

    @patch("services.membros_service.session_scope")
    def test_update_member_duplicate_name_fails(self, mock_session_scope, mock_session):
        """Update to duplicate name should fail."""
        existing_member = Member(id="1", name="João")
        other_member = Member(id="2", name="João Silva")
        
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_member
        mock_session.query.return_value.filter.return_value.all.return_value = [other_member]
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.update_member("1", name="João Silva")
        
        assert result is None
        # Member name should not be changed
        assert existing_member.name == "João"


class TestMembrosServiceDeleteMember:
    """Test soft deleting a member."""

    @patch("services.membros_service.session_scope")
    def test_delete_member_success(self, mock_session_scope, mock_session):
        """Soft delete (mark as inactive) should succeed."""
        existing_member = Member(id="1", name="João", status=True)
        
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_member
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.delete_member("1")
        
        assert result is True
        assert existing_member.status is False
        mock_session.commit.assert_called_once()

    @patch("services.membros_service.session_scope")
    def test_delete_member_not_found(self, mock_session_scope, mock_session):
        """Delete non-existent member should fail."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.delete_member("999")
        
        assert result is False
        mock_session.commit.assert_not_called()


class TestMembrosServiceMemberScheduleCount:
    """Test counting schedules (squad memberships) for a member."""

    @patch("services.membros_service.session_scope")
    def test_count_schedules_with_squads(self, mock_session_scope, mock_session):
        """Count member's squad memberships."""
        membership1 = MemberSquad(member_id="1", squad_id="squad-1", level=1)
        membership2 = MemberSquad(member_id="1", squad_id="squad-2", level=2)
        member = Member(id="1", name="João")
        member.memberships = [membership1, membership2]
        
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = member
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_member_schedule_count("1")
        
        assert result == 2

    @patch("services.membros_service.session_scope")
    def test_count_schedules_none_found(self, mock_session_scope, mock_session):
        """Count returns 0 when member not found."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_member_schedule_count("999")
        
        assert result == 0


class TestMembrosServiceGetAllMemberNames:
    """Test getting all member names for validation."""

    @patch("services.membros_service.session_scope")
    def test_get_all_names_success(self, mock_session_scope, mock_session):
        """Get list of all member names."""
        member1 = Member(id="1", name="Alice")
        member2 = Member(id="2", name="Bob")
        
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.all.return_value = [member1, member2]
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_all_member_names()
        
        assert result == ["Alice", "Bob"]

    @patch("services.membros_service.session_scope")
    def test_get_all_names_empty(self, mock_session_scope, mock_session):
        """Get empty list when no members exist."""
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.all.return_value = []
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_all_member_names()
        
        assert result == []


class TestMembrosServiceSquadAssignment:
    """Test assigning/removing members from squads."""

    @patch("services.membros_service.session_scope")
    def test_assign_member_to_squad_success(self, mock_session_scope):
        """Assign member to squad successfully."""
        member = Member(id="1", name="João")
        squad = Squad(id="squad-1", nome="Squad A")
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        
        # Setup the chain of mock calls
        query_mock = MagicMock()
        mock_session.query.return_value = query_mock
        
        # First call: filter_by(member_id) returns member
        # Second call: filter_by(squad_id) returns squad
        # Third call: filter_by(member_id, squad_id) returns None (no existing)
        query_mock.filter_by.side_effect = [
            MagicMock(first=MagicMock(return_value=member)),
            MagicMock(first=MagicMock(return_value=squad)),
            MagicMock(first=MagicMock(return_value=None)),
        ]
        
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.assign_member_to_squad("1", "squad-1", level=2)
        
        assert result is not None
        mock_session.add.assert_called_once()

    @patch("services.membros_service.session_scope")
    def test_assign_member_not_found(self, mock_session_scope):
        """Assign non-existent member should fail."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.assign_member_to_squad("999", "squad-1")
        
        assert result is None
        mock_session.add.assert_not_called()

    @patch("services.membros_service.session_scope")
    def test_assign_squad_not_found(self, mock_session_scope):
        """Assign to non-existent squad should fail."""
        member = Member(id="1", name="João")
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        
        query_mock = MagicMock()
        mock_session.query.return_value = query_mock
        
        # First call: filter_by(member_id) returns member
        # Second call: filter_by(squad_id) returns None
        query_mock.filter_by.side_effect = [
            MagicMock(first=MagicMock(return_value=member)),
            MagicMock(first=MagicMock(return_value=None)),
        ]
        
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.assign_member_to_squad("1", "squad-999")
        
        assert result is None
        mock_session.add.assert_not_called()

    @patch("services.membros_service.session_scope")
    def test_assign_member_already_in_squad(self, mock_session_scope):
        """Assigning member already in squad should fail."""
        member = Member(id="1", name="João")
        squad = Squad(id="squad-1", nome="Squad A")
        existing = MemberSquad(member_id="1", squad_id="squad-1", level=1)
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        
        query_mock = MagicMock()
        mock_session.query.return_value = query_mock
        
        # First call: filter_by(member_id) returns member
        # Second call: filter_by(squad_id) returns squad
        # Third call: filter_by(member_id, squad_id) returns existing
        query_mock.filter_by.side_effect = [
            MagicMock(first=MagicMock(return_value=member)),
            MagicMock(first=MagicMock(return_value=squad)),
            MagicMock(first=MagicMock(return_value=existing)),
        ]
        
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.assign_member_to_squad("1", "squad-1")
        
        assert result is None
        mock_session.add.assert_not_called()

    @patch("services.membros_service.session_scope")
    def test_assign_member_to_squad_exception(self, mock_session_scope):
        """Handle exceptions during assignment."""
        member = Member(id="1", name="João")
        squad = Squad(id="squad-1", nome="Squad A")
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        
        query_mock = MagicMock()
        mock_session.query.return_value = query_mock
        
        query_mock.filter_by.side_effect = [
            MagicMock(first=MagicMock(return_value=member)),
            MagicMock(first=MagicMock(return_value=squad)),
            MagicMock(first=MagicMock(return_value=None)),
        ]
        
        mock_session.add.side_effect = Exception("DB Error")
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.assign_member_to_squad("1", "squad-1")
        
        assert result is None

    @patch("services.membros_service.session_scope")
    def test_remove_member_from_squad_success(self, mock_session_scope):
        """Remove member from squad successfully."""
        membership = MemberSquad(member_id="1", squad_id="squad-1", level=1)
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = membership
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.remove_member_from_squad("1", "squad-1")
        
        assert result is True
        mock_session.delete.assert_called_once()

    @patch("services.membros_service.session_scope")
    def test_remove_member_from_squad_not_found(self, mock_session_scope):
        """Remove non-existent membership should fail."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.remove_member_from_squad("999", "squad-999")
        
        assert result is False
        mock_session.delete.assert_not_called()

    @patch("services.membros_service.session_scope")
    def test_remove_member_from_squad_exception(self, mock_session_scope):
        """Handle exceptions during removal."""
        membership = MemberSquad(member_id="1", squad_id="squad-1", level=1)
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = membership
        mock_session.delete.side_effect = Exception("DB Error")
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.remove_member_from_squad("1", "squad-1")
        
        assert result is False

    @patch("services.membros_service.session_scope")
    def test_get_member_squads_success(self, mock_session_scope):
        """Get all squads for a member."""
        squad1 = Squad(id="squad-1", nome="Squad A")
        squad2 = Squad(id="squad-2", nome="Squad B")
        membership1 = MemberSquad(member_id="1", squad_id="squad-1", level=1)
        membership1.squad = squad1
        membership2 = MemberSquad(member_id="1", squad_id="squad-2", level=2)
        membership2.squad = squad2
        
        member = Member(id="1", name="João")
        member.memberships = [membership1, membership2]
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = member
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_member_squads("1")
        
        assert len(result) == 2
        assert result[0].nome == "Squad A"
        assert result[1].nome == "Squad B"

    @patch("services.membros_service.session_scope")
    def test_get_member_squads_not_found(self, mock_session_scope):
        """Get squads for non-existent member should return empty list."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.get_member_squads("999")
        
        assert result == []


class TestMembrosServiceExceptionHandling:
    """Test exception handling in service operations."""

    @patch("services.membros_service.session_scope")
    def test_create_member_exception(self, mock_session_scope):
        """Handle exception during member creation."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.add.side_effect = Exception("DB Error")
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.create_member("João")
        
        assert result is None

    @patch("services.membros_service.session_scope")
    def test_update_member_exception(self, mock_session_scope):
        """Handle exception during member update."""
        member = Member(id="1", name="João")
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = member
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.commit.side_effect = Exception("DB Error")
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.update_member("1", name="João Silva")
        
        assert result is None

    @patch("services.membros_service.session_scope")
    def test_delete_member_exception(self, mock_session_scope):
        """Handle exception during member deletion."""
        member = Member(id="1", name="João", status=True)
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = member
        mock_session.commit.side_effect = Exception("DB Error")
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.delete_member("1")
        
        assert result is False

    @patch("services.membros_service.session_scope")
    def test_update_with_partial_fields(self, mock_session_scope):
        """Update member with only some fields provided."""
        member = Member(id="1", name="João", phone_number="123", email="old@test.com")
        
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.query.return_value.filter_by.return_value.first.return_value = member
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session_scope.return_value = mock_session
        
        result = MembrosService.update_member("1", email="new@test.com", instagram="@new")
        
        assert result == member
        assert member.email == "new@test.com"
        assert member.instagram == "@new"
        assert member.phone_number == "123"
        mock_session.commit.assert_called_once()

    @patch("services.membros_service.session_scope")
    def test_create_member_none_name(self, mock_session_scope):
        """Creating member with None name should fail immediately."""
        mock_session_scope.return_value.__enter__.return_value = MagicMock()
        
        result = MembrosService.create_member(name=None)
        
        assert result is None
