"""
Testes para services/eventos_service.py (integração com BD).

Testes de integração validam que os helpers+service+BD funcionam juntos.
"""

import unittest
from infra.database import Event, Squad, EventSquad, session_scope, create_tables
from services.eventos_service import EventosService


class TestEventosService(unittest.TestCase):
    """Testa EventosService com banco de dados."""

    @classmethod
    def setUpClass(cls):
        """Cria tabelas antes de rodar testes."""
        create_tables()

    def setUp(self):
        """Setup antes de cada teste."""
        self.service = EventosService()
        
        # Limpar dados de teste anteriores
        with session_scope() as session:
            session.query(EventSquad).delete()
            session.query(Event).delete()
            session.query(Squad).delete()
            session.commit()
        
        # Criar squads de teste
        with session_scope() as session:
            squad1 = Squad(id="squad-1", nome="Squad A")
            squad2 = Squad(id="squad-2", nome="Squad B")
            session.add(squad1)
            session.add(squad2)
            session.commit()

    def test_criar_evento_fixo_com_sucesso(self):
        """Criar evento fixo retorna sucesso."""
        success, msg, event = self.service.create_event(
            name="Culto Domingo",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(event)
        self.assertEqual(event.name, "Culto Domingo")
        self.assertEqual(event.type, "fixo")
        self.assertEqual(event.time, "19:00")
        self.assertEqual(event.day_of_week, "Domingo")

    def test_criar_evento_sazonal_com_sucesso(self):
        """Criar evento sazonal retorna sucesso."""
        success, msg, event = self.service.create_event(
            name="Natal",
            event_type="sazonal",
            time="18:00",
            date="25/12/2024",
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(event)
        self.assertEqual(event.name, "Natal")
        self.assertEqual(event.type, "sazonal")
        self.assertEqual(event.date, "2024-12-25")  # Normalizado para ISO
        self.assertIsNone(event.day_of_week)

    def test_criar_evento_sem_nome_falha(self):
        """Criar evento sem nome retorna erro."""
        success, msg, event = self.service.create_event(
            name="",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        
        self.assertFalse(success)
        self.assertIsNone(event)
        self.assertIn("vazio", msg.lower())

    def test_criar_evento_com_nome_duplicado_falha(self):
        """Criar evento com nome duplicado retorna erro."""
        # Criar primeiro evento
        self.service.create_event(
            name="Culto Domingo",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        
        # Tentar criar com mesmo nome
        success, msg, event = self.service.create_event(
            name="Culto Domingo",
            event_type="fixo",
            time="20:00",
            day_of_week="Domingo",
        )
        
        self.assertFalse(success)
        self.assertIsNone(event)
        self.assertIn("já existe", msg.lower())

    def test_criar_evento_fixo_sem_dia_semana_falha(self):
        """Criar evento fixo sem dia da semana falha."""
        success, msg, event = self.service.create_event(
            name="Culto",
            event_type="fixo",
            time="19:00",
        )
        
        self.assertFalse(success)
        self.assertIsNone(event)
        self.assertIn("obrigatório", msg.lower())

    def test_criar_evento_sazonal_sem_data_falha(self):
        """Criar evento sazonal sem data falha."""
        success, msg, event = self.service.create_event(
            name="Evento",
            event_type="sazonal",
            time="19:00",
        )
        
        self.assertFalse(success)
        self.assertIsNone(event)
        self.assertIn("obrigatória", msg.lower())

    def test_criar_evento_com_squads_customizadas(self):
        """Criar evento com configuração customizada de squads."""
        success, msg, event = self.service.create_event(
            name="Evento com Squads",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
            squad_quantities={"squad-1": 3, "squad-2": 5},
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(event)
        
        # Verificar que EventSquad foi criado
        with session_scope() as session:
            configs = session.query(EventSquad).filter(
                EventSquad.event_id == event.id
            ).all()
            self.assertEqual(len(configs), 2)

    def test_atualizar_evento_nome(self):
        """Atualizar nome do evento."""
        # Criar primeiro
        success, msg, event = self.service.create_event(
            name="Culto Original",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        event_id = event.id
        
        # Atualizar
        success, msg, updated = self.service.update_event(
            event_id=event_id,
            name="Culto Atualizado",
        )
        
        self.assertTrue(success)
        self.assertEqual(updated.name, "Culto Atualizado")
        
        # Verificar no banco
        with session_scope() as session:
            fetched = session.query(Event).filter(Event.id == event_id).first()
            self.assertEqual(fetched.name, "Culto Atualizado")

    def test_atualizar_evento_horario(self):
        """Atualizar horário do evento."""
        success, msg, event = self.service.create_event(
            name="Culto",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        
        success, msg, updated = self.service.update_event(
            event_id=event.id,
            time="20:30",
        )
        
        self.assertTrue(success)
        self.assertEqual(updated.time, "20:30")

    def test_atualizar_evento_inexistente_falha(self):
        """Atualizar evento inexistente retorna erro."""
        success, msg, event = self.service.update_event(
            event_id="nonexistent",
            name="Novo Nome",
        )
        
        self.assertFalse(success)
        self.assertIsNone(event)
        self.assertIn("não encontrado", msg.lower())

    def test_deletar_evento_com_sucesso(self):
        """Deletar evento com sucesso."""
        success, msg, event = self.service.create_event(
            name="Evento Temporário",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        event_id = event.id
        
        success, msg = self.service.delete_event(event_id)
        
        self.assertTrue(success)
        self.assertIn("deletado", msg.lower())
        
        # Verificar que foi deletado
        with session_scope() as session:
            fetched = session.query(Event).filter(Event.id == event_id).first()
            self.assertIsNone(fetched)

    def test_deletar_evento_inexistente_falha(self):
        """Deletar evento inexistente retorna erro."""
        success, msg = self.service.delete_event("nonexistent")
        
        self.assertFalse(success)
        self.assertIn("não encontrado", msg.lower())

    def test_get_event_by_id(self):
        """Buscar evento por ID."""
        success, msg, event = self.service.create_event(
            name="Teste",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        
        fetched = self.service.get_event_by_id(event.id)
        
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Teste")

    def test_get_event_by_id_inexistente(self):
        """Buscar evento inexistente retorna None."""
        fetched = self.service.get_event_by_id("nonexistent")
        self.assertIsNone(fetched)

    def test_list_all_events_ordenado_por_nome(self):
        """Listar eventos retorna ordenado por nome."""
        self.service.create_event(
            name="Zebra",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        self.service.create_event(
            name="Alpha",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        
        events = self.service.list_all_events()
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].name, "Alpha")
        self.assertEqual(events[1].name, "Zebra")

    def test_configure_event_squads(self):
        """Configurar squads do evento."""
        success, msg, event = self.service.create_event(
            name="Evento",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        
        success, msg = self.service.configure_event_squads(
            event_id=event.id,
            squad_quantities={"squad-1": 10, "squad-2": 5},
        )
        
        self.assertTrue(success)
        
        # Verificar
        with session_scope() as session:
            configs = session.query(EventSquad).filter(
                EventSquad.event_id == event.id
            ).all()
            self.assertEqual(len(configs), 2)
            for config in configs:
                if config.squad_id == "squad-1":
                    self.assertEqual(config.quantity, 10)
                else:
                    self.assertEqual(config.quantity, 5)

    def test_normalizar_entrada_nome(self):
        """Nome com espaços extras é normalizado."""
        success, msg, event = self.service.create_event(
            name="  Culto Domingo  ",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
        )
        
        self.assertTrue(success)
        self.assertEqual(event.name, "Culto Domingo")  # Sem espaços extras

    def test_normalizar_horario(self):
        """Horário sem zero padding é normalizado."""
        success, msg, event = self.service.create_event(
            name="Evento",
            event_type="fixo",
            time="9:5",
            day_of_week="Domingo",
        )
        
        self.assertTrue(success)
        self.assertEqual(event.time, "09:05")

    def test_normalizar_data_para_iso(self):
        """Data DD/MM/YYYY é convertida para ISO."""
        success, msg, event = self.service.create_event(
            name="Natal",
            event_type="sazonal",
            time="18:00",
            date="25/12/2024",
        )
        
        self.assertTrue(success)
        self.assertEqual(event.date, "2024-12-25")


class TestEventosServiceIntegration(unittest.TestCase):
    """Testes de integração mais complexos."""

    @classmethod
    def setUpClass(cls):
        """Cria tabelas."""
        create_tables()

    def setUp(self):
        """Setup."""
        self.service = EventosService()
        with session_scope() as session:
            session.query(EventSquad).delete()
            session.query(Event).delete()
            session.query(Squad).delete()
            session.commit()

    def test_cascata_deleta_event_squads(self):
        """Deletar evento remove automaticamente EventSquads (cascata)."""
        # Criar squad
        with session_scope() as session:
            squad = Squad(id="squad-1", nome="Squad A")
            session.add(squad)
            session.commit()
        
        # Criar evento com squad
        success, msg, event = self.service.create_event(
            name="Evento",
            event_type="fixo",
            time="19:00",
            day_of_week="Domingo",
            squad_quantities={"squad-1": 5},
        )
        event_id = event.id
        
        # Verificar EventSquad existe
        with session_scope() as session:
            config = session.query(EventSquad).filter(
                EventSquad.event_id == event_id
            ).first()
            self.assertIsNotNone(config)
        
        # Deletar evento
        self.service.delete_event(event_id)
        
        # EventSquad deve ter sido deletado (cascata)
        with session_scope() as session:
            config = session.query(EventSquad).filter(
                EventSquad.event_id == event_id
            ).first()
            self.assertIsNone(config)


if __name__ == "__main__":
    unittest.main()
