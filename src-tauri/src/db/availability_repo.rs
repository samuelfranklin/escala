use crate::{errors::AppError, models::availability::{Availability, CreateAvailabilityDto}};
use sqlx::SqlitePool;
use uuid::Uuid;

pub async fn list_by_member(pool: &SqlitePool, member_id: &str) -> Result<Vec<Availability>, AppError> {
    sqlx::query_as!(Availability, "SELECT id, member_id, unavailable_date, reason, created_at FROM availability WHERE member_id = ? ORDER BY unavailable_date", member_id)
        .fetch_all(pool).await.map_err(AppError::from)
}

pub async fn create(pool: &SqlitePool, dto: CreateAvailabilityDto) -> Result<Availability, AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    sqlx::query!("INSERT INTO availability (id, member_id, unavailable_date, reason) VALUES (?, ?, ?, ?)", id, dto.member_id, dto.unavailable_date, dto.reason)
        .execute(pool).await.map_err(|e| match e {
            sqlx::Error::Database(ref db) if db.message().contains("UNIQUE") => AppError::Conflict("Availability already registered for this date".into()),
            _ => AppError::from(e),
        })?;
    sqlx::query_as!(Availability, "SELECT id, member_id, unavailable_date, reason, created_at FROM availability WHERE id = ?", id)
        .fetch_one(pool).await.map_err(AppError::from)
}

pub async fn delete(pool: &SqlitePool, id: &str) -> Result<(), AppError> {
    let rows = sqlx::query!("DELETE FROM availability WHERE id = ?", id).execute(pool).await.map_err(AppError::from)?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("Availability not found".into())); }
    Ok(())
}
