-- Migration: 0004_fix_schedule_unique_constraint
-- Corrige a constraint UNIQUE de schedule_entries para incluir occurrence_date.
-- Sem occurrence_date na constraint, o INSERT OR IGNORE descartava silenciosamente
-- todas as ocorrências de um evento recorrente após a primeira no mesmo mês.

PRAGMA foreign_keys = OFF;

CREATE TABLE schedule_entries_new (
    id              TEXT PRIMARY KEY,
    event_id        TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    occurrence_date TEXT,
    squad_id        TEXT NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
    member_id       TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(event_id, occurrence_date, squad_id, member_id)
);

INSERT INTO schedule_entries_new (id, event_id, occurrence_date, squad_id, member_id, created_at)
SELECT id, event_id, occurrence_date, squad_id, member_id, created_at FROM schedule_entries;

DROP TABLE schedule_entries;
ALTER TABLE schedule_entries_new RENAME TO schedule_entries;

PRAGMA foreign_keys = ON;
