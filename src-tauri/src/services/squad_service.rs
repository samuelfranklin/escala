use crate::{db::squad_repo, errors::AppError, models::{member::Member, squad::{CreateSquadDto, Squad, UpdateSquadDto}}};
use sqlx::SqlitePool;

pub async fn list_squads(pool: &SqlitePool) -> Result<Vec<Squad>, AppError> { squad_repo::list_all(pool).await }
pub async fn get_squad(pool: &SqlitePool, id: &str) -> Result<Squad, AppError> { squad_repo::get_by_id(pool, id).await }

pub async fn create_squad(pool: &SqlitePool, dto: CreateSquadDto) -> Result<Squad, AppError> {
    if dto.name.trim().is_empty() { return Err(AppError::Validation("Name cannot be empty".into())); }
    squad_repo::create(pool, dto).await
}

pub async fn update_squad(pool: &SqlitePool, id: &str, dto: UpdateSquadDto) -> Result<Squad, AppError> {
    if let Some(ref name) = dto.name { if name.trim().is_empty() { return Err(AppError::Validation("Name cannot be empty".into())); } }
    squad_repo::update(pool, id, dto).await
}

pub async fn delete_squad(pool: &SqlitePool, id: &str) -> Result<(), AppError> { squad_repo::delete(pool, id).await }
pub async fn get_squad_members(pool: &SqlitePool, squad_id: &str) -> Result<Vec<Member>, AppError> { squad_repo::get_members(pool, squad_id).await }
pub async fn add_member_to_squad(pool: &SqlitePool, squad_id: &str, member_id: &str, role: &str) -> Result<(), AppError> { squad_repo::add_member(pool, squad_id, member_id, role).await }
pub async fn remove_member_from_squad(pool: &SqlitePool, squad_id: &str, member_id: &str) -> Result<(), AppError> { squad_repo::remove_member(pool, squad_id, member_id).await }
