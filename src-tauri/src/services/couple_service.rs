use crate::{db::couple_repo, errors::AppError, models::couple::{Couple, CreateCoupleDto}};
use sqlx::SqlitePool;

pub async fn list_couples(pool: &SqlitePool) -> Result<Vec<Couple>, AppError> { couple_repo::list_all(pool).await }

pub async fn create_couple(pool: &SqlitePool, dto: CreateCoupleDto) -> Result<Couple, AppError> {
    if dto.member_a_id == dto.member_b_id { return Err(AppError::Validation("A member cannot be coupled with themselves".into())); }
    couple_repo::create(pool, &dto.member_a_id, &dto.member_b_id).await
}

pub async fn delete_couple(pool: &SqlitePool, id: &str) -> Result<(), AppError> { couple_repo::delete(pool, id).await }
