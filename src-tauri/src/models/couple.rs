use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Couple {
    pub id: String,
    pub member_a_id: String,
    pub member_b_id: String,
    pub created_at: String,
}

#[derive(Debug, Deserialize)]
pub struct CreateCoupleDto {
    pub member_a_id: String,
    pub member_b_id: String,
}
