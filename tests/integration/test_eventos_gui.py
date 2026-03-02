"""
Testes de integração para gui/eventos_orm.py (GUI + Service + BD).

Validam que:
1. EventosFrame inicializa corretamente com EventosService
2. CRUD via GUI funciona: create, read, update, delete
3. Treeview é atualizado após operações
4. Mensagens de erro são tratadas corretamente
"""

import pytest
import tkinter as tk
from tkinter import messagebox
from unittest.mock import Mock, patch, MagicMock

from gui.eventos_orm import EventosFrame
from services.eventos_service import EventosService
from infra.database import Event, Squad, EventSquad, session_scope, create_tables


@pytest.fixture(scope="module")
def setup_db():
    """Setup banco de dados para testes."""
    create_tables()
    
    # Limpar dados anteriores
    with session_scope() as session:
        session.query(EventSquad).delete()
        session.query(Event).delete()
        session.query(Squad).delete()
        session.commit()
    
    # Criar squads padrão
    with session_scope() as session:
        squads = [
            Squad(id="squad-1", nome="Squad A"),
            Squad(id="squad-2", nome="Squad B"),
        ]
        session.add_all(squads)
        session.commit()
    
    yield
    
    # Cleanup após testes
    with session_scope() as session:
        session.query(EventSquad).delete()
        session.query(Event).delete()
        session.query(Squad).delete()
        session.commit()


@pytest.fixture
def root():
    """Cria janela Tkinter para testes."""
    root = tk.Tk()
    root.withdraw()  # Ocultar janela
    yield root
    root.destroy()


@pytest.fixture
def eventos_frame(root, setup_db):
    """Cria EventosFrame para testes."""
    frame = EventosFrame(root)
    frame.pack()
    yield frame
    # Cleanup
    try:
        frame.destroy()
    except tk.TclError:
        pass


class TestEventosFrameInitialization:
    """Testa inicialização do EventosFrame."""

    def test_eventos_frame_initializes(self, eventos_frame):
        """EventosFrame deve inicializar com EventosService."""
        assert hasattr(eventos_frame, 'service')
        assert isinstance(eventos_frame.service, EventosService)
        assert hasattr(eventos_frame, 'tree')
        assert hasattr(eventos_frame, 'atualizar_lista')


class TestCreateEvent:
    """Testa criação de eventos via GUI."""

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showinfo')
    def test_create_event_fixo(self, mock_showinfo, mock_dialog, eventos_frame):
        """Criar evento fixo (recorrente) via GUI."""
        # Mock o diálogo com resultado válido
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Culto", "fixo", "Domingo", "", "19:00", "Culto semanal")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Executar criar
        eventos_frame.adicionar()
        
        # Verificar showinfo foi chamado
        assert mock_showinfo.called
        
        # Verificar que evento foi criado no BD
        with session_scope() as session:
            event = session.query(Event).filter(Event.name == "Culto").first()
            assert event is not None
            assert event.type == "fixo"
            assert event.day_of_week == "Domingo"
            assert event.time == "19:00"

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showinfo')
    def test_create_event_sazonal(self, mock_showinfo, mock_dialog, eventos_frame):
        """Criar evento sazonal via GUI."""
        # Mock o diálogo com resultado válido
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Natal", "sazonal", "", "25/12/2024", "18:00", "Celebração de Natal")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Executar criar
        eventos_frame.adicionar()
        
        # Verificar showinfo foi chamado
        assert mock_showinfo.called
        
        # Verificar que evento foi criado no BD
        with session_scope() as session:
            event = session.query(Event).filter(Event.name == "Natal").first()
            assert event is not None
            assert event.type == "sazonal"
            assert event.date == "2024-12-25"  # Normalizado para ISO
            assert event.day_of_week is None

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showerror')
    def test_create_event_invalid_type(self, mock_showerror, mock_dialog, eventos_frame):
        """Criar evento com tipo inválido retorna erro."""
        # Mock o diálogo
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Teste", "tipo_invalido", "", "25/12/2024", "18:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Executar criar
        eventos_frame.adicionar()
        
        # Verificar que showerror foi chamado
        assert mock_showerror.called
        
        # Verificar que evento NÃO foi criado
        with session_scope() as session:
            event = session.query(Event).filter(Event.name == "Teste").first()
            assert event is None


class TestLoadEvents:
    """Testa carregamento de eventos na treeview."""

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showinfo')
    def test_eventos_carregam_na_treeview(self, mock_showinfo, mock_dialog, eventos_frame):
        """Após criar evento, deve aparecer na treeview."""
        # Limpar treeview
        for item in eventos_frame.tree.get_children():
            eventos_frame.tree.delete(item)
        
        # Criar evento
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Reunião", "fixo", "Segunda-feira", "", "20:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        eventos_frame.adicionar()
        
        # Verificar que evento aparece na treeview
        items = eventos_frame.tree.get_children()
        assert len(items) > 0
        
        # Verificar valores
        values = eventos_frame.tree.item(items[0])["values"]
        assert values[0] == "Reunião"  # Nome
        assert values[1] == "Fixo"     # Tipo capitalizado
        assert values[3] == "20:00"    # Horário


class TestDeleteEvent:
    """Testa deleção de eventos."""

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.messagebox.askyesno', return_value=True)
    def test_delete_event_via_gui(self, mock_askyesno, mock_showinfo, mock_dialog, eventos_frame):
        """Deletar evento via GUI."""
        # Criar evento primeiro
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Encontro", "fixo", "Sábado", "", "17:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        eventos_frame.adicionar()
        
        # Obter ID do evento criado
        items = eventos_frame.tree.get_children()
        event_id = items[0]
        
        # Selecionar evento
        eventos_frame.tree.selection_set(event_id)
        
        # Mock o showinfo para delete
        mock_showinfo.reset_mock()
        
        # Deletar
        eventos_frame.remover()
        
        # Verificar showinfo foi chamado
        assert mock_showinfo.called
        
        # Verificar que evento foi deletado do BD
        with session_scope() as session:
            event = session.query(Event).filter(Event.id == event_id).first()
            assert event is None


class TestErrorHandling:
    """Testa tratamento de erros."""

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showerror')
    def test_error_handling_invalid_type(self, mock_showerror, mock_dialog, eventos_frame):
        """Tipo de evento inválido deve mostrar erro."""
        # Mock o diálogo
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Evento", "invalido", "", "25/12/2024", "18:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Executar
        eventos_frame.adicionar()
        
        # Verificar erro foi mostrado
        assert mock_showerror.called
        call_args = mock_showerror.call_args
        assert "tipo" in str(call_args).lower() or "inválido" in str(call_args).lower()

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showerror')
    def test_error_handling_empty_name(self, mock_showerror, mock_dialog, eventos_frame):
        """Nome vazio deve retornar erro."""
        # Mock o diálogo
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("", "fixo", "Domingo", "", "19:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Executar
        eventos_frame.adicionar()
        
        # Verificar erro foi mostrado
        assert mock_showerror.called

    def test_error_handling_no_selection_on_delete(self, eventos_frame):
        """Deletar sem selecionar evento não deve fazer nada."""
        # Limpar seleção
        eventos_frame.tree.selection_remove(eventos_frame.tree.selection())
        
        # Deletar sem seleção
        eventos_frame.remover()
        
        # Não deve lançar exceção, apenas silenciosamente retornar


class TestUpdateEvent:
    """Testa atualização de eventos."""

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showinfo')
    def test_update_event_changes_name(self, mock_showinfo, mock_dialog, eventos_frame):
        """Editar evento deve atualizar no BD."""
        # Criar evento primeiro
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Original", "fixo", "Domingo", "", "19:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        eventos_frame.adicionar()
        
        # Obter ID
        items = eventos_frame.tree.get_children()
        event_id = items[0]
        
        # Selecionar para editar
        eventos_frame.tree.selection_set(event_id)
        
        # Mock novo diálogo para edição
        mock_dialog_instance2 = Mock()
        mock_dialog_instance2.result = ("Atualizado", "fixo", "Domingo", "", "19:00", "")
        mock_dialog_instance2.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance2
        
        mock_showinfo.reset_mock()
        
        # Editar
        eventos_frame.editar()
        
        # Verificar que foi atualizado
        with session_scope() as session:
            event = session.query(Event).filter(Event.id == event_id).first()
            assert event is not None
            assert event.name == "Atualizado"


class TestConfigureEventSquads:
    """Testa configuração de squads para eventos."""

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showinfo')
    def test_configure_event_squads_via_service(self, mock_showinfo, mock_dialog, eventos_frame):
        """Configurar squads de um evento via service."""
        # Criar evento primeiro
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Evento com Squads", "fixo", "Sexta-feira", "", "20:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        eventos_frame.adicionar()
        
        # Obter ID do evento criado
        with session_scope() as session:
            event = session.query(Event).filter(Event.name == "Evento com Squads").first()
            event_id = event.id
        
        # Configurar squads usando o service
        squad_quantities = {
            "squad-1": 2,
            "squad-2": 3,
        }
        
        success, message = eventos_frame.service.configure_event_squads(
            event_id=event_id,
            squad_quantities=squad_quantities
        )
        
        # Verificar sucesso
        assert success
        assert "sucesso" in message.lower()
        
        # Verificar que squads foram configuradas no BD
        with session_scope() as session:
            event_squads = session.query(EventSquad).filter(
                EventSquad.event_id == event_id
            ).all()
            
            assert len(event_squads) == 2
            
            squad_dict = {es.squad_id: es.quantity for es in event_squads}
            assert squad_dict["squad-1"] == 2
            assert squad_dict["squad-2"] == 3

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showinfo')
    def test_event_squads_created_on_event_create(self, mock_showinfo, mock_dialog, eventos_frame):
        """Ao criar evento, EventSquad deve ser criado com defaults para todas as squads."""
        # Criar evento
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Novo Evento", "fixo", "Terça-feira", "", "18:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        eventos_frame.adicionar()
        
        # Obter ID do evento
        with session_scope() as session:
            event = session.query(Event).filter(Event.name == "Novo Evento").first()
            event_id = event.id
            
            # Verificar que EventSquad foi criado para todas as squads
            event_squads = session.query(EventSquad).filter(
                EventSquad.event_id == event_id
            ).all()
            
            # Devem existir 2 squads (squad-1 e squad-2)
            assert len(event_squads) == 2
            
            # Ambas devem ter quantity=0 (default)
            for es in event_squads:
                assert es.quantity == 0
                assert es.level == 2


class TestEventoDialogValidation:
    """Testa validação de dados no EventoDialog e EventosService."""

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showerror')
    def test_invalid_date_sazonal(self, mock_showerror, mock_dialog, eventos_frame):
        """Data inválida para evento sazonal deve retornar erro."""
        # Mock o diálogo com data inválida
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Evento", "sazonal", "", "32/13/2024", "18:00", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Executar
        eventos_frame.adicionar()
        
        # Verificar erro foi mostrado
        assert mock_showerror.called
        
        # Verificar que evento NÃO foi criado
        with session_scope() as session:
            event = session.query(Event).filter(Event.name == "Evento").first()
            assert event is None

    @patch('gui.eventos_orm.EventoDialog')
    @patch('tkinter.messagebox.showerror')
    def test_invalid_time_format(self, mock_showerror, mock_dialog, eventos_frame):
        """Horário inválido deve retornar erro."""
        # Mock o diálogo
        mock_dialog_instance = Mock()
        mock_dialog_instance.result = ("Evento", "fixo", "Domingo", "", "25:99", "")
        mock_dialog_instance.dialog = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Executar
        eventos_frame.adicionar()
        
        # Verificar erro foi mostrado
        assert mock_showerror.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
