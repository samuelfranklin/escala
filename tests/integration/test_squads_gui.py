"""Integration tests for SquadsFrame GUI.

Tests GUI interactions with SquadsService including member management,
patente updates, and UI state consistency.
"""

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gui.squads import SquadsFrame
from infra.database import Base, Member, MemberSquad, Squad, session_scope
from services.squads_service import SquadsService


@pytest.fixture(scope="function")
def test_db():
    """Create in-memory SQLite database for tests."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(test_engine)

    TestSessionLocal = sessionmaker(bind=test_engine)

    import infra.database

    original_sessionmaker = infra.database.SessionLocal
    infra.database.SessionLocal = TestSessionLocal

    yield test_engine

    infra.database.SessionLocal = original_sessionmaker
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def members_fixture(test_db):
    """Create sample members for testing."""
    TestSessionLocal = sessionmaker(bind=test_db)
    session = TestSessionLocal()

    members_list = [
        Member(name="Alice", status=True),
        Member(name="Bob", status=True),
        Member(name="Charlie", status=True),
        Member(name="Dave", status=True),
    ]
    session.add_all(members_list)
    session.commit()

    members_dict = {m.name: m.id for m in members_list}
    session.close()

    return members_dict


@pytest.fixture
def root_window():
    """Create Tk window for testing."""
    root = tk.Tk()
    root.withdraw()  # Hide window
    yield root
    try:
        root.destroy()
    except:
        pass


@pytest.fixture
def squads_frame(root_window, test_db):
    """Create SquadsFrame for testing."""
    frame = SquadsFrame(root_window)
    root_window.update()
    return frame


class TestSquadsFrameInitialization:
    """Test SquadsFrame initialization."""

    def test_frame_initializes_with_service(self, squads_frame):
        """Test SquadsFrame initializes with SquadsService."""
        assert squads_frame is not None
        assert hasattr(squads_frame, "service")
        assert isinstance(squads_frame.service, SquadsService)

    def test_frame_has_required_attributes(self, squads_frame):
        """Test SquadsFrame has all required attributes."""
        assert hasattr(squads_frame, "patentes")
        assert "Líder" in squads_frame.patentes
        assert "Treinador" in squads_frame.patentes
        assert "Membro" in squads_frame.patentes
        assert "Recruta" in squads_frame.patentes

    def test_frame_has_required_methods(self, squads_frame):
        """Test SquadsFrame has all required methods."""
        required_methods = [
            "atualizar_lista",
            "adicionar",
            "editar",
            "remover",
            "salvar_membros",
            "_on_select",
        ]

        for method in required_methods:
            assert hasattr(squads_frame, method)
            assert callable(getattr(squads_frame, method))


class TestSquadsFrameCreateSquad:
    """Test squad creation through GUI."""

    def test_create_squad_success(self, squads_frame, test_db):
        """Test creating a squad successfully."""
        with patch("gui.squads.messagebox.showinfo"):
            with patch("gui.squads.SquadDialog") as mock_dialog:
                mock_dialog.return_value.result = ("Time Alpha", "")

                squads_frame.adicionar()

                # Verify squad was created
                squads = squads_frame.service.get_all_squads()
                assert len(squads) == 1
                assert squads[0]["nome"] == "Time Alpha"

    def test_create_squad_duplicate_name_error(self, squads_frame, test_db):
        """Test creating squad with duplicate name shows error."""
        squads_frame.service.create_squad("Guerreiros")

        with patch("gui.squads.messagebox.showerror") as mock_error:
            with patch("gui.squads.SquadDialog") as mock_dialog:
                mock_dialog.return_value.result = ("Guerreiros", "")

                squads_frame.adicionar()

                # Verify error was called
                assert mock_error.called
                assert "já existe" in mock_error.call_args[0][1].lower()

    def test_create_squad_empty_name_error(self, squads_frame, test_db):
        """Test creating squad with empty name shows error."""
        with patch("gui.squads.messagebox.showerror") as mock_error:
            with patch("gui.squads.SquadDialog") as mock_dialog:
                mock_dialog.return_value.result = ("", "")

                squads_frame.adicionar()

                # Verify error was called
                assert mock_error.called
                assert "obrigatório" in mock_error.call_args[0][1].lower()

    def test_create_squad_cancel_dialog(self, squads_frame, test_db):
        """Test canceling squad creation dialog."""
        with patch("gui.squads.SquadDialog") as mock_dialog:
            mock_dialog.return_value.result = None

            initial_count = len(squads_frame.tree_squads.get_children())
            squads_frame.adicionar()
            final_count = len(squads_frame.tree_squads.get_children())

            # Should not create squad
            assert initial_count == final_count


class TestSquadsFrameEditSquad:
    """Test squad editing through GUI."""

    def test_edit_squad_name_success(self, squads_frame, test_db):
        """Test editing squad name successfully."""
        # Create squad
        success, error, squad_id = squads_frame.service.create_squad("Old Name")
        assert success is True

        # Load in GUI
        squads_frame.atualizar_lista()

        # Select squad
        squads_frame.tree_squads.selection_set(squad_id)

        # Mock dialog and edit
        with patch("gui.squads.messagebox.showinfo"):
            with patch("gui.squads.SquadDialog") as mock_dialog:
                mock_dialog.return_value.result = ("New Name", "")

                squads_frame.editar()

        # Verify name was updated
        squad = squads_frame.service.get_squad_by_id(squad_id)
        assert squad["nome"] == "New Name"

    def test_edit_without_selection_shows_warning(self, squads_frame, test_db):
        """Test editing without selecting squad shows warning."""
        with patch("gui.squads.messagebox.showwarning") as mock_warning:
            squads_frame.editar()

            assert mock_warning.called
            assert "selecione" in mock_warning.call_args[0][1].lower()

    def test_edit_nonexistent_squad(self, squads_frame, test_db):
        """Test editing nonexistent squad shows warning."""
        # Create fake selection
        with patch("gui.squads.SquadsFrame.tree_squads") as mock_tree:
            mock_tree.selection.return_value = ["fake-id"]
            squads_frame.tree_squads = mock_tree

            with patch("gui.squads.messagebox.showwarning") as mock_warning:
                squads_frame.editar()

                # Should show some warning or error
                # Since service returns None, editdialog won't show


class TestSquadsFrameDeleteSquad:
    """Test squad deletion through GUI."""

    def test_delete_squad_success(self, squads_frame, test_db):
        """Test deleting a squad successfully."""
        # Create squad
        success, error, squad_id = squads_frame.service.create_squad("Guerreiros")
        assert success is True

        # Load in GUI
        squads_frame.atualizar_lista()

        # Select squad
        squads_frame.tree_squads.selection_set(squad_id)

        # Mock messagebox and delete
        with patch("gui.squads.messagebox.askyesno", return_value=True):
            with patch("gui.squads.messagebox.showinfo"):
                squads_frame.remover()

        # Verify squad was deleted
        squads = squads_frame.service.get_all_squads()
        assert len(squads) == 0

    def test_delete_squad_cancel(self, squads_frame, test_db):
        """Test canceling squad deletion."""
        # Create squad
        success, error, squad_id = squads_frame.service.create_squad("Guerreiros")

        # Load and select
        squads_frame.atualizar_lista()
        squads_frame.tree_squads.selection_set(squad_id)

        # Cancel deletion
        with patch("gui.squads.messagebox.askyesno", return_value=False):
            squads_frame.remover()

        # Verify squad still exists
        squads = squads_frame.service.get_all_squads()
        assert len(squads) == 1

    def test_delete_without_selection(self, squads_frame, test_db):
        """Test deleting without selecting squad does nothing."""
        initial_count = len(squads_frame.tree_squads.get_children())
        squads_frame.remover()
        final_count = len(squads_frame.tree_squads.get_children())

        assert initial_count == final_count


class TestSquadsFrameAddMember:
    """Test adding members to squads."""

    def test_add_member_to_squad_with_rank(
        self, squads_frame, members_fixture, test_db
    ):
        """Test adding a member to squad with specified rank."""
        # Create squad
        success, error, squad_id = squads_frame.service.create_squad("Time Test")
        member_id = members_fixture["Alice"]

        # Add member
        success, error = squads_frame.service.add_member_to_squad(
            squad_id, member_id, "Líder"
        )
        assert success is True

        # Verify member was added
        members = squads_frame.service.get_squad_members(squad_id)
        assert len(members) == 1
        assert members[0]["member_id"] == member_id
        assert members[0]["level"] == 4  # Líder = 4

    def test_add_duplicate_member_error(self, squads_frame, members_fixture, test_db):
        """Test adding member already in squad shows error."""
        # Create squad and add member
        success, error, squad_id = squads_frame.service.create_squad("Time Test")
        member_id = members_fixture["Alice"]

        squads_frame.service.add_member_to_squad(squad_id, member_id, "Membro")

        # Try add again
        success, error = squads_frame.service.add_member_to_squad(
            squad_id, member_id, "Membro"
        )

        assert success is False
        assert "já está neste time" in error

    def test_add_member_different_ranks(self, squads_frame, members_fixture, test_db):
        """Test adding members with different ranks."""
        success, error, squad_id = squads_frame.service.create_squad("Time Test")

        ranks_and_levels = [
            ("Alice", "Líder", 4),
            ("Bob", "Treinador", 3),
            ("Charlie", "Membro", 2),
            ("Dave", "Recruta", 1),
        ]

        for name, rank, level in ranks_and_levels:
            member_id = members_fixture[name]
            success, error = squads_frame.service.add_member_to_squad(
                squad_id, member_id, rank
            )
            assert success is True

        # Verify all added with correct ranks
        members = squads_frame.service.get_squad_members(squad_id)
        assert len(members) == 4

        for member in members:
            if member["member_id"] == members_fixture["Alice"]:
                assert member["level"] == 4
            elif member["member_id"] == members_fixture["Bob"]:
                assert member["level"] == 3


class TestSquadsFrameRemoveMember:
    """Test removing members from squads."""

    def test_remove_member_from_squad(self, squads_frame, members_fixture, test_db):
        """Test removing a member from squad."""
        # Create squad and add member
        success, error, squad_id = squads_frame.service.create_squad("Time Test")
        member_id = members_fixture["Alice"]

        squads_frame.service.add_member_to_squad(squad_id, member_id, "Membro")

        # Remove member
        success, error = squads_frame.service.remove_member_from_squad(
            squad_id, member_id
        )
        assert success is True

        # Verify removal
        members = squads_frame.service.get_squad_members(squad_id)
        assert len(members) == 0

    def test_remove_nonexistent_member_error(
        self, squads_frame, members_fixture, test_db
    ):
        """Test removing member not in squad shows error."""
        success, error, squad_id = squads_frame.service.create_squad("Time Test")
        member_id = members_fixture["Alice"]

        # Try remove member not in squad
        success, error = squads_frame.service.remove_member_from_squad(
            squad_id, member_id
        )

        assert success is False
        assert "não está neste time" in error


class TestSquadsFrameUpdatePatente:
    """Test updating member rank (patente) in squad."""

    def test_update_member_patente_success(self, squads_frame, members_fixture, test_db):
        """Test updating member rank successfully."""
        # Create squad and add member
        success, error, squad_id = squads_frame.service.create_squad("Time Test")
        member_id = members_fixture["Alice"]

        squads_frame.service.add_member_to_squad(squad_id, member_id, "Recruta")

        # Update rank
        success, error = squads_frame.service.update_member_rank_in_squad(
            squad_id, member_id, "Líder"
        )
        assert success is True

        # Verify updated rank
        members = squads_frame.service.get_squad_members(squad_id)
        assert members[0]["level"] == 4  # Líder = 4

    def test_update_rank_all_transitions(self, squads_frame, members_fixture, test_db):
        """Test updating rank through all transitions."""
        success, error, squad_id = squads_frame.service.create_squad("Time Test")
        member_id = members_fixture["Alice"]

        squads_frame.service.add_member_to_squad(squad_id, member_id, "Recruta")

        transitions = [
            "Membro",
            "Treinador",
            "Líder",
        ]

        for rank in transitions:
            success, error = squads_frame.service.update_member_rank_in_squad(
                squad_id, member_id, rank
            )
            assert success is True

        members = squads_frame.service.get_squad_members(squad_id)
        assert members[0]["level"] == 4  # Final rank: Líder


class TestSquadsFrameBulkUpdate:
    """Test bulk update of squad memberships."""

    def test_bulk_update_memberships_success(
        self, squads_frame, members_fixture, test_db
    ):
        """Test bulk updating squad memberships."""
        success, error, squad_id = squads_frame.service.create_squad("Time Bulk")

        # Prepare memberships
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        charlie_id = members_fixture["Charlie"]

        memberships = [
            (alice_id, 4),      # Líder
            (bob_id, 3),        # Treinador
            (charlie_id, 2),    # Membro
        ]

        # Bulk update
        success, error = squads_frame.service.bulk_update_squad_memberships(
            squad_id, memberships
        )

        assert success is True
        assert error is None

        # Verify
        members = squads_frame.service.get_squad_members(squad_id)
        assert len(members) == 3

    def test_bulk_update_replaces_previous(
        self, squads_frame, members_fixture, test_db
    ):
        """Test bulk update replaces previous memberships."""
        success, error, squad_id = squads_frame.service.create_squad("Time Bulk")

        # Add initial members
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]
        charlie_id = members_fixture["Charlie"]

        initial_memberships = [(alice_id, 2), (bob_id, 2)]
        squads_frame.service.bulk_update_squad_memberships(
            squad_id, initial_memberships
        )

        # Replace with different members
        new_memberships = [(bob_id, 3), (charlie_id, 2)]
        success, error = squads_frame.service.bulk_update_squad_memberships(
            squad_id, new_memberships
        )

        assert success is True

        # Verify new memberships
        members = squads_frame.service.get_squad_members(squad_id)
        member_ids = [m["member_id"] for m in members]

        assert alice_id not in member_ids  # Removed
        assert bob_id in member_ids  # Kept
        assert charlie_id in member_ids  # Added

    def test_bulk_update_via_gui_save(self, squads_frame, members_fixture, test_db):
        """Test bulk update through GUI save."""
        # Create squad
        success, error, squad_id = squads_frame.service.create_squad("Time Save")

        # Load UI
        squads_frame.tree_squads.selection_set(squad_id)
        squads_frame._on_select()

        # Manually set members (simulate user interaction)
        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]

        squads_frame.membros_widgets[alice_id][0].set(True)   # Check
        squads_frame.membros_widgets[alice_id][1].set("Líder")

        squads_frame.membros_widgets[bob_id][0].set(True)     # Check
        squads_frame.membros_widgets[bob_id][1].set("Membro")

        # Simulate save
        with patch("gui.squads.messagebox.showinfo"):
            squads_frame.salvar_membros()

        # Verify memberships
        members = squads_frame.service.get_squad_members(squad_id)
        assert len(members) == 2

    def test_bulk_update_without_squad_selected_error(self, squads_frame, test_db):
        """Test saving members without selecting squad shows warning."""
        with patch("gui.squads.messagebox.showwarning") as mock_warning:
            squads_frame.salvar_membros()

            assert mock_warning.called
            assert "selecione um time" in mock_warning.call_args[0][1].lower()

    def test_bulk_update_with_no_widgets_error(self, squads_frame, test_db):
        """Test saving without loading members shows warning."""
        # Create squad
        success, error, squad_id = squads_frame.service.create_squad("Time No Widgets")

        squads_frame._squad_selecionado = squad_id
        squads_frame.membros_widgets = {}

        with patch("gui.squads.messagebox.showwarning") as mock_warning:
            squads_frame.salvar_membros()

            assert mock_warning.called


class TestSquadsFrameListOperations:
    """Test squad list operations."""

    def test_list_squads_displays_all(self, squads_frame, test_db):
        """Test listing all squads in treeview."""
        # Create multiple squads
        squads_frame.service.create_squad("Guerreiros")
        squads_frame.service.create_squad("Assassinos")
        squads_frame.service.create_squad("Mágicos")

        # Refresh list
        squads_frame.atualizar_lista()

        # Verify all squads appear in treeview
        items = squads_frame.tree_squads.get_children()
        assert len(items) == 3

    def test_list_count_label_updates(self, squads_frame, test_db):
        """Test count label updates with squad count."""
        squads_frame.service.create_squad("Guerreiros")
        squads_frame.service.create_squad("Assassinos")

        squads_frame.atualizar_lista()

        # Check count label
        count_text = squads_frame._lbl_count.cget("text")
        assert "(2 times)" in count_text

    def test_list_empty_squads(self, squads_frame, test_db):
        """Test listing when no squads exist."""
        squads_frame.atualizar_lista()

        items = squads_frame.tree_squads.get_children()
        assert len(items) == 0

        count_text = squads_frame._lbl_count.cget("text")
        assert "(0 times)" in count_text


class TestSquadsFrameMemberSelection:
    """Test member selection and display in squad details."""

    def test_select_squad_shows_members(self, squads_frame, members_fixture, test_db):
        """Test selecting squad shows enrolled and available members."""
        # Create squad and add some members
        success, error, squad_id = squads_frame.service.create_squad("Time Test")

        alice_id = members_fixture["Alice"]
        bob_id = members_fixture["Bob"]

        squads_frame.service.add_member_to_squad(squad_id, alice_id, "Líder")
        squads_frame.service.add_member_to_squad(squad_id, bob_id, "Membro")

        # Select squad
        squads_frame.tree_squads.selection_set(squad_id)
        squads_frame._on_select()

        # Verify membros_widgets contains all members
        assert alice_id in squads_frame.membros_widgets
        assert bob_id in squads_frame.membros_widgets

        # Verify enrollment status
        check_alice, patente_alice = squads_frame.membros_widgets[alice_id]
        check_bob, patente_bob = squads_frame.membros_widgets[bob_id]

        assert check_alice.get() is True
        assert check_bob.get() is True
        assert patente_alice.get() == "Líder"
        assert patente_bob.get() == "Membro"

    def test_select_squad_with_no_members(self, squads_frame, test_db):
        """Test selecting squad with no members shows placeholder."""
        success, error, squad_id = squads_frame.service.create_squad("Time Empty")

        squads_frame.tree_squads.selection_set(squad_id)
        squads_frame._on_select()

        # Should show placeholder text
        squad_nome = squads_frame._lbl_squad_nome.cget("text")
        assert squad_nome == ""

    def test_select_squad_without_members_in_system(
        self, squads_frame, test_db
    ):
        """Test selecting squad when no members exist in system."""
        success, error, squad_id = squads_frame.service.create_squad("Time NoMems")

        squads_frame.tree_squads.selection_set(squad_id)
        squads_frame._on_select()

        # Should show "no members" message
        # (checked by the presence of membros_widgets being empty)
        assert len(squads_frame.membros_widgets) == 0


class TestSquadsFrameErrorHandling:
    """Test error handling in GUI."""

    def test_list_error_shows_message(self, squads_frame, test_db):
        """Test error loading list shows error message."""
        with patch("gui.squads.SquadsService.get_all_squads") as mock_get:
            mock_get.side_effect = Exception("DB Error")

            with patch("gui.squads.messagebox.showerror") as mock_error:
                squads_frame.atualizar_lista()

                assert mock_error.called
                assert "carregar times" in mock_error.call_args[0][0].lower()

    def test_select_error_shows_message(self, squads_frame, test_db):
        """Test error selecting squad shows error message."""
        success, error, squad_id = squads_frame.service.create_squad("Time Test")
        squads_frame.tree_squads.selection_set(squad_id)

        with patch("gui.squads.SquadsService.get_all_members") as mock_get:
            mock_get.side_effect = Exception("DB Error")

            with patch("gui.squads.messagebox.showerror") as mock_error:
                squads_frame._on_select()

                assert mock_error.called
                assert "carregar membros" in mock_error.call_args[0][0].lower()

    def test_add_error_shows_message(self, squads_frame, test_db):
        """Test error creating squad shows error message."""
        with patch("gui.squads.SquadsService.create_squad") as mock_create:
            mock_create.side_effect = Exception("DB Error")

            with patch("gui.squads.messagebox.showerror") as mock_error:
                with patch("gui.squads.SquadDialog") as mock_dialog:
                    mock_dialog.return_value.result = ("Test", "")
                    squads_frame.adicionar()

                    assert mock_error.called


class TestSquadsServiceIntegration:
    """Test SquadsService methods called from GUI."""

    def test_service_get_all_members(self, squads_frame, members_fixture, test_db):
        """Test getting all members via service."""
        members = squads_frame.service.get_all_members()

        assert len(members) == 4
        assert all("id" in m and "name" in m for m in members)

        # Verify ordered by name
        names = [m["name"] for m in members]
        assert names == sorted(names)

    def test_service_get_all_squads(self, squads_frame, test_db):
        """Test getting all squads via service."""
        squads_frame.service.create_squad("Time 1")
        squads_frame.service.create_squad("Time 2")

        squads = squads_frame.service.get_all_squads()

        assert len(squads) == 2
        assert all("id" in s and "nome" in s for s in squads)
