use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Event {
    pub id: String,
    pub name: String,
    pub event_date: Option<String>,
    pub event_type: String,
    /// 0=Dom, 1=Seg, 2=Ter, 3=Qua, 4=Qui, 5=Sex, 6=Sáb — usado em eventos regulares
    pub day_of_week: Option<i64>,
    /// Frequência: weekly, biweekly, monthly_1..4 — usado em eventos regulares
    pub recurrence: Option<String>,
    pub notes: Option<String>,
    pub created_at: String,
    pub updated_at: String,
}

/// View retornada ao frontend (inclui nome do squad via JOIN)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventSquad {
    pub squad_id: String,
    pub squad_name: String,
    pub min_members: i64,
    pub max_members: i64,
}

/// Input para configurar squads num evento
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventSquadDto {
    pub squad_id: String,
    pub min_members: i64,
    pub max_members: i64,
}

#[derive(Debug, Deserialize)]
pub struct CreateEventDto {
    pub name: String,
    /// Obrigatório para eventos especiais e treinamentos; None para regulares
    pub event_date: Option<String>,
    pub event_type: Option<String>,
    pub day_of_week: Option<i64>,
    pub recurrence: Option<String>,
    pub notes: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateEventDto {
    pub name: Option<String>,
    pub event_date: Option<String>,
    pub event_type: Option<String>,
    pub day_of_week: Option<i64>,
    pub recurrence: Option<String>,
    pub notes: Option<String>,
}
