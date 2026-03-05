use crate::{errors::AppError, models::member::{CreateMemberDto, Member, UpdateMemberDto}};
use sqlx::SqlitePool;
use uuid::Uuid;

pub async fn list_all(pool: &SqlitePool) -> Result<Vec<Member>, AppError> {
    sqlx::query_as!(
        Member,
        r#"SELECT id as "id!", name as "name!", email, phone, instagram, rank as "rank!",
                  active as "active: bool", created_at as "created_at!", updated_at as "updated_at!"
           FROM members ORDER BY name"#
    )
    .fetch_all(pool)
    .await
    .map_err(AppError::from)
}

pub async fn get_by_id(pool: &SqlitePool, id: &str) -> Result<Member, AppError> {
    sqlx::query_as!(
        Member,
        r#"SELECT id as "id!", name as "name!", email, phone, instagram, rank as "rank!",
                  active as "active: bool", created_at as "created_at!", updated_at as "updated_at!"
           FROM members WHERE id = ?"#,
        id
    )
    .fetch_optional(pool)
    .await
    .map_err(AppError::from)?
    .ok_or_else(|| AppError::NotFound(format!("Member '{}' not found", id)))
}

pub async fn create(pool: &SqlitePool, dto: CreateMemberDto) -> Result<Member, AppError> {
    let id = Uuid::new_v4().to_string().replace('-', "");
    let rank = dto.rank.unwrap_or_else(|| "member".to_string());
    sqlx::query!(
        "INSERT INTO members (id, name, email, phone, instagram, rank) VALUES (?, ?, ?, ?, ?, ?)",
        id, dto.name, dto.email, dto.phone, dto.instagram, rank
    )
    .execute(pool)
    .await
    .map_err(|e| match e {
        sqlx::Error::Database(ref db) if db.message().contains("UNIQUE") => {
            AppError::Conflict("Email already in use".into())
        }
        _ => AppError::from(e),
    })?;
    get_by_id(pool, &id).await
}

pub async fn update(pool: &SqlitePool, id: &str, dto: UpdateMemberDto) -> Result<Member, AppError> {
    // Build dynamic update — only set provided fields
    let mut sets: Vec<String> = vec!["updated_at = datetime('now')".to_string()];
    if let Some(v) = &dto.name        { sets.push(format!("name = '{}'", v.replace('\'', "''"))) }
    if let Some(v) = &dto.email       { sets.push(format!("email = '{}'", v.replace('\'', "''"))) }
    if let Some(v) = &dto.phone       { sets.push(format!("phone = '{}'", v.replace('\'', "''"))) }
    if let Some(v) = &dto.instagram   { sets.push(format!("instagram = '{}'", v.replace('\'', "''"))) }
    if let Some(v) = &dto.rank        { sets.push(format!("rank = '{}'", v.replace('\'', "''"))) }
    if let Some(v) = dto.active       { sets.push(format!("active = {}", v as i32)) }

    let sql = format!("UPDATE members SET {} WHERE id = '{}'", sets.join(", "), id);
    let rows = sqlx::query(&sql).execute(pool).await.map_err(AppError::from)?.rows_affected();
    if rows == 0 {
        return Err(AppError::NotFound(format!("Member '{}' not found", id)));
    }
    get_by_id(pool, id).await
}

pub async fn delete(pool: &SqlitePool, id: &str) -> Result<(), AppError> {
    let rows = sqlx::query!("DELETE FROM members WHERE id = ?", id)
        .execute(pool)
        .await
        .map_err(AppError::from)?
        .rows_affected();
    if rows == 0 {
        return Err(AppError::NotFound(format!("Member '{}' not found", id)));
    }
    Ok(())
}
