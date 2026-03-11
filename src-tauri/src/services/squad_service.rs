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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::member::CreateMemberDto;
    use crate::services::member_service;

    async fn setup_pool() -> sqlx::SqlitePool {
        let pool = sqlx::SqlitePool::connect(":memory:").await.unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();
        pool
    }

    #[tokio::test]
    async fn test_squad_crud_full_cycle() {
        let pool = setup_pool().await;

        // Create
        let squad = create_squad(&pool, CreateSquadDto { name: "Câmera".into(), description: Some("Filmagem".into()) }).await.unwrap();
        assert_eq!(squad.name, "Câmera");
        assert_eq!(squad.description.as_deref(), Some("Filmagem"));

        // List
        let all = list_squads(&pool).await.unwrap();
        assert_eq!(all.len(), 1);

        // Get
        let fetched = get_squad(&pool, &squad.id).await.unwrap();
        assert_eq!(fetched.id, squad.id);

        // Update
        let updated = update_squad(&pool, &squad.id, UpdateSquadDto { name: Some("Som".into()), description: None }).await.unwrap();
        assert_eq!(updated.name, "Som");

        // Delete
        delete_squad(&pool, &squad.id).await.unwrap();
        assert!(list_squads(&pool).await.unwrap().is_empty());
    }

    #[tokio::test]
    async fn test_create_empty_name_fails() {
        let pool = setup_pool().await;
        let err = create_squad(&pool, CreateSquadDto { name: "  ".into(), description: None }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_update_empty_name_fails() {
        let pool = setup_pool().await;
        let squad = create_squad(&pool, CreateSquadDto { name: "Câmera".into(), description: None }).await.unwrap();
        let err = update_squad(&pool, &squad.id, UpdateSquadDto { name: Some("  ".into()), description: None }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_squad_members_management() {
        let pool = setup_pool().await;
        let squad = create_squad(&pool, CreateSquadDto { name: "Câmera".into(), description: None }).await.unwrap();
        let member = member_service::create_member(&pool, CreateMemberDto {
            name: "Alice".into(), email: None, phone: None, instagram: None, rank: None,
        }).await.unwrap();

        // Add member
        add_member_to_squad(&pool, &squad.id, &member.id, "member").await.unwrap();
        let members = get_squad_members(&pool, &squad.id).await.unwrap();
        assert_eq!(members.len(), 1);
        assert_eq!(members[0].name, "Alice");

        // Remove member
        remove_member_from_squad(&pool, &squad.id, &member.id).await.unwrap();
        assert!(get_squad_members(&pool, &squad.id).await.unwrap().is_empty());
    }

    #[tokio::test]
    async fn test_delete_nonexistent_squad() {
        let pool = setup_pool().await;
        let err = delete_squad(&pool, "nonexistent").await;
        assert!(matches!(err, Err(AppError::NotFound(_))));
    }

    #[tokio::test]
    async fn test_remove_nonexistent_member_from_squad() {
        let pool = setup_pool().await;
        let squad = create_squad(&pool, CreateSquadDto { name: "Câmera".into(), description: None }).await.unwrap();
        let err = remove_member_from_squad(&pool, &squad.id, "nonexistent").await;
        assert!(matches!(err, Err(AppError::NotFound(_))));
    }
}
