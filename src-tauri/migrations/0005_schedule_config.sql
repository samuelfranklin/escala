-- Migration: 0005_schedule_config
-- Tabela de configuração global do gerador de escala.
-- Persiste as regras que antes eram constantes hardcoded em scoring.rs e constraints.rs.
-- Sempre contém exatamente uma linha (id = 1).

CREATE TABLE IF NOT EXISTS schedule_config (
    id                        INTEGER PRIMARY KEY DEFAULT 1,
    apply_monthly_limit       INTEGER NOT NULL DEFAULT 1,
    max_occurrences_per_month INTEGER NOT NULL DEFAULT 2,
    propagate_couples         INTEGER NOT NULL DEFAULT 1,
    apply_history_scoring     INTEGER NOT NULL DEFAULT 1,
    CHECK (id = 1)
);

INSERT OR IGNORE INTO schedule_config (id) VALUES (1);
