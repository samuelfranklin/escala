use crate::{errors::AppError, models::{member::Member, squad::{CreateSquadDto, Squad, UpdateSquadDto}}};
use sqlx::SqlitePool;
use uuid::Uuid;

pub async fn list_all(pool: &SqlitePool) -> Result<Vec<Squad>, AppError> {
    sqlx::query_as!(Squad, "SELECT id, name, description, created_at, updated_at FROM squads ORDER BY name")
        .fetch_all(pool).await.map_err(AppError::from)
}

pub async fn get_by_id(pool: &SqlitePool, id: &str) -> Result<Squad, AppError> {
    sqlx::query_as!(Squad, "SELECT id, name, description, created_at, updated_at FROM squads WHERE id = ?", id)
        .fetch_optional(pool).await.map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Squad '{}' not found", id)))
}

pub async fn create(pool: &SqlitePool, dto: CreateSquadDto) -> Result<Squad, AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    sqlx::query!("INSERT INTO squads (id, name, description) VALUES (?, ?, ?)", id, dto.name, dto.description)
        .execute(pool).await.map_err(|e| match e {
            sqlx::Error::Database(ref db) if db.message().contains("UNIQUE") => AppError::Conflict("Squad name already exists".into()),
            _ => AppError::from(e),
        })?;
    get_by_id(pool, &id).await
}

pub async fn update(pool: &SqlitePool, id: &str, dto: UpdateSquadDto) -> Result<Squad, AppError> {
    let mut sets = vec!["updated_at = datetime('now')".to_string()];
    if let Some(v) = &dto.name        { sets.push(format!("name = '{}'", v.replace('\'', "''"))) }
    if let Some(v) = &dto.description { sets.push(format!("description = '{}'", v.replace('\'', "''"))) }
    let sql = format!("UPDATE squads SET {} WHERE id = '{}'", sets.join(", "), id);
    let rows = sqlx::query(&sql).execute(pool).await.map_err(AppError::from)?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound(format!("Squad '{}' not found", id))); }
    get_by_id(pool, id).await
}

pub async fn delete(pool: &SqlitePool, id: &str) -> Result<(), AppError> {
    let rows = sqlx::query!("DELETE FROM squads WHERE id = ?", id).execute(pool).await.map_err(AppError::from)?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound(format!("Squad '{}' not found", id))); }
    Ok(())
}

pub async fn get_members(pool: &SqlitePool, squad_id: &str) -> Result<Vec<Member>, AppError> {
    sqlx::query_as!(
        Member,
        r#"SELECT m.id, m.name, m.email, m.phone, m.instagram, m.rank,
                  m.active as "active: bool", m.created_at, m.updated_at
           FROM members m
           INNER JOIN members_squads ms ON ms.member_id = m.id
           WHERE ms.squad_id = ? ORDER BY m.name"#,
        squad_id
    ).fetch_all(pool).await.map_err(AppError::from)
}

pub async fn add_member(pool: &SqlitePool, squad_id: &str, member_id: &str, role: &str) -> Result<(), AppError> {
    sqlx::query!("INSERT INTO members_squads (member_id, squad_id, role) VALUES (?, ?, ?)", member_id, squad_id, role)
        .execute(pool).await.map_err(|e| match e {
            sqlx::Error::Database(ref db) if db.message().contains("UNIQUE") => AppError::Conflict("Member already in squad".into()),
            _ => AppError::from(e),
        })?;
    Ok(())
}

pub async fn remove_member(pool: &SqlitePool, squad_id: &str, member_id: &str) -> Result<(), AppError> {
    let rows = sqlx::query!("DELETE FROM members_squads WHERE squad_id = ? AND member_id = ?", squad_id, member_id)
        .execute(pool).await.map_err(AppError::from)?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("Member not in squad".into())); }
    Ok(())
}
