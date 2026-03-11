-- Adiciona occurrence_date às entradas de escala.
-- Eventos fixos (special/training): occurrence_date = event_date.
-- Eventos regulares (recorrentes): occurrence_date = data calculada da ocorrência no mês.
-- Entradas antigas ficam NULL (sem impacto nas queries existentes por event_id).

ALTER TABLE schedule_entries ADD COLUMN occurrence_date TEXT;
