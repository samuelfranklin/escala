use crate::{db::availability_repo, errors::AppError, models::availability::{Availability, CreateAvailabilityDto}};
use sqlx::SqlitePool;

pub async fn list_by_member(pool: &SqlitePool, member_id: &str) -> Result<Vec<Availability>, AppError> { availability_repo::list_by_member(pool, member_id).await }

pub async fn create_availability(pool: &SqlitePool, dto: CreateAvailabilityDto) -> Result<Availability, AppError> {
    if dto.unavailable_date.trim().is_empty() { return Err(AppError::Validation("Date cannot be empty".into())); }
    availability_repo::create(pool, dto).await
}

pub async fn delete_availability(pool: &SqlitePool, id: &str) -> Result<(), AppError> { availability_repo::delete(pool, id).await }
