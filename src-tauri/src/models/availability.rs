use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Availability {
    pub id: String,
    pub member_id: String,
    pub unavailable_date: String,
    pub reason: Option<String>,
    pub created_at: String,
}

#[derive(Debug, Deserialize)]
pub struct CreateAvailabilityDto {
    pub member_id: String,
    pub unavailable_date: String,
    pub reason: Option<String>,
}
