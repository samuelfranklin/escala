use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Event {
    pub id: String,
    pub name: String,
    pub event_date: String,
    pub event_type: String,
    pub notes: Option<String>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventSquad {
    pub event_id: String,
    pub squad_id: String,
    pub min_members: i64,
    pub max_members: i64,
}

#[derive(Debug, Deserialize)]
pub struct CreateEventDto {
    pub name: String,
    pub event_date: String,
    pub event_type: Option<String>,
    pub notes: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateEventDto {
    pub name: Option<String>,
    pub event_date: Option<String>,
    pub event_type: Option<String>,
    pub notes: Option<String>,
}
