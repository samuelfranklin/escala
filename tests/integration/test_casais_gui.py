"""Testes de integração para CasaisFrame GUI.

Testa interação entre GUI (Tkinter), Service e BD.
"""

import tkinter as tk
from unittest.mock import patch, MagicMock
import uuid

import pytest

from gui.casais_orm import CasaisFrame
from services.casais_service import CasaisService
from infra.database import FamilyCouple, Member, create_tables, session_scope, Base, engine


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database before and after each test."""
    # Drop all tables
    Base.metadata.drop_all(engine)
    # Recreate tables
    create_tables()
    yield
    # Cleanup after test
    Base.metadata.drop_all(engine)


class TestCasaisFrameInitialization:
    """Testa inicialização e setup do frame."""

    def test_casais_frame_initializes(self):
        """Frame CasaisFrame cria sem erros."""
        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            assert frame is not None
            assert isinstance(frame, tk.Frame)
            assert hasattr(frame, 'service')
            assert isinstance(frame.service, CasaisService)
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_frame_has_required_widgets(self):
        """Frame possui widgets necessários."""
        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            # Verifica widgets principais
            assert hasattr(frame, 'tree')
            assert hasattr(frame, 'combo1')
            assert hasattr(frame, 'combo2')
            assert hasattr(frame, 'membros_dict')
        finally:
            try:
                root.destroy()
            except Exception:
                pass


class TestCasaisFrameCRUD:
    """Testa operações CRUD via GUI."""

    def test_create_couple_via_gui(self):
        """Testa criação de casal via GUI."""
        # Setup: criar membros na BD com UUIDs únicos
        m1_id = str(uuid.uuid4())
        m2_id = str(uuid.uuid4())
        
        with session_scope() as session:
            m1 = Member(id=m1_id, name="Alice", status=True)
            m2 = Member(id=m2_id, name="Bob", status=True)
            session.add(m1)
            session.add(m2)
            session.commit()

        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            
            # Simula seleção nos combos
            frame.combo1.set("Alice")
            frame.combo2.set("Bob")
            
            # Simula clique em cadastrar
            frame.cadastrar()
            
            # Verifica se casal foi criado
            casais = frame.service.get_all_couples()
            assert len(casais) == 1
            assert casais[0].member1_id == m1_id
            assert casais[0].member2_id == m2_id
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_refresh_populates_treeview(self):
        """Testa se refresh_data carrega casais na treeview."""
        # Setup: criar membros e casal com UUIDs únicos
        m1_id = str(uuid.uuid4())
        m2_id = str(uuid.uuid4())
        
        with session_scope() as session:
            m1 = Member(id=m1_id, name="Charlie", status=True)
            m2 = Member(id=m2_id, name="Diana", status=True)
            session.add(m1)
            session.add(m2)
            session.commit()

        service = CasaisService()
        service.create_couple(m1_id, m2_id)

        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            
            # Verifica que treeview tem dados
            items = frame.tree.get_children()
            assert len(items) > 0
            
            # Verifica conteúdo do item
            item = frame.tree.item(items[0])
            nome1, nome2 = item["values"]
            assert nome1 in ["Charlie", "Diana"]
            assert nome2 in ["Charlie", "Diana"]
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_delete_couple_via_gui(self):
        """Testa deleção de casal via GUI."""
        # Setup: criar membros e casal com UUIDs únicos
        m1_id = str(uuid.uuid4())
        m2_id = str(uuid.uuid4())
        
        with session_scope() as session:
            m1 = Member(id=m1_id, name="Eve", status=True)
            m2 = Member(id=m2_id, name="Frank", status=True)
            session.add(m1)
            session.add(m2)
            session.commit()

        service = CasaisService()
        couple = service.create_couple(m1_id, m2_id)
        couple_id = couple.id

        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            
            # Força seleção do casal
            items = frame.tree.get_children()
            if items:
                frame.tree.selection_set(items[0])
                
                # Simula clique em remover
                with patch('tkinter.messagebox.askyesno', return_value=True):
                    frame.remover()
                
                # Verifica se casal foi deletado
                casais_depois = frame.service.get_all_couples()
                assert len(casais_depois) == 0
        finally:
            try:
                root.destroy()
            except Exception:
                pass


class TestCasaisFrameErrorHandling:
    """Testa tratamento de erros no GUI."""

    def test_error_different_spouses(self):
        """Testa erro quando cônjuges são iguais."""
        m1_id = str(uuid.uuid4())
        
        with session_scope() as session:
            m1 = Member(id=m1_id, name="Grace", status=True)
            session.add(m1)
            session.commit()

        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            frame.combo1.set("Grace")
            frame.combo2.set("Grace")
            
            # Deve mostrar aviso
            with patch('tkinter.messagebox.showwarning') as mock_warn:
                frame.cadastrar()
                mock_warn.assert_called()
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_error_duplicate_couple(self):
        """Testa erro ao tentar criar casal duplicado."""
        m1_id = str(uuid.uuid4())
        m2_id = str(uuid.uuid4())
        
        with session_scope() as session:
            m1 = Member(id=m1_id, name="Henry", status=True)
            m2 = Member(id=m2_id, name="Iris", status=True)
            session.add(m1)
            session.add(m2)
            session.commit()

        service = CasaisService()
        service.create_couple(m1_id, m2_id)

        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            frame.combo1.set("Henry")
            frame.combo2.set("Iris")
            
            # Deve mostrar erro (ValueError)
            with patch('tkinter.messagebox.showerror') as mock_error:
                frame.cadastrar()
                mock_error.assert_called()
                # Verifica se mensagem contém "já existe"
                call_args = mock_error.call_args
                assert "já existe" in str(call_args).lower() or "existe" in str(call_args).lower()
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_error_missing_selection(self):
        """Testa erro ao tentar deletar sem seleção."""
        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            
            # Tenta deletar sem seleção
            with patch('tkinter.messagebox.showwarning') as mock_warn:
                frame.remover()
                mock_warn.assert_called()
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_error_no_empty_fields(self):
        """Testa erro ao tentar cadastrar com campos vazios."""
        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            frame.combo1.set("")
            frame.combo2.set("")
            
            # Deve mostrar aviso
            with patch('tkinter.messagebox.showwarning') as mock_warn:
                frame.cadastrar()
                mock_warn.assert_called()
        finally:
            try:
                root.destroy()
            except Exception:
                pass


class TestCasaisFrameCallbacks:
    """Testa callbacks e sincronização."""

    def test_atualizar_lista_callback(self):
        """Testa callback atualizar_lista (sincronização)."""
        # Setup: criar casal
        m1_id = str(uuid.uuid4())
        m2_id = str(uuid.uuid4())
        
        with session_scope() as session:
            m1 = Member(id=m1_id, name="Jack", status=True)
            m2 = Member(id=m2_id, name="Karen", status=True)
            session.add(m1)
            session.add(m2)
            session.commit()

        service = CasaisService()
        service.create_couple(m1_id, m2_id)

        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            
            # Chama callback
            frame.atualizar_lista()
            
            # Verifica que treeview foi atualizado
            items = frame.tree.get_children()
            assert len(items) > 0
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_refresh_data_updates_combos(self):
        """Testa se refresh_data atualiza comboboxes com membros."""
        m1_id = str(uuid.uuid4())
        m2_id = str(uuid.uuid4())
        
        with session_scope() as session:
            m1 = Member(id=m1_id, name="Leo", status=True)
            m2 = Member(id=m2_id, name="Mia", status=True)
            session.add(m1)
            session.add(m2)
            session.commit()

        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            
            # Verifica que combos foram populados
            combo_values = frame.combo1['values']
            assert "Leo" in combo_values
            assert "Mia" in combo_values
        finally:
            try:
                root.destroy()
            except Exception:
                pass


class TestCasaisFrameIntegration:
    """Testa integração completa: GUI + Service + BD."""

    def test_full_workflow(self):
        """Testa workflow completo: criar, listar, deletar."""
        # Setup: criar membros
        m1_id = str(uuid.uuid4())
        m2_id = str(uuid.uuid4())
        
        with session_scope() as session:
            m1 = Member(id=m1_id, name="Noah", status=True)
            m2 = Member(id=m2_id, name="Olivia", status=True)
            session.add(m1)
            session.add(m2)
            session.commit()

        root = tk.Tk()
        try:
            frame = CasaisFrame(root)
            
            # 1. Criar casal
            frame.combo1.set("Noah")
            frame.combo2.set("Olivia")
            with patch('tkinter.messagebox.showinfo'):
                frame.cadastrar()
            
            # Verifica criação
            casais = frame.service.get_all_couples()
            assert len(casais) == 1
            couple_id = casais[0].id
            
            # 2. Verificar treeview
            items = frame.tree.get_children()
            assert len(items) == 1
            
            # 3. Deletar casal
            frame.tree.selection_set(items[0])
            with patch('tkinter.messagebox.askyesno', return_value=True):
                with patch('tkinter.messagebox.showinfo'):
                    frame.remover()
            
            # Verifica deleção
            casais_depois = frame.service.get_all_couples()
            assert len(casais_depois) == 0
        finally:
            try:
                root.destroy()
            except Exception:
                pass
