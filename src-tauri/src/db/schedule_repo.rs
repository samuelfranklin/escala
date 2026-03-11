use crate::{
    errors::AppError,
    models::event::EventSquad,
    models::schedule::{
        EventMonthRow, EventScheduleRow, MonthScheduleView, OccurrenceSchedule,
        ScheduleEntryView, ScheduleView,
    },
};
use chrono::NaiveDate;
use sqlx::SqlitePool;
use std::collections::{HashMap, HashSet};
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
        let needs_new = occurrences.last().is_none_or(|o: &OccurrenceSchedule| {
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

// ── Fetch: dados para geração de escala ──

pub async fn fetch_event_basics(pool: &SqlitePool, event_id: &str) -> Result<Option<EventScheduleRow>, AppError> {
    let row = sqlx::query!(
        r#"SELECT id as "id!", event_date, event_type as "event_type!" FROM events WHERE id = ?"#,
        event_id
    ).fetch_optional(pool).await.map_err(AppError::from)?;

    Ok(row.map(|r| EventScheduleRow {
        id: r.id,
        event_date: r.event_date,
        event_type: r.event_type,
    }))
}

pub async fn fetch_event_squads(pool: &SqlitePool, event_id: &str) -> Result<Vec<EventSquad>, AppError> {
    let rows = sqlx::query!(
        r#"SELECT es.squad_id as "squad_id!", s.name as "squad_name!", es.min_members, es.max_members
           FROM event_squads es
           JOIN squads s ON s.id = es.squad_id
           WHERE es.event_id = ?"#,
        event_id
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter().map(|r| EventSquad {
        squad_id: r.squad_id,
        squad_name: r.squad_name,
        min_members: r.min_members,
        max_members: r.max_members,
    }).collect())
}

pub async fn fetch_all_events(pool: &SqlitePool) -> Result<Vec<EventMonthRow>, AppError> {
    let rows = sqlx::query!(
        r#"SELECT id as "id!", name as "name!", event_date, event_type as "event_type!", day_of_week, recurrence
           FROM events"#
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter().map(|r| EventMonthRow {
        id: r.id,
        name: r.name,
        event_date: r.event_date,
        event_type: r.event_type,
        day_of_week: r.day_of_week,
        recurrence: r.recurrence,
    }).collect())
}

pub async fn fetch_unavailable_members(pool: &SqlitePool, date: &str) -> Result<HashSet<String>, AppError> {
    let rows = sqlx::query!(
        r#"SELECT member_id as "member_id!" FROM availability WHERE unavailable_date = ?"#,
        date
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter().map(|r| r.member_id).collect())
}

pub async fn fetch_couple_pairs(pool: &SqlitePool) -> Result<Vec<(String, String)>, AppError> {
    let rows = sqlx::query!(
        r#"SELECT member_a_id as "member_a_id!", member_b_id as "member_b_id!" FROM couples"#
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter().map(|r| (r.member_a_id, r.member_b_id)).collect())
}

pub async fn fetch_monthly_counts(pool: &SqlitePool, month: &str) -> Result<HashMap<String, i64>, AppError> {
    let pattern = format!("{}%", month);
    let rows = sqlx::query!(
        r#"SELECT member_id as "member_id!", COUNT(*) as "cnt: i64"
           FROM schedule_entries WHERE occurrence_date LIKE ? GROUP BY member_id"#,
        pattern
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter().map(|r| (r.member_id, r.cnt)).collect())
}

pub async fn fetch_historical_counts(pool: &SqlitePool, month: &str) -> Result<HashMap<String, i64>, AppError> {
    let pattern = format!("{}%", month);
    let rows = sqlx::query!(
        r#"SELECT member_id as "member_id!", COUNT(*) as "cnt: i64"
           FROM schedule_entries WHERE occurrence_date NOT LIKE ? GROUP BY member_id"#,
        pattern
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter().map(|r| (r.member_id, r.cnt)).collect())
}

pub async fn fetch_historical_counts_with_nulls(pool: &SqlitePool, month: &str) -> Result<HashMap<String, i64>, AppError> {
    let pattern = format!("{}%", month);
    let rows = sqlx::query!(
        r#"SELECT member_id as "member_id!", COUNT(*) as "cnt: i64"
           FROM schedule_entries
           WHERE occurrence_date NOT LIKE ? OR occurrence_date IS NULL
           GROUP BY member_id"#,
        pattern
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter().map(|r| (r.member_id, r.cnt)).collect())
}

pub async fn fetch_last_dates_before(pool: &SqlitePool, before_date: &str) -> Result<HashMap<String, NaiveDate>, AppError> {
    let rows = sqlx::query!(
        r#"SELECT member_id as "member_id!", MAX(occurrence_date) as "last_date!"
           FROM schedule_entries WHERE occurrence_date < ? GROUP BY member_id"#,
        before_date
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter()
        .filter_map(|r| {
            NaiveDate::parse_from_str(&r.last_date, "%Y-%m-%d").ok()
                .map(|d| (r.member_id, d))
        })
        .collect())
}

pub async fn fetch_last_dates_excluding_month(pool: &SqlitePool, month: &str) -> Result<HashMap<String, NaiveDate>, AppError> {
    let pattern = format!("{}%", month);
    let rows = sqlx::query!(
        r#"SELECT member_id as "member_id!", MAX(occurrence_date) as "last_date!"
           FROM schedule_entries WHERE occurrence_date NOT LIKE ? GROUP BY member_id"#,
        pattern
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter()
        .filter_map(|r| {
            NaiveDate::parse_from_str(&r.last_date, "%Y-%m-%d").ok()
                .map(|d| (r.member_id, d))
        })
        .collect())
}

pub async fn fetch_squad_candidates(pool: &SqlitePool, squad_id: &str) -> Result<Vec<String>, AppError> {
    let rows = sqlx::query!(
        r#"SELECT m.id as "id!" FROM members m
           INNER JOIN members_squads ms ON ms.member_id = m.id
           WHERE ms.squad_id = ? AND m.active = 1"#,
        squad_id
    ).fetch_all(pool).await.map_err(AppError::from)?;

    Ok(rows.into_iter().map(|r| r.id).collect())
}

/// Salva todas as alocações do mês em transação atômica (delete + insert).
pub async fn save_month_allocations(
    pool: &SqlitePool,
    month: &str,
    allocations: &[(String, String, String, String)],
) -> Result<(), AppError> {
    let month_pattern = format!("{}%", month);
    let mut tx = pool.begin().await.map_err(AppError::from)?;

    sqlx::query!("DELETE FROM schedule_entries WHERE occurrence_date LIKE ?", month_pattern)
        .execute(&mut *tx).await.map_err(AppError::from)?;

    for (event_id, occurrence_date, squad_id, member_id) in allocations {
        let id = Uuid::new_v4().to_string().replace('-', "");
        sqlx::query!(
            "INSERT INTO schedule_entries (id, event_id, occurrence_date, squad_id, member_id) VALUES (?, ?, ?, ?, ?)",
            id, event_id, occurrence_date, squad_id, member_id
        ).execute(&mut *tx).await.map_err(AppError::from)?;
    }

    tx.commit().await.map_err(AppError::from)?;
    Ok(())
}
