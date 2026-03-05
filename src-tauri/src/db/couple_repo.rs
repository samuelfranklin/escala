use crate::{errors::AppError, models::couple::{Couple, CreateCoupleDto}};
use sqlx::SqlitePool;
use uuid::Uuid;

pub async fn list_all(pool: &SqlitePool) -> Result<Vec<Couple>, AppError> {
    sqlx::query_as!(Couple, "SELECT id, member_a_id, member_b_id, created_at FROM couples ORDER BY created_at")
        .fetch_all(pool).await.map_err(AppError::from)
}

pub async fn create(pool: &SqlitePool, a_id: &str, b_id: &str) -> Result<Couple, AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    // Canonical order: smaller id first (enforced by CHECK constraint)
    let (a, b) = if a_id < b_id { (a_id, b_id) } else { (b_id, a_id) };
    sqlx::query!("INSERT INTO couples (id, member_a_id, member_b_id) VALUES (?, ?, ?)", id, a, b)
        .execute(pool).await.map_err(|e| match e {
            sqlx::Error::Database(ref db) if db.message().contains("UNIQUE") => AppError::Conflict("Couple already exists".into()),
            _ => AppError::from(e),
        })?;
    sqlx::query_as!(Couple, "SELECT id, member_a_id, member_b_id, created_at FROM couples WHERE id = ?", id)
        .fetch_one(pool).await.map_err(AppError::from)
}

pub async fn delete(pool: &SqlitePool, id: &str) -> Result<(), AppError> {
    let rows = sqlx::query!("DELETE FROM couples WHERE id = ?", id).execute(pool).await.map_err(AppError::from)?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("Couple not found".into())); }
    Ok(())
}
