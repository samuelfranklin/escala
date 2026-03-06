use crate::{errors::AppError, models::schedule::{MonthScheduleView, OccurrenceSchedule, ScheduleEntryView, ScheduleView}};
use sqlx::SqlitePool;
use uuid::Uuid;

pub async fn get_by_event(pool: &SqlitePool, event_id: &str) -> Result<ScheduleView, AppError> {
    let event = sqlx::query!(
        r#"SELECT id as "id!", name as "name!", event_date FROM events WHERE id = ?"#, event_id)
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

/// Retorna a escala mensal para um dado mês (YYYY-MM), agrupada por ocorrência.
pub async fn get_month_schedule(pool: &SqlitePool, month: &str) -> Result<MonthScheduleView, AppError> {
    let pattern = format!("{}%", month);
    let rows = sqlx::query!(
        r#"SELECT se.event_id as "event_id!", e.name as "event_name!",
                  se.occurrence_date as "occurrence_date!",
                  se.id as "entry_id!", se.squad_id as "squad_id!", s.name as "squad_name!",
                  se.member_id as "member_id!", m.name as "member_name!"
           FROM schedule_entries se
           JOIN events e ON e.id = se.event_id
           JOIN squads s ON s.id = se.squad_id
           JOIN members m ON m.id = se.member_id
           WHERE se.occurrence_date LIKE ?
           ORDER BY se.occurrence_date, e.name, s.name, m.name"#,
        pattern
    ).fetch_all(pool).await.map_err(AppError::from)?;

    // Agrupa linearmente — rows já ordenadas por (occurrence_date, event_name)
    let mut occurrences: Vec<OccurrenceSchedule> = Vec::new();
    for r in rows {
        let needs_new = occurrences.last().map_or(true, |o: &OccurrenceSchedule| {
            o.event_id != r.event_id || o.occurrence_date != r.occurrence_date
        });
        if needs_new {
            occurrences.push(OccurrenceSchedule {
                event_id: r.event_id,
                event_name: r.event_name,
                occurrence_date: r.occurrence_date,
                entries: vec![ScheduleEntryView {
                    entry_id: r.entry_id,
                    squad_id: r.squad_id,
                    squad_name: r.squad_name,
                    member_id: r.member_id,
                    member_name: r.member_name,
                }],
            });
        } else {
            occurrences.last_mut().unwrap().entries.push(ScheduleEntryView {
                entry_id: r.entry_id,
                squad_id: r.squad_id,
                squad_name: r.squad_name,
                member_id: r.member_id,
                member_name: r.member_name,
            });
        }
    }

    Ok(MonthScheduleView { month: month.to_string(), occurrences })
}

pub async fn insert_entry(pool: &SqlitePool, event_id: &str, squad_id: &str, member_id: &str) -> Result<(), AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    sqlx::query!("INSERT OR IGNORE INTO schedule_entries (id, event_id, squad_id, member_id) VALUES (?, ?, ?, ?)",
        id, event_id, squad_id, member_id)
        .execute(pool).await.map_err(AppError::from)?;
    Ok(())
}

/// Insere uma entrada de escala para uma ocorrência específica (com data).
pub async fn insert_occurrence_entry(
    pool: &SqlitePool,
    event_id: &str,
    occurrence_date: &str,
    squad_id: &str,
    member_id: &str,
) -> Result<(), AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    sqlx::query!(
        "INSERT OR IGNORE INTO schedule_entries (id, event_id, occurrence_date, squad_id, member_id) VALUES (?, ?, ?, ?, ?)",
        id, event_id, occurrence_date, squad_id, member_id)
        .execute(pool).await.map_err(AppError::from)?;
    Ok(())
}

pub async fn clear_event(pool: &SqlitePool, event_id: &str) -> Result<(), AppError> {
    sqlx::query!("DELETE FROM schedule_entries WHERE event_id = ?", event_id)
        .execute(pool).await.map_err(AppError::from)?;
    Ok(())
}

/// Remove todas as entradas de ocorrência para um mês (YYYY-MM).
pub async fn clear_month(pool: &SqlitePool, month: &str) -> Result<(), AppError> {
    let pattern = format!("{}%", month);
    sqlx::query!("DELETE FROM schedule_entries WHERE occurrence_date LIKE ?", pattern)
        .execute(pool).await.map_err(AppError::from)?;
    Ok(())
}
