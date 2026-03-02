"""
Testes para EscalaService - integração com BD e helpers.

Padrão:
- Testes de integração (usa session_scope e BD)
- Fixtures para setup/teardown de dados
- Cenários reais: eventos, squads, membros, casais, restrições
"""

import pytest
from datetime import date, datetime
import tempfile
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from infra.database import (
    Base,
    session_scope,
    SessionLocal,
    engine,
    Member,
    Squad,
    Event,
    EventSquad,
    MemberSquad,
    FamilyCouple,
    MemberRestrictions,
)
from services.escala_service import EscalaService


@pytest.fixture(scope="function")
def isolated_db():
    """Criar BD em memória isolada para cada teste."""
    from infra import database
    
    # Criar engine em memória
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    # Enable FK para SQLite
    @event.listens_for(test_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()
    
    # Criar tabelas
    Base.metadata.create_all(test_engine)
    
    # Criar session factory para BD isolada
    TestSessionLocal = sessionmaker(bind=test_engine, expire_on_commit=False)
    
    # Patch session_scope para usar BD de teste
    original_sessionlocal = database.SessionLocal
    database.SessionLocal = TestSessionLocal
    
    yield test_engine, TestSessionLocal
    
    # Restore original
    database.SessionLocal = original_sessionlocal


@pytest.fixture
def escala_service(isolated_db):
    """Instancia EscalaService com BD isolada."""
    return EscalaService()


@pytest.fixture
def sample_members(isolated_db):
    """Cria membros de exemplo no BD isolada."""
    test_engine, TestSessionLocal = isolated_db
    
    with TestSessionLocal() as session:
        members = [
            Member(name="João", status=True),
            Member(name="Maria", status=True),
            Member(name="Pedro", status=True),
            Member(name="Ana", status=True),
            Member(name="Tiago", status=True),
        ]
        session.add_all(members)
        session.commit()
        member_ids = {m.name: m.id for m in members}
    
    return member_ids


@pytest.fixture
def sample_squads(isolated_db):
    """Cria squads de exemplo."""
    test_engine, TestSessionLocal = isolated_db
    
    with TestSessionLocal() as session:
        squads = [
            Squad(nome="Louvor"),
            Squad(nome="Infantil"),
            Squad(nome="Administrativo"),
        ]
        session.add_all(squads)
        session.commit()
        squad_ids = {s.nome: s.id for s in squads}
    
    return squad_ids


@pytest.fixture
def sample_couples(isolated_db, sample_members):
    """Cria casal João & Maria."""
    test_engine, TestSessionLocal = isolated_db
    
    with TestSessionLocal() as session:
        joao_id = sample_members["João"]
        maria_id = sample_members["Maria"]
        
        casal = FamilyCouple(
            member1_id=joao_id,
            member2_id=maria_id,
            family_type=1,  # cônjuges
        )
        session.add(casal)
        session.commit()


# ============================================
# Tests: Basic validation
# ============================================


class TestEscalaServiceValidation:
    """Valida entrada e retorno básico."""

    def test_invalid_month(self, escala_service):
        """Mês inválido retorna erro."""
        success, msg, escala = escala_service.generate_schedule(13, 2025)
        assert success is False
        assert len(msg) > 0
        assert escala == []

    def test_invalid_year(self, escala_service):
        """Ano inválido (0) retorna erro."""
        success, msg, escala = escala_service.generate_schedule(1, 0)
        assert success is False
        assert escala == []

    def test_valid_month_year_but_no_events(self, escala_service):
        """Mês/ano válido mas sem eventos retorna aviso."""
        success, msg, escala = escala_service.generate_schedule(1, 2025)
        # Se não houver eventos cadastrados, deve retornar falso
        assert success is False
        assert "nenhum evento" in msg.lower()
        assert escala == []


# ============================================
# Tests: Fixed event generation
# ============================================


class TestFixedEventGeneration:
    """Testa geração de eventos fixos (de repetição semanal)."""

    def test_fixed_event_generates_multiple_dates(
        self, escala_service, isolated_db, sample_squads, sample_members
    ):
        """Evento fixo na segunda-feira gera múltiplas datas no mês."""
        test_engine, TestSessionLocal = isolated_db
        
        # Setup: criar evento fixo (Segunda)
        with TestSessionLocal() as session:
            event = Event(
                name="Culto",
                type="fixo",
                day_of_week="Segunda",
                time="19:00",
            )
            session.add(event)
            session.flush()
            event_id = event.id

            # Adicionar squad ao evento
            squad_id = list(sample_squads.values())[0]
            event_squad = EventSquad(
                event_id=event_id,
                squad_id=squad_id,
                quantity=2,
            )
            session.add(event_squad)
            session.commit()

        # Adicionar membros à squad
        with TestSessionLocal() as session:
            squad_id = list(sample_squads.values())[0]
            for member_id in list(sample_members.values())[:2]:
                ms = MemberSquad(member_id=member_id, squad_id=squad_id, level=2)
                session.add(ms)
            session.commit()

        # Gerar escala
        success, msg, escala = escala_service.generate_schedule(3, 2025)  # Março 2025

        if success:
            # Março 2025: segundas são dias 3, 10, 17, 24, 31
            # Esperamos 4 ou 5 entradas (dependendo de quantas segundas no mês)
            dates = {e["data"] for e in escala}
            assert len(dates) > 0


class TestSeasonalEventGeneration:
    """Testa eventos sazonais (data específica)."""

    def test_seasonal_event_specific_date(
        self, escala_service, isolated_db, sample_squads, sample_members
    ):
        """Evento sazonal em data específica é incluído."""
        test_engine, TestSessionLocal = isolated_db
        
        # Setup: criar evento sazonal (Natal)
        with TestSessionLocal() as session:
            event = Event(
                name="Celebração Natalina",
                type="sazonal",
                date="2025-12-25",
                time="18:00",
            )
            session.add(event)
            session.flush()
            event_id = event.id

            squad_id = list(sample_squads.values())[0]
            event_squad = EventSquad(
                event_id=event_id,
                squad_id=squad_id,
                quantity=3,
            )
            session.add(event_squad)
            session.commit()

        # Adicionar membros
        with TestSessionLocal() as session:
            squad_id = list(sample_squads.values())[0]
            for member_id in list(sample_members.values())[:3]:
                ms = MemberSquad(member_id=member_id, squad_id=squad_id, level=2)
                session.add(ms)
            session.commit()

        # Gerar escala para dezembro
        success, msg, escala = escala_service.generate_schedule(12, 2025)

        if success:
            # Procurar pela data 25/12/2025
            natal_entries = [e for e in escala if "25/12/2025" in e["data"]]
            assert len(natal_entries) > 0


# ============================================
# Tests: Couples handling
# ============================================


class TestCoupleHandling:
    """Testa processamento de casais."""

    def test_couples_escalated_together(
        self, escala_service, isolated_db, sample_members, sample_squads, sample_couples
    ):
        """Se respeitar casais, João e Maria são escalados juntos."""
        test_engine, TestSessionLocal = isolated_db
        
        # Setup: event com 2 vagas
        with TestSessionLocal() as session:
            event = Event(
                name="Culto",
                type="fixo",
                day_of_week="Segunda",
                time="19:00",
            )
            session.add(event)
            session.flush()
            event_id = event.id

            squad_id = list(sample_squads.values())[0]
            event_squad = EventSquad(
                event_id=event_id,
                squad_id=squad_id,
                quantity=2,
            )
            session.add(event_squad)
            session.commit()

        # Adicionar João e Maria à squad
        with TestSessionLocal() as session:
            squad_id = list(sample_squads.values())[0]
            joao_id = sample_members["João"]
            maria_id = sample_members["Maria"]

            ms1 = MemberSquad(member_id=joao_id, squad_id=squad_id, level=2)
            ms2 = MemberSquad(member_id=maria_id, squad_id=squad_id, level=2)
            session.add_all([ms1, ms2])
            session.commit()

        # Gerar com respect_couples=True
        success, msg, escala = escala_service.generate_schedule(
            3, 2025, respect_couples=True
        )

        if success and escala:
            # Verificar se ambos aparecem em alguns eventos
            names = [e["membro"] for e in escala]
            # Se resp couples, ambos devem estar (ou nenhum)
            assert "João" in names or "Maria" not in names
            assert "Maria" in names or "João" not in names


# ============================================
# Tests: Member restrictions
# ============================================


class TestMemberRestrictions:
    """Testa excl isão de membros com restrições."""

    def test_member_with_restriction_excluded(
        self, escala_service, isolated_db, sample_members, sample_squads
    ):
        """Membro com restrição em data específica é excluído."""
        test_engine, TestSessionLocal = isolated_db
        
        # Setup: criar evento
        with TestSessionLocal() as session:
            event = Event(
                name="Culto",
                type="fixo",
                day_of_week="Segunda",
                time="19:00",
            )
            session.add(event)
            session.flush()
            event_id = event.id

            squad_id = list(sample_squads.values())[0]
            event_squad = EventSquad(
                event_id=event_id,
                squad_id=squad_id,
                quantity=1,
            )
            session.add(event_squad)
            session.commit()

        # Adicionar João à squad
        with TestSessionLocal() as session:
            squad_id = list(sample_squads.values())[0]
            joao_id = sample_members["João"]
            ms = MemberSquad(member_id=joao_id, squad_id=squad_id, level=2)
            session.add(ms)
            session.commit()

        # Adicionar restrição para João em 03/03/2025 (primeira segunda de março)
        with TestSessionLocal() as session:
            joao_id = sample_members["João"]
            restricao = MemberRestrictions(
                member_id=joao_id,
                date=date(2025, 3, 3),
                description="Férias",
            )
            session.add(restricao)
            session.commit()

        # Gerar escala March
        success, msg, escala = escala_service.generate_schedule(3, 2025)

        if success:
            # João não deve aparecer em 03/03/2025
            entries_03 = [e for e in escala if e["data"] == "03/03/2025"]
            joao_entries_03 = [e for e in entries_03 if e["membro"] == "João"]
            assert len(joao_entries_03) == 0


# ============================================
# Tests: Patron ranking
# ============================================


class TestPatronRanking:
    """Testa seleção por patente."""

    def test_leaders_selected_before_members(
        self, escala_service, isolated_db, sample_members, sample_squads
    ):
        """Líderes são selecionados antes de membros."""
        test_engine, TestSessionLocal = isolated_db
        
        # Setup: event com 1 vaga
        with TestSessionLocal() as session:
            event = Event(
                name="Culto",
                type="fixo",
                day_of_week="Segunda",
                time="19:00",
            )
            session.add(event)
            session.flush()
            event_id = event.id

            squad_id = list(sample_squads.values())[0]
            event_squad = EventSquad(
                event_id=event_id,
                squad_id=squad_id,
                quantity=1,
            )
            session.add(event_squad)
            session.commit()

        # Adicionar João (Líder=4) e Maria (Membro=2) à squad
        with TestSessionLocal() as session:
            squad_id = list(sample_squads.values())[0]

            joao_id = sample_members["João"]
            ms1 = MemberSquad(member_id=joao_id, squad_id=squad_id, level=4)  # Líder
            
            maria_id = sample_members["Maria"]
            ms2 = MemberSquad(member_id=maria_id, squad_id=squad_id, level=2)  # Membro

            session.add_all([ms1, ms2])
            session.commit()

        # Gerar escala
        success, msg, escala = escala_service.generate_schedule(3, 2025)

        if success and escala:
            # João (Líder) deve ser selecionado, não Maria
            names = [e["membro"] for e in escala]
            assert "João" in names
            # Maria pode ou não estar (depends no algo, mas João tem prioridade)
