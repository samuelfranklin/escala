use serde::{Deserialize, Serialize};

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
    pub event_date: String,
    pub entries: Vec<ScheduleEntryView>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleEntryView {
    pub entry_id: String,
    pub squad_id: String,
    pub squad_name: String,
    pub member_id: String,
    pub member_name: String,
}
