-- Migration: torna event_date opcional e adiciona suporte a recorrência
-- Eventos regulares (recorrentes) usam day_of_week + recurrence e não têm data fixa.
-- Eventos especiais/treinamentos mantêm event_date.

CREATE TABLE events_new (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    event_date  TEXT,
    event_type  TEXT NOT NULL DEFAULT 'regular'
                    CHECK(event_type IN ('regular','special','training')),
    day_of_week INTEGER CHECK(day_of_week BETWEEN 0 AND 6),
    recurrence  TEXT CHECK(recurrence IN ('weekly','biweekly','monthly_1','monthly_2','monthly_3','monthly_4')),
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO events_new (id, name, event_date, event_type, notes, created_at, updated_at)
    SELECT id, name, event_date, event_type, notes, created_at, updated_at FROM events;

DROP TABLE events;
ALTER TABLE events_new RENAME TO events;
