"""Configuração pytest com fixtures compartilhadas."""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao PYTHONPATH
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infra.database import Base, Member


@pytest.fixture(scope="function")
def test_db():
    """Criar BD SQLite em memória para testes."""
    # Criar engine em memória
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    
    # Criar tabelas
    Base.metadata.create_all(test_engine)
    
    # Criar session factory
    TestSessionLocal = sessionmaker(bind=test_engine)
    
    # Substituir session global
    import infra.database
    original_sessionmaker = infra.database.SessionLocal
    infra.database.SessionLocal = TestSessionLocal
    
    yield test_engine
    
    # Restaurar original
    infra.database.SessionLocal = original_sessionmaker
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def members_fixture(test_db):
    """Criar membros de teste na BD."""
    TestSessionLocal = sessionmaker(bind=test_db)
    session = TestSessionLocal()
    
    members_list = [
        Member(name="Alice"),
        Member(name="Bob"),
        Member(name="Charlie"),
        Member(name="Dave"),
        Member(name="Eve"),
        Member(name="Frank"),
    ]
    session.add_all(members_list)
    session.commit()
    
    # Retornar dict com IDs
    members_dict = {m.name: m.id for m in members_list}
    session.close()
    
    return members_dict
