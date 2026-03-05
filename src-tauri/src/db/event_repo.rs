use crate::{errors::AppError, models::event::{CreateEventDto, Event, UpdateEventDto}};
use sqlx::SqlitePool;
use uuid::Uuid;

pub async fn list_all(pool: &SqlitePool) -> Result<Vec<Event>, AppError> {
    sqlx::query_as!(Event, "SELECT id, name, event_date, event_type, notes, created_at, updated_at FROM events ORDER BY event_date DESC")
        .fetch_all(pool).await.map_err(AppError::from)
}

pub async fn get_by_id(pool: &SqlitePool, id: &str) -> Result<Event, AppError> {
    sqlx::query_as!(Event, "SELECT id, name, event_date, event_type, notes, created_at, updated_at FROM events WHERE id = ?", id)
        .fetch_optional(pool).await.map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Event '{}' not found", id)))
}

pub async fn create(pool: &SqlitePool, dto: CreateEventDto) -> Result<Event, AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    let event_type = dto.event_type.unwrap_or_else(|| "regular".into());
    sqlx::query!("INSERT INTO events (id, name, event_date, event_type, notes) VALUES (?, ?, ?, ?, ?)",
        id, dto.name, dto.event_date, event_type, dto.notes)
        .execute(pool).await.map_err(AppError::from)?;
    get_by_id(pool, &id).await
}

pub async fn update(pool: &SqlitePool, id: &str, dto: UpdateEventDto) -> Result<Event, AppError> {
    let mut sets = vec!["updated_at = datetime('now')".to_string()];
    if let Some(v) = &dto.name       { sets.push(format!("name = '{}'", v.replace('\'', "''"))) }
    if let Some(v) = &dto.event_date { sets.push(format!("event_date = '{}'", v)) }
    if let Some(v) = &dto.event_type { sets.push(format!("event_type = '{}'", v)) }
    if let Some(v) = &dto.notes      { sets.push(format!("notes = '{}'", v.replace('\'', "''"))) }
    let sql = format!("UPDATE events SET {} WHERE id = '{}'", sets.join(", "), id);
    let rows = sqlx::query(&sql).execute(pool).await.map_err(AppError::from)?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound(format!("Event '{}' not found", id))); }
    get_by_id(pool, id).await
}

pub async fn delete(pool: &SqlitePool, id: &str) -> Result<(), AppError> {
    let rows = sqlx::query!("DELETE FROM events WHERE id = ?", id).execute(pool).await.map_err(AppError::from)?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound(format!("Event '{}' not found", id))); }
    Ok(())
}
