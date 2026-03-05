use crate::{db::event_repo, errors::AppError, models::event::{CreateEventDto, Event, UpdateEventDto}};
use sqlx::SqlitePool;

pub async fn list_events(pool: &SqlitePool) -> Result<Vec<Event>, AppError> { event_repo::list_all(pool).await }
pub async fn get_event(pool: &SqlitePool, id: &str) -> Result<Event, AppError> { event_repo::get_by_id(pool, id).await }

pub async fn create_event(pool: &SqlitePool, dto: CreateEventDto) -> Result<Event, AppError> {
    if dto.name.trim().is_empty() { return Err(AppError::Validation("Name cannot be empty".into())); }
    if dto.event_date.trim().is_empty() { return Err(AppError::Validation("Event date cannot be empty".into())); }
    event_repo::create(pool, dto).await
}

pub async fn update_event(pool: &SqlitePool, id: &str, dto: UpdateEventDto) -> Result<Event, AppError> {
    if let Some(ref name) = dto.name { if name.trim().is_empty() { return Err(AppError::Validation("Name cannot be empty".into())); } }
    event_repo::update(pool, id, dto).await
}

pub async fn delete_event(pool: &SqlitePool, id: &str) -> Result<(), AppError> { event_repo::delete(pool, id).await }
