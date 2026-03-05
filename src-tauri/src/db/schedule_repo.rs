use crate::{errors::AppError, models::schedule::{ScheduleEntryView, ScheduleView}};
use sqlx::SqlitePool;
use uuid::Uuid;

pub async fn get_by_event(pool: &SqlitePool, event_id: &str) -> Result<ScheduleView, AppError> {
    let event = sqlx::query!(
        r#"SELECT id as "id!", name as "name!", event_date as "event_date!" FROM events WHERE id = ?"#, event_id)
        .fetch_optional(pool).await.map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Event '{}' not found", event_id)))?;

    let entries = sqlx::query!(
        r#"SELECT se.id as "entry_id!", se.squad_id as "squad_id!", s.name as "squad_name!",
                  se.member_id as "member_id!", m.name as "member_name!"
           FROM schedule_entries se
           JOIN squads s ON s.id = se.squad_id
           JOIN members m ON m.id = se.member_id
           WHERE se.event_id = ?
           ORDER BY s.name, m.name"#,
        event_id
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(ScheduleView {
        event_id: event.id,
        event_name: event.name,
        event_date: event.event_date,
        entries: entries.into_iter().map(|r| ScheduleEntryView {
            entry_id: r.entry_id,
            squad_id: r.squad_id,
            squad_name: r.squad_name,
            member_id: r.member_id,
            member_name: r.member_name,
        }).collect(),
    })
}

pub async fn insert_entry(pool: &SqlitePool, event_id: &str, squad_id: &str, member_id: &str) -> Result<(), AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    sqlx::query!("INSERT OR IGNORE INTO schedule_entries (id, event_id, squad_id, member_id) VALUES (?, ?, ?, ?)",
        id, event_id, squad_id, member_id)
        .execute(pool).await.map_err(AppError::from)?;
    Ok(())
}

pub async fn clear_event(pool: &SqlitePool, event_id: &str) -> Result<(), AppError> {
    sqlx::query!("DELETE FROM schedule_entries WHERE event_id = ?", event_id)
        .execute(pool).await.map_err(AppError::from)?;
    Ok(())
}
