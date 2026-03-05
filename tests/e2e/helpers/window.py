"""Helpers de verificação de estado para testes E2E.

Usa sqlite3 diretamente para verificar o estado do banco de dados
sem depender de screenshot ou OCR.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional


def _get_db_path() -> Optional[str]:
    """Retorna o caminho do banco de dados em uso (da env var DATABASE_URL)."""
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    # Fallback para o banco padrão
    project_root = Path(__file__).resolve().parents[4]
    return str(project_root / "escala.db")


def count_members(db_path: str) -> int:
    """Conta quantos membros estão no banco."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM members")
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except Exception:
        return -1


def count_squads(db_path: str) -> int:
    """Conta quantos squads/times estão no banco."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM squads")
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except Exception:
        return -1


def count_events(db_path: str) -> int:
    """Conta quantos eventos estão no banco."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM events")
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except Exception:
        return -1


def count_member_squads(db_path: str) -> int:
    """Conta associações membro-squad."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM members_squads")
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except Exception:
        return -1


def count_event_squads(db_path: str) -> int:
    """Conta configurações evento-squad (EventSquad)."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM events_squads")
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except Exception:
        return -1


def count_schedule_entries(db_path: str, month: int, year: int) -> int:
    """Conta entradas de escala geradas para o mês/ano."""
    try:
        conn = sqlite3.connect(db_path)
        # Tenta tabela 'schedules' (nome pode variar)
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM schedules WHERE strftime('%m', date) = ? "
                "AND strftime('%Y', date) = ?",
                (f"{month:02d}", str(year)),
            )
            result = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            result = 0
        conn.close()
        return result
    except Exception:
        return -1
