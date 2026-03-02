"""Integration tests for VisualizarFrame GUI component."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk

from gui.visualizar import VisualizarFrame
from infra.database import (
    create_tables,
    session_scope,
    Member,
    Squad,
    Event,
    EventSquad,
    MemberSquad,
)


class VisualizarFrameIntegrationTests(unittest.TestCase):
    """Integration tests for VisualizarFrame using service layer."""

    @classmethod
    def setUpClass(cls) -> None:
        """Setup test database and create test data."""
        create_tables()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls) -> None:
        """Create sample data for testing."""
        with session_scope() as session:
            # Create members
            member1 = Member(name="João Silva", status=True)
            member2 = Member(name="Maria Santos", status=True)
            session.add(member1)
            session.add(member2)
            session.flush()

            # Create squads
            squad1 = Squad(nome="Squad A")
            squad2 = Squad(nome="Squad B")
            session.add(squad1)
            session.add(squad2)
            session.flush()

            # Add members to squads
            session.add(
                MemberSquad(member_id=member1.id, squad_id=squad1.id, level=1)
            )
            session.add(
                MemberSquad(member_id=member2.id, squad_id=squad2.id, level=2)
            )

            # Create events
            event1 = Event(
                name="Evento A",
                type="tipo_a",
                date="2026-03-15",
                day_of_week="Domingo",
                time="10:00",
            )
            event2 = Event(
                name="Evento B",
                type="tipo_b",
                date="2026-03-20",
                day_of_week="Sexta",
                time="18:30",
            )
            session.add(event1)
            session.add(event2)
            session.flush()

            # Add squad allocations to events
            session.add(EventSquad(event_id=event1.id, squad_id=squad1.id, level=1, quantity=2))
            session.add(EventSquad(event_id=event2.id, squad_id=squad2.id, level=2, quantity=3))

            session.commit()

    def setUp(self):
        """Create a temporary root window for testing."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window

    def tearDown(self):
        """Clean up after each test."""
        self.root.destroy()

    def test_visualizar_frame_initializes(self):
        """Test that VisualizarFrame initializes without errors."""
        try:
            frame = VisualizarFrame(self.root)
            self.assertIsNotNone(frame)
            self.assertEqual(frame.escala_atual, [])
            self.assertTrue(hasattr(frame, 'tree'))
        except Exception as e:
            self.fail(f"VisualizarFrame initialization failed: {str(e)}")

    def test_load_schedule_from_service(self):
        """Test loading schedule from service via atualizar_lista."""
        frame = VisualizarFrame(self.root)
        
        try:
            frame.atualizar_lista()
            # Should load data for current month/year
            # May be empty if no events match current date
        except Exception as e:
            self.fail(f"atualizar_lista failed: {str(e)}")

    def test_filter_by_squad(self):
        """Test filtering schedule by squad."""
        frame = VisualizarFrame(self.root)
        
        try:
            # Get a squad ID from test data
            with session_scope() as session:
                squad = session.query(Squad).first()
                if squad:
                    frame.filtrar_por_squad(squad.id)
                    # Should not raise exception
        except Exception as e:
            self.fail(f"filtrar_por_squad failed: {str(e)}")

    def test_filter_by_member(self):
        """Test filtering schedule by member."""
        frame = VisualizarFrame(self.root)
        
        try:
            # Get a member ID from test data
            with session_scope() as session:
                member = session.query(Member).first()
                if member:
                    frame.filtrar_por_membro(member.id)
                    # Should not raise exception
        except Exception as e:
            self.fail(f"filtrar_por_membro failed: {str(e)}")

    def test_export_to_csv_creates_file(self):
        """Test exporting schedule to CSV creates a file."""
        frame = VisualizarFrame(self.root)
        
        # Set some test data
        frame.set_escala([
            {
                "data": "2026-03-15",
                "dia": "Domingo",
                "evento": "Evento A",
                "horario": "10:00",
                "squad": "Squad A",
                "membro": "João Silva",
            },
            {
                "data": "2026-03-20",
                "dia": "Sexta",
                "evento": "Evento B",
                "horario": "18:30",
                "squad": "Squad B",
                "membro": "Maria Santos",
            },
        ])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = os.path.join(tmpdir, "test_export.csv")
            
            # Mock the file dialog to return our temp file
            with patch('tkinter.filedialog.asksaveasfilename', return_value=csv_file):
                frame.exportar_csv()
                
                # Verify file was created
                self.assertTrue(os.path.exists(csv_file), "CSV file was not created")
                
                # Verify file has content
                with open(csv_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.assertIn("Data", content)
                    self.assertIn("João Silva", content)

    def test_export_to_txt_creates_file(self):
        """Test exporting schedule to TXT creates a file."""
        frame = VisualizarFrame(self.root)
        
        # Set some test data
        frame.set_escala([
            {
                "data": "2026-03-15",
                "dia": "Domingo",
                "evento": "Evento A",
                "horario": "10:00",
                "squad": "Squad A",
                "membro": "João Silva",
            },
        ])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = os.path.join(tmpdir, "test_export.txt")
            
            # Mock the file dialog to return our temp file
            with patch('tkinter.filedialog.asksaveasfilename', return_value=txt_file):
                frame.exportar_txt()
                
                # Verify file was created
                self.assertTrue(os.path.exists(txt_file), "TXT file was not created")
                
                # Verify file has content
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.assertIn("ESCALA", content)
                    self.assertIn("João Silva", content)

    def test_set_escala_updates_treeview(self):
        """Test that set_escala updates treeview with schedule data."""
        frame = VisualizarFrame(self.root)
        
        test_data = [
            {
                "data": "2026-03-15",
                "dia": "Domingo",
                "evento": "Evento Teste",
                "horario": "10:00",
                "squad": "Squad Teste",
                "membro": "Voluntário Teste",
            }
        ]
        
        frame.set_escala(test_data)
        
        # Verify data was stored
        self.assertEqual(len(frame.escala_atual), 1)
        self.assertEqual(frame.escala_atual[0]["evento"], "Evento Teste")
        
        # Verify treeview was updated
        tree_items = frame.tree.get_children()
        self.assertEqual(len(tree_items), 1)

    def test_limpar_clears_treeview(self):
        """Test that limpar() clears the schedule data."""
        frame = VisualizarFrame(self.root)
        
        # Add some data
        frame.set_escala([
            {
                "data": "2026-03-15",
                "dia": "Domingo",
                "evento": "Evento",
                "horario": "10:00",
                "squad": "Squad",
                "membro": "Voluntário",
            }
        ])
        
        self.assertGreater(len(frame.escala_atual), 0)
        
        # Clear
        with patch('tkinter.messagebox.showinfo'):
            frame.limpar()
        
        # Verify cleared
        self.assertEqual(len(frame.escala_atual), 0)
        self.assertEqual(len(frame.tree.get_children()), 0)


if __name__ == "__main__":
    unittest.main()
