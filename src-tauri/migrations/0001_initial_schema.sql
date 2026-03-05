-- Migration: 0001_initial_schema
-- Escala Mídia — Schema inicial completo

PRAGMA foreign_keys = ON;

-- Members: membros do time de mídia
CREATE TABLE IF NOT EXISTS members (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT UNIQUE,
    phone       TEXT,
    instagram   TEXT,
    rank        TEXT NOT NULL DEFAULT 'member'
                    CHECK(rank IN ('leader','trainer','member','recruit')),
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Squads: times/departamentos (câmera, som, transmissão, etc.)
CREATE TABLE IF NOT EXISTS squads (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Members ↔ Squads: um membro pode estar em vários times
CREATE TABLE IF NOT EXISTS members_squads (
    member_id   TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    squad_id    TEXT NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
    role        TEXT NOT NULL DEFAULT 'member',
    joined_at   TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (member_id, squad_id)
);

-- Events: cultos e eventos com data e configuração
CREATE TABLE IF NOT EXISTS events (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    event_date  TEXT NOT NULL,
    event_type  TEXT NOT NULL DEFAULT 'regular'
                    CHECK(event_type IN ('regular','special','training')),
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Event ↔ Squads: quais times participam de cada evento e quantos membros precisam
CREATE TABLE IF NOT EXISTS event_squads (
    event_id    TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    squad_id    TEXT NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
    min_members INTEGER NOT NULL DEFAULT 1,
    max_members INTEGER NOT NULL DEFAULT 3,
    PRIMARY KEY (event_id, squad_id)
);

-- Schedule entries: escala gerada — alocação de membro por evento e squad
CREATE TABLE IF NOT EXISTS schedule_entries (
    id          TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    squad_id    TEXT NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
    member_id   TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(event_id, squad_id, member_id)
);

-- Couples: restrições de par (esses dois não podem servir juntos)
CREATE TABLE IF NOT EXISTS couples (
    id          TEXT PRIMARY KEY,
    member_a_id TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    member_b_id TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK(member_a_id < member_b_id),
    UNIQUE(member_a_id, member_b_id)
);

-- Availability: indisponibilidade de membro em data específica
CREATE TABLE IF NOT EXISTS availability (
    id          TEXT PRIMARY KEY,
    member_id   TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    unavailable_date TEXT NOT NULL,
    reason      TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(member_id, unavailable_date)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_members_active ON members(active);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_schedule_event ON schedule_entries(event_id);
CREATE INDEX IF NOT EXISTS idx_schedule_member ON schedule_entries(member_id);
CREATE INDEX IF NOT EXISTS idx_availability_member ON availability(member_id);
CREATE INDEX IF NOT EXISTS idx_availability_date ON availability(unavailable_date);
