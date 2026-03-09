use serde::{Deserialize, Serialize};

/// Dados mínimos de evento para geração de escala unitária
#[derive(Debug, Clone)]
pub struct EventScheduleRow {
    pub id: String,
    pub event_date: Option<String>,
    pub event_type: String,
}

/// Dados de evento para geração de escala mensal
#[derive(Debug, Clone)]
pub struct EventMonthRow {
    pub id: String,
    pub name: String,
    pub event_date: Option<String>,
    pub event_type: String,
    pub day_of_week: Option<i64>,
    pub recurrence: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ScheduleEntry {
    pub id: String,
    pub event_id: String,
    pub squad_id: String,
    pub member_id: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleView {
    pub event_id: String,
    pub event_name: String,
    pub event_date: Option<String>,
    pub entries: Vec<ScheduleEntryView>,
}

/// Uma ocorrência concreta de um evento (uma data específica dentro do mês)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OccurrenceSchedule {
    pub event_id: String,
    pub event_name: String,
    /// Data concreta da ocorrência: YYYY-MM-DD
    pub occurrence_date: String,
    pub entries: Vec<ScheduleEntryView>,
}

/// Escala mensal: todas as ocorrências de todos os eventos num mês YYYY-MM
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonthScheduleView {
    pub month: String,
    pub occurrences: Vec<OccurrenceSchedule>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleEntryView {
    pub entry_id: String,
    pub squad_id: String,
    pub squad_name: String,
    pub member_id: String,
    pub member_name: String,
}
