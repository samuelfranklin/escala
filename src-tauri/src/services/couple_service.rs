use crate::{db::couple_repo, errors::AppError, models::couple::{Couple, CreateCoupleDto}};
use sqlx::SqlitePool;

pub async fn list_couples(pool: &SqlitePool) -> Result<Vec<Couple>, AppError> { couple_repo::list_all(pool).await }

pub async fn create_couple(pool: &SqlitePool, dto: CreateCoupleDto) -> Result<Couple, AppError> {
    if dto.member_a_id == dto.member_b_id { return Err(AppError::Validation("A member cannot be coupled with themselves".into())); }
    couple_repo::create(pool, &dto.member_a_id, &dto.member_b_id).await
}

pub async fn delete_couple(pool: &SqlitePool, id: &str) -> Result<(), AppError> { couple_repo::delete(pool, id).await }

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

    async fn create_member(pool: &sqlx::SqlitePool, name: &str) -> String {
        member_service::create_member(pool, CreateMemberDto {
            name: name.into(), email: None, phone: None, instagram: None, rank: None,
        }).await.unwrap().id
    }

    #[tokio::test]
    async fn test_couple_crud() {
        let pool = setup_pool().await;
        let a = create_member(&pool, "Alice").await;
        let b = create_member(&pool, "Bob").await;

        let couple = create_couple(&pool, CreateCoupleDto { member_a_id: a.clone(), member_b_id: b.clone() }).await.unwrap();
        assert!(!couple.id.is_empty());

        let all = list_couples(&pool).await.unwrap();
        assert_eq!(all.len(), 1);

        delete_couple(&pool, &couple.id).await.unwrap();
        assert!(list_couples(&pool).await.unwrap().is_empty());
    }

    #[tokio::test]
    async fn test_couple_same_member_fails() {
        let pool = setup_pool().await;
        let a = create_member(&pool, "Alice").await;
        let err = create_couple(&pool, CreateCoupleDto { member_a_id: a.clone(), member_b_id: a }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_delete_nonexistent_couple() {
        let pool = setup_pool().await;
        let err = delete_couple(&pool, "nonexistent").await;
        assert!(matches!(err, Err(AppError::NotFound(_))));
    }
}
