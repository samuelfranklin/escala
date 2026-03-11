use crate::{errors::AppError, models::event::{CreateEventDto, Event, EventSquad, EventSquadDto, UpdateEventDto}};
use sqlx::SqlitePool;
use uuid::Uuid;

pub async fn list_all(pool: &SqlitePool) -> Result<Vec<Event>, AppError> {
    sqlx::query_as!(Event,
        r#"SELECT id as "id!", name as "name!", event_date, event_type as "event_type!", day_of_week, recurrence, notes, created_at as "created_at!", updated_at as "updated_at!" FROM events ORDER BY event_date DESC NULLS LAST, name ASC"#)
        .fetch_all(pool).await.map_err(AppError::from)
}

pub async fn get_by_id(pool: &SqlitePool, id: &str) -> Result<Event, AppError> {
    sqlx::query_as!(Event,
        r#"SELECT id as "id!", name as "name!", event_date, event_type as "event_type!", day_of_week, recurrence, notes, created_at as "created_at!", updated_at as "updated_at!" FROM events WHERE id = ?"#, id)
        .fetch_optional(pool).await.map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Event '{}' not found", id)))
}

pub async fn create(pool: &SqlitePool, dto: CreateEventDto) -> Result<Event, AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    let event_type = dto.event_type.unwrap_or_else(|| "regular".into());
    sqlx::query!(
        "INSERT INTO events (id, name, event_date, event_type, day_of_week, recurrence, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        id, dto.name, dto.event_date, event_type, dto.day_of_week, dto.recurrence, dto.notes)
        .execute(pool).await.map_err(AppError::from)?;
    get_by_id(pool, &id).await
}

pub async fn update(pool: &SqlitePool, id: &str, dto: UpdateEventDto) -> Result<Event, AppError> {
    let mut sets = vec!["updated_at = datetime('now')".to_string()];
    if let Some(v) = &dto.name       { sets.push(format!("name = '{}'", v.replace('\'', "''"))) }
    if let Some(v) = &dto.event_date { sets.push(format!("event_date = '{}'", v)) }
    if let Some(v) = &dto.event_type { sets.push(format!("event_type = '{}'", v)) }
    if let Some(v) = dto.day_of_week { sets.push(format!("day_of_week = {}", v)) }
    if let Some(v) = &dto.recurrence { sets.push(format!("recurrence = '{}'", v)) }
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

pub async fn get_event_squads(pool: &SqlitePool, event_id: &str) -> Result<Vec<EventSquad>, AppError> {
    let rows = sqlx::query!(
        r#"SELECT es.squad_id as "squad_id!", s.name as "squad_name!", es.min_members as "min_members!", es.max_members as "max_members!"
           FROM event_squads es
           INNER JOIN squads s ON s.id = es.squad_id
           WHERE es.event_id = ?
           ORDER BY s.name"#,
        event_id
    )
    .fetch_all(pool)
    .await
    .map_err(AppError::from)?;

    Ok(rows.into_iter()
        .map(|r| EventSquad {
            squad_id: r.squad_id,
            squad_name: r.squad_name,
            min_members: r.min_members,
            max_members: r.max_members,
        })
        .collect())
}

pub async fn set_event_squads(pool: &SqlitePool, event_id: &str, items: &[EventSquadDto]) -> Result<(), AppError> {
    let mut tx: sqlx::Transaction<'_, sqlx::Sqlite> = pool.begin().await.map_err(AppError::from)?;
    sqlx::query!("DELETE FROM event_squads WHERE event_id = ?", event_id)
        .execute(tx.as_mut())
        .await
        .map_err(AppError::from)?;
    for item in items {
        sqlx::query!(
            "INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES (?, ?, ?, ?)",
            event_id, item.squad_id, item.min_members, item.max_members
        )
        .execute(tx.as_mut())
        .await
        .map_err(AppError::from)?;
    }
    tx.commit().await.map_err(AppError::from)
}
