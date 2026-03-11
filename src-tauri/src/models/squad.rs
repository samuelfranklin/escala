use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Squad {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct SquadWithMembers {
    pub squad: Squad,
    pub members: Vec<crate::models::member::Member>,
}

#[derive(Debug, Deserialize)]
pub struct CreateSquadDto {
    pub name: String,
    pub description: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateSquadDto {
    pub name: Option<String>,
    pub description: Option<String>,
}
