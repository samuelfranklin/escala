import os as _os
import uuid
from ast import BoolOp
from contextlib import contextmanager
from pathlib import Path as _Path
from typing import Generator, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=gen_uuid, nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # e.g., "fixo", "sazonal", "eventual"
    date = Column(String(20), nullable=True)  # e.g., "2024-12-25"
    day_of_week = Column(String(20), nullable=True)  # e.g., "Segunda-feira"
    time = Column(String(20), nullable=True)  # e.g., "19:00"
    details = Column(String(255), nullable=True)
    settings = relationship(
        "EventSquad", back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id!r} nome={self.name!r}>"


class Squad(Base):
    __tablename__ = "squads"

    id = Column(String(36), primary_key=True, default=gen_uuid, nullable=False)
    nome = Column(String(100), unique=True, nullable=False)

    memberships = relationship(
        "MemberSquad", back_populates="squad", cascade="all, delete-orphan"
    )
    event_settings = relationship(
        "EventSquad", back_populates="squad", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Squad id={self.id!r} nome={self.nome!r}>"


class Member(Base):
    __tablename__ = "members"

    id = Column(String(36), primary_key=True, default=gen_uuid, nullable=False)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    instagram = Column(String(100), nullable=True)
    status = Column(
        Boolean, nullable=False, default=True
    )  # True = ativo, False = inativo

    memberships = relationship(
        "MemberSquad", back_populates="member", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Member id={self.id!r} name={self.name!r}>"


class EventSquad(Base):
    __tablename__ = "events_squads"

    event_id = Column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    squad_id = Column(
        String(36),
        ForeignKey("squads.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    level = Column(Integer, nullable=True, default=3)  # e.g., "Soldado", "Sargento"
    quantity = Column(Integer, nullable=False, default=0)

    event = relationship("Event", back_populates="settings")
    squad = relationship("Squad", back_populates="event_settings")

    __table_args__ = (
        Index("ix_event_settings_event_id", "event_id"),
        Index("ix_event_settings_squad_id", "squad_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<EventSquad event_id={self.event_id!r} "
            f"squad_id={self.squad_id!r} level={self.level!r}>"
        )


class MemberSquad(Base):
    """Association table between Member and Squad (M:N).

    Uses a composite primary key (member_id, squad_id) to naturally
    prevent duplicate associations without needing a separate unique
    constraint or a surrogate id column.
    """

    __tablename__ = "members_squads"

    member_id = Column(
        String(36),
        ForeignKey("members.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    squad_id = Column(
        String(36),
        ForeignKey("squads.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    level = Column(Integer, nullable=False, default=1)

    member = relationship("Member", back_populates="memberships")
    squad = relationship("Squad", back_populates="memberships")

    __table_args__ = (
        Index("ix_members_squads_member_id", "member_id"),
        Index("ix_members_squads_squad_id", "squad_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<MemberSquad member_id={self.member_id!r} "
            f"squad_id={self.squad_id!r} level={self.level!r}>"
        )


class MemberRestrictions(Base):
    __tablename__ = "members_restrictions"

    id = Column(String(36), primary_key=True, default=gen_uuid, nullable=False)
    member_id = Column(
        String(36),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )

    date = Column(Date, nullable=False)  # Data da restrição
    description = Column(String(255), nullable=True)  # e.g., "Férias", "Licença médica"

    def __repr__(self) -> str:
        return (
            f"<MemberRestrictions member_id={self.member_id!r} "
            f"date={self.date!r} description={self.description!r}>"
        )


class FamilyCouple(Base):
    __tablename__ = "family_couples"

    id = Column(String(36), primary_key=True, default=gen_uuid, nullable=False)
    member1_id = Column(
        String(36),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )
    member2_id = Column(
        String(36),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_type = Column(
        Integer, nullable=False, default=0
    )  # e.g., 0 = none, 1 = cônjuges, 2 = pais, 3 = filho, 4 = irmão etc.

    member1 = relationship("Member", foreign_keys=[member1_id])
    member2 = relationship("Member", foreign_keys=[member2_id])

    __table_args__ = (
        UniqueConstraint("member1_id", "member2_id", name="uq_family_couple"),
    )

    def __repr__(self) -> str:
        return (
            f"<FamilyCouple member1_id={self.member1_id!r} "
            f"member2_id={self.member2_id!r} family_type={self.family_type!r}>"
        )


# ---------- Database URL resolution ----------

_DATABASE_URL = _os.getenv("DATABASE_URL")

if _DATABASE_URL:
    DATABASE_URL = _DATABASE_URL
else:

    def _find_env_file(names: tuple = (".ENV", ".env")) -> Optional[_Path]:
        current = _Path(__file__).resolve().parent
        for directory in [current] + list(current.parents):
            for name in names:
                candidate = directory / name
                if candidate.exists():
                    return candidate
        return None

    _env_path = _find_env_file()
    DATABASE_URL = None

    if _env_path:
        try:
            with _env_path.open("r", encoding="utf-8") as _f:
                for _line in _f:
                    _line = _line.strip()
                    if not _line or _line.startswith("#"):
                        continue
                    if "=" not in _line:
                        continue
                    _key, _val = _line.split("=", 1)
                    if _key.strip() == "DATABASE_URL":
                        _val = _val.strip()
                        if (_val.startswith('"') and _val.endswith('"')) or (
                            _val.startswith("'") and _val.endswith("'")
                        ):
                            _val = _val[1:-1]
                        DATABASE_URL = _val
                        break
        except Exception:
            DATABASE_URL = None

    if not DATABASE_URL:
        DATABASE_URL = "sqlite:///escala.db"


# ---------- Engine ----------

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)

# Enable FK enforcement for every SQLite connection.
# This is necessary for ON DELETE CASCADE to work in SQLite.
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


# ---------- Session ----------

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope() -> Generator:
    """Provide a transactional scope around a series of operations."""
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# ---------- Table creation ----------


def create_tables() -> None:
    """Create all tables declared in the metadata.

    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS under the hood).
    For production schema changes, prefer Alembic migrations instead.
    """
    Base.metadata.create_all(engine)


# alias for backward compatibility
init_db = create_tables
