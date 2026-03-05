use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Member {
    pub id: String,
    pub name: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub instagram: Option<String>,
    pub rank: String,
    pub active: bool,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Deserialize)]
pub struct CreateMemberDto {
    pub name: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub instagram: Option<String>,
    pub rank: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateMemberDto {
    pub name: Option<String>,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub instagram: Option<String>,
    pub rank: Option<String>,
    pub active: Option<bool>,
}
