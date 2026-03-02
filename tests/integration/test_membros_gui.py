"""Integration tests for MembrosFrame GUI refactoring.

Tests that the GUI correctly uses MembrosService and properly displays/manages members.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock

from gui.membros import MembrosFrame
from services.membros_service import MembrosService
from infra.database import Member, Squad, MemberSquad


class TestMembrosFrameInitialization(unittest.TestCase):
    """Test that MembrosFrame initializes correctly with MembrosService."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_membros_frame_initializes(self):
        """Verify that MembrosFrame initializes with MembrosService."""
        frame = MembrosFrame(self.root, db=None)
        
        # Check that service is injected
        self.assertIsNotNone(frame.service)
        self.assertIsInstance(frame.service, MembrosService)
        
        # Check that core UI components exist
        self.assertTrue(hasattr(frame, 'tree_membros'))
        self.assertTrue(hasattr(frame, 'squads_widgets'))
        self.assertTrue(hasattr(frame, '_membro_selecionado'))
        
        # Check that patentes are initialized
        self.assertEqual(frame.patentes, ["Líder", "Treinador", "Membro", "Recruta"])

    def test_membros_frame_has_required_methods(self):
        """Verify that MembrosFrame has all required CRUD methods."""
        frame = MembrosFrame(self.root, db=None)
        
        required_methods = ['adicionar', 'editar', 'remover', 'salvar_squads', 'atualizar_lista']
        for method_name in required_methods:
            self.assertTrue(hasattr(frame, method_name), f"Missing method: {method_name}")
            self.assertTrue(callable(getattr(frame, method_name)), f"Not callable: {method_name}")


class TestMembrosFrameDataDisplaying(unittest.TestCase):
    """Test that MembrosFrame correctly displays member data from service."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_atualizar_lista_calls_service(self):
        """Verify that atualizar_lista uses MembrosService.get_all_members()."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock the service
        frame.service.get_all_members = Mock(return_value=[])
        
        # Call atualizar_lista
        frame.atualizar_lista()
        
        # Verify service was called
        frame.service.get_all_members.assert_called_once()

    @patch('gui.membros.session_scope')
    def test_membros_aparecem_na_treeview(self, mock_session_scope):
        """Verify that members appear in the treeview after atualizar_lista."""
        # Create mock members
        mock_member1 = Mock(spec=Member)
        mock_member1.id = "member-1"
        mock_member1.name = "João Silva"
        mock_member1.phone_number = "111222333"
        mock_member1.memberships = []
        
        mock_member2 = Mock(spec=Member)
        mock_member2.id = "member-2"
        mock_member2.name = "Maria Santos"
        mock_member2.phone_number = "444555666"
        mock_member2.memberships = []
        
        frame = MembrosFrame(self.root, db=None)
        frame.service.get_all_members = Mock(return_value=[mock_member1, mock_member2])
        
        # Call atualizar_lista
        frame.atualizar_lista()
        
        # Verify members appear in treeview
        all_items = frame.tree_membros.get_children()
        self.assertEqual(len(all_items), 2)
        
        # Check first item values
        values = frame.tree_membros.item(all_items[0], 'values')
        self.assertEqual(values[0], "João Silva")
        self.assertEqual(values[1], "111222333")

    def test_atualizar_lista_handles_error(self):
        """Verify that atualizar_lista gracefully handles service errors."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock service to raise an error
        frame.service.get_all_members = Mock(side_effect=Exception("DB Error"))
        
        # This should not raise an exception - error should be caught
        try:
            frame.atualizar_lista()
        except Exception as e:
            self.fail(f"atualizar_lista raised {type(e).__name__} unexpectedly!")


class TestMembrosFrameCreateMember(unittest.TestCase):
    """Test that MembrosFrame correctly creates members via service."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    @patch('gui.membros.MembroDialog')
    def test_create_membro_via_gui(self, mock_dialog_class):
        """Verify that adicionar() calls MembrosService.create_member()."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock the dialog to return form data
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("João Test", "joao@test.com", "123456789", "Recruta", "", "")
        mock_dialog_class.return_value = mock_dialog_instance
        
        # Mock the service
        frame.service.create_member = Mock(return_value=Mock(spec=Member))
        frame.atualizar_lista = Mock()
        
        # Call adicionar
        frame.adicionar()
        
        # Verify service.create_member was called with correct params
        frame.service.create_member.assert_called_once()
        call_args = frame.service.create_member.call_args
        self.assertEqual(call_args[1]['name'], "João Test")
        self.assertEqual(call_args[1]['email'], "joao@test.com")
        self.assertEqual(call_args[1]['phone_number'], "123456789")
        
        # Verify list was updated
        frame.atualizar_lista.assert_called_once()

    @patch('gui.membros.MembroDialog')
    def test_create_membro_handles_validation_error(self, mock_dialog_class):
        """Verify that adicionar() handles ValueError from service."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Duplicado", "test@test.com", "123", "Recruta", "", "")
        mock_dialog_class.return_value = mock_dialog_instance
        
        # Mock service to raise ValueError for duplicate
        frame.service.create_member = Mock(side_effect=ValueError("Membro já existe"))
        frame.atualizar_lista = Mock()
        
        # Should not raise, error should be handled in messagebox
        try:
            frame.adicionar()
        except Exception:
            self.fail("adicionar() did not handle ValueError")
        
        # List should not be updated on error
        frame.atualizar_lista.assert_not_called()

    @patch('gui.membros.MembroDialog')
    def test_create_membro_cancellation(self, mock_dialog_class):
        """Verify that adicionar() does nothing if dialog is canceled."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock dialog to return None (cancellation)
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = None
        mock_dialog_class.return_value = mock_dialog_instance
        
        # Mock the service
        frame.service.create_member = Mock()
        frame.atualizar_lista = Mock()
        
        # Call adicionar
        frame.adicionar()
        
        # Verify service was NOT called
        frame.service.create_member.assert_not_called()
        frame.atualizar_lista.assert_not_called()


class TestMembrosFrameEditMember(unittest.TestCase):
    """Test that MembrosFrame correctly edits members via service."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_edit_membro_requires_selection(self):
        """Verify that editar() requires a selection."""
        frame = MembrosFrame(self.root, db=None)
        
        # Clear any selection
        frame.tree_membros.selection_remove(frame.tree_membros.selection())
        
        # Mock the service
        frame.service.update_member = Mock()
        
        # Call editar with no selection
        frame.editar()
        
        # Service should not be called
        frame.service.update_member.assert_not_called()

    @patch('gui.membros.MembroDialog')
    def test_edit_membro_via_gui(self, mock_dialog_class):
        """Verify that editar() calls MembrosService.update_member()."""
        frame = MembrosFrame(self.root, db=None)
        
        # Create a mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.name = "João Original"
        mock_member.email = "joao@test.com"
        mock_member.phone_number = "123456789"
        
        # Add to treeview
        frame.tree_membros.insert("", "end", iid="member-1", values=("João Original", "123456789", ""))
        frame.tree_membros.selection_set("member-1")
        
        # Mock dialog to return updated data
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("João Updated", "joao.updated@test.com", "987654321", "Treinador", "", "")
        mock_dialog_class.return_value = mock_dialog_instance
        
        # Mock service
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.update_member = Mock(return_value=mock_member)
        frame.atualizar_lista = Mock()
        
        # Call editar
        frame.editar()
        
        # Verify service.update_member was called
        frame.service.update_member.assert_called_once()
        call_args = frame.service.update_member.call_args
        self.assertEqual(call_args[1]['member_id'], "member-1")
        self.assertEqual(call_args[1]['name'], "João Updated")
        self.assertEqual(call_args[1]['email'], "joao.updated@test.com")
        self.assertEqual(call_args[1]['phone_number'], "987654321")
        
        # Verify list was updated
        frame.atualizar_lista.assert_called_once()

    @patch('gui.membros.MembroDialog')
    def test_edit_membro_cancellation(self, mock_dialog_class):
        """Verify that editar() does nothing if dialog is canceled."""
        frame = MembrosFrame(self.root, db=None)
        
        # Create a mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.name = "João"
        mock_member.email = "joao@test.com"
        mock_member.phone_number = "123456789"
        
        # Add to treeview and select
        frame.tree_membros.insert("", "end", iid="member-1", values=("João", "123456789", ""))
        frame.tree_membros.selection_set("member-1")
        
        # Mock dialog to return None (cancellation)
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = None
        mock_dialog_class.return_value = mock_dialog_instance
        
        # Mock service
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.update_member = Mock()
        frame.atualizar_lista = Mock()
        
        # Call editar
        frame.editar()
        
        # Verify service was NOT called
        frame.service.update_member.assert_not_called()
        frame.atualizar_lista.assert_not_called()

    @patch('gui.membros.MembroDialog')
    def test_edit_membro_handles_error(self, mock_dialog_class):
        """Verify that editar() handles errors gracefully."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("João Updated", "joao@test.com", "123", "Recruta", "", "")
        mock_dialog_class.return_value = mock_dialog_instance
        
        # Add item to treeview
        frame.tree_membros.insert("", "end", iid="member-1", values=("João", "123", ""))
        frame.tree_membros.selection_set("member-1")
        
        # Mock service to raise error
        frame.service.get_member_by_id = Mock(side_effect=Exception("DB Error"))
        frame.service.update_member = Mock()
        
        # Should not raise
        try:
            frame.editar()
        except Exception:
            self.fail("editar() did not handle error")
        
        # Update should not be called
        frame.service.update_member.assert_not_called()


class TestMembrosFrameDeleteMember(unittest.TestCase):
    """Test that MembrosFrame correctly deletes members via service."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_delete_membro_requires_selection(self):
        """Verify that remover() requires a selection."""
        frame = MembrosFrame(self.root, db=None)
        
        # Clear any selection
        frame.tree_membros.selection_remove(frame.tree_membros.selection())
        
        # Mock the service
        frame.service.delete_member = Mock()
        
        # Call remover with no selection
        frame.remover()
        
        # Service should not be called
        frame.service.delete_member.assert_not_called()

    @patch('gui.membros.messagebox.askyesno')
    def test_delete_membro_via_gui(self, mock_ask):
        """Verify that remover() calls MembrosService.delete_member()."""
        frame = MembrosFrame(self.root, db=None)
        
        # Create a mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.name = "João to Delete"
        
        # Add to treeview manually
        frame.tree_membros.insert("", "end", iid="member-1", values=("João to Delete", "123", ""))
        frame.tree_membros.selection_set("member-1")
        
        # Mock dialog to confirm deletion
        mock_ask.return_value = True
        
        # Mock service
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.delete_member = Mock(return_value=True)
        frame.atualizar_lista = Mock()
        
        # Call remover
        frame.remover()
        
        # Verify service was called
        frame.service.delete_member.assert_called_once_with("member-1")
        frame.atualizar_lista.assert_called_once()

    @patch('gui.membros.messagebox.askyesno')
    def test_delete_membro_cancellation(self, mock_ask):
        """Verify that remover() respects user cancellation."""
        frame = MembrosFrame(self.root, db=None)
        
        # Create a mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.name = "João"
        
        # Add to treeview
        frame.tree_membros.insert("", "end", iid="member-1", values=("João", "123", ""))
        frame.tree_membros.selection_set("member-1")
        
        # Mock dialog to cancel deletion
        mock_ask.return_value = False
        
        # Mock service
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.delete_member = Mock()
        frame.atualizar_lista = Mock()
        
        # Call remover
        frame.remover()
        
        # Service should not be called
        frame.service.delete_member.assert_not_called()
        frame.atualizar_lista.assert_not_called()


class TestMembrosFrameSquadAssignment(unittest.TestCase):
    """Test that MembrosFrame correctly manages squad assignments."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_assign_membro_to_squad(self):
        """Verify that salvar_squads() calls service for squad assignments."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.memberships = []
        
        # Set up frame state
        frame._membro_selecionado = "member-1"
        
        # Create squad widget state: squad-1 selected, squad-2 not selected
        squad1_check = tk.BooleanVar(value=True)
        squad1_rank = tk.StringVar(value="1")
        frame.squads_widgets["squad-1"] = (squad1_check, squad1_rank)
        
        squad2_check = tk.BooleanVar(value=False)
        squad2_rank = tk.StringVar(value="1")
        frame.squads_widgets["squad-2"] = (squad2_check, squad2_rank)
        
        # Mock service methods
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.assign_member_to_squad = Mock(return_value=Mock(spec=MemberSquad))
        frame.service.remove_member_from_squad = Mock(return_value=True)
        frame.atualizar_lista = Mock()
        frame.tree_membros.selection_set = Mock()
        frame._on_select = Mock()
        
        # Call salvar_squads
        frame.salvar_squads()
        
        # Verify assign was called for squad-1
        frame.service.assign_member_to_squad.assert_called_once_with(
            member_id="member-1",
            squad_id="squad-1",
            level=1
        )

    def test_salvar_squads_requires_selection(self):
        """Verify that salvar_squads() requires a member selection."""
        frame = MembrosFrame(self.root, db=None)
        
        # No member selected
        frame._membro_selecionado = None
        
        # Mock service
        frame.service.get_member_by_id = Mock()
        
        # Call salvar_squads
        frame.salvar_squads()
        
        # Service should not be called
        frame.service.get_member_by_id.assert_not_called()

    def test_salvar_squads_handles_error(self):
        """Verify that salvar_squads() handles errors gracefully."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.memberships = []
        
        # Set up frame state
        frame._membro_selecionado = "member-1"
        
        # Create squad widget
        squad_check = tk.BooleanVar(value=True)
        squad_rank = tk.StringVar(value="1")
        frame.squads_widgets["squad-1"] = (squad_check, squad_rank)
        
        # Mock service to raise error
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.assign_member_to_squad = Mock(side_effect=Exception("DB Error"))
        
        # Should not raise
        try:
            frame.salvar_squads()
        except Exception:
            self.fail("salvar_squads() did not handle error")

    def test_remove_squad_assignment(self):
        """Verify that removing squad checkbox calls remove_member_from_squad."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock member with existing squad membership
        mock_membership = Mock(spec=MemberSquad)
        mock_membership.squad_id = "squad-1"
        mock_membership.level = 1
        
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.memberships = [mock_membership]
        
        # Set up frame state
        frame._membro_selecionado = "member-1"
        
        # Create squad widget state: squad-1 was enrolled, now unchecked
        squad_check = tk.BooleanVar(value=False)
        squad_rank = tk.StringVar(value="1")
        frame.squads_widgets["squad-1"] = (squad_check, squad_rank)
        
        # Mock service methods
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.remove_member_from_squad = Mock(return_value=True)
        frame.atualizar_lista = Mock()
        frame.tree_membros.selection_set = Mock()
        frame._on_select = Mock()
        
        # Call salvar_squads
        frame.salvar_squads()
        
        # Verify remove was called
        frame.service.remove_member_from_squad.assert_called_once_with(
            member_id="member-1",
            squad_id="squad-1"
        )

    def test_salvar_squads_multiple_assignments(self):
        """Verify that salvar_squads() handles multiple squad assignments."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.memberships = []
        
        # Set up frame state
        frame._membro_selecionado = "member-1"
        
        # Create multiple squad widgets
        for i in range(1, 4):
            squad_id = f"squad-{i}"
            squad_check = tk.BooleanVar(value=(i <= 2))  # First 2 squads selected
            squad_rank = tk.StringVar(value=str(i))
            frame.squads_widgets[squad_id] = (squad_check, squad_rank)
        
        # Mock service methods
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.assign_member_to_squad = Mock(return_value=Mock(spec=MemberSquad))
        frame.service.remove_member_from_squad = Mock(return_value=True)
        frame.atualizar_lista = Mock()
        frame.tree_membros.selection_set = Mock()
        frame._on_select = Mock()
        
        # Call salvar_squads
        frame.salvar_squads()
        
        # Verify assign was called for squad-1 and squad-2
        self.assertEqual(frame.service.assign_member_to_squad.call_count, 2)
        
        # Verify remove was called for squad-3 (never was enrolled, so no remove)
        self.assertEqual(frame.service.remove_member_from_squad.call_count, 0)


class TestMembrosFrameSquadSelection(unittest.TestCase):
    """Test that MembrosFrame correctly loads squads when member is selected."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    @patch('gui.membros.session_scope')
    def test_on_select_loads_squads(self, mock_session_scope):
        """Verify that _on_select() loads squads from service."""
        frame = MembrosFrame(self.root, db=None)
        
        # Create mock squads
        mock_squad1 = Mock(spec=Squad)
        mock_squad1.id = "squad-1"
        mock_squad1.nome = "Time Alpha"
        
        mock_squad2 = Mock(spec=Squad)
        mock_squad2.id = "squad-2"
        mock_squad2.nome = "Time Beta"
        
        # Create mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.name = "João"
        mock_member.memberships = []
        
        # Add member to treeview
        frame.tree_membros.insert("", "end", iid="member-1", values=("João", "123", ""))
        frame.tree_membros.selection_set("member-1")
        
        # Mock service methods
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.get_all_squads = Mock(return_value=[mock_squad1, mock_squad2])
        
        # Call _on_select
        frame._on_select()
        
        # Verify service was called
        frame.service.get_member_by_id.assert_called_once_with("member-1")
        frame.service.get_all_squads.assert_called_once()
        
        # Verify label was updated with member name
        self.assertIn("João", frame._lbl_nome.cget("text"))

    def test_on_select_no_selection(self):
        """Verify that _on_select() does nothing if no member is selected."""
        frame = MembrosFrame(self.root, db=None)
        
        # No selection
        frame.tree_membros.selection_remove(frame.tree_membros.selection())
        
        # Mock service
        frame.service.get_member_by_id = Mock()
        frame.service.get_all_squads = Mock()
        
        # Call _on_select - should return early
        frame._on_select()
        
        # Service should not be called
        frame.service.get_member_by_id.assert_not_called()

    def test_on_select_no_squads_available(self):
        """Verify that _on_select() handles case when no squads exist."""
        frame = MembrosFrame(self.root, db=None)
        
        # Create mock member
        mock_member = Mock(spec=Member)
        mock_member.id = "member-1"
        mock_member.name = "João"
        mock_member.memberships = []
        
        # Add member to treeview
        frame.tree_membros.insert("", "end", iid="member-1", values=("João", "123", ""))
        frame.tree_membros.selection_set("member-1")
        
        # Mock service to return no squads
        frame.service.get_member_by_id = Mock(return_value=mock_member)
        frame.service.get_all_squads = Mock(return_value=[])
        
        # Call _on_select
        frame._on_select()
        
        # Verify placeholder message was shown
        placeholder_found = False
        for widget in frame._inner.winfo_children():
            if hasattr(widget, 'cget'):
                text = widget.cget('text')
                if 'Nenhum time' in text:
                    placeholder_found = True
                    break
        self.assertTrue(placeholder_found, "Placeholder for no squads not found")



    """Test error handling in MembrosFrame."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_error_handling_duplicate_name(self):
        """Verify that duplicate name errors are properly caught and displayed."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock dialog with duplicate name
        with patch('gui.membros.MembroDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.result = ("Duplicado", None, None, "Recruta", "", "")
            mock_dialog_class.return_value = mock_dialog
            
            # Mock service to raise ValueError
            frame.service.create_member = Mock(side_effect=ValueError("Membro já existe"))
            frame.atualizar_lista = Mock()
            
            # Call adicionar - should handle error without raising
            try:
                frame.adicionar()
            except Exception as e:
                self.fail(f"Error not handled: {e}")
            
            # List should not be updated
            frame.atualizar_lista.assert_not_called()

    def test_atualizar_lista_empty_result(self):
        """Verify that atualizar_lista handles empty member list."""
        frame = MembrosFrame(self.root, db=None)
        
        # Mock service to return empty list
        frame.service.get_all_members = Mock(return_value=[])
        
        # Call atualizar_lista
        frame.atualizar_lista()
        
        # Treeview should be empty
        items = frame.tree_membros.get_children()
        self.assertEqual(len(items), 0)
        
        # Label should show 0 membros
        self.assertIn("(0 membro", frame._lbl_count.cget("text"))


if __name__ == "__main__":
    unittest.main()
