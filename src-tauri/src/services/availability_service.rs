use crate::{db::availability_repo, errors::AppError, models::availability::{Availability, CreateAvailabilityDto}};
use sqlx::SqlitePool;

pub async fn list_by_member(pool: &SqlitePool, member_id: &str) -> Result<Vec<Availability>, AppError> { availability_repo::list_by_member(pool, member_id).await }

pub async fn create_availability(pool: &SqlitePool, dto: CreateAvailabilityDto) -> Result<Availability, AppError> {
    if dto.unavailable_date.trim().is_empty() { return Err(AppError::Validation("Date cannot be empty".into())); }
    availability_repo::create(pool, dto).await
}

pub async fn delete_availability(pool: &SqlitePool, id: &str) -> Result<(), AppError> { availability_repo::delete(pool, id).await }

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
    async fn test_availability_crud() {
        let pool = setup_pool().await;
        let member = member_service::create_member(&pool, CreateMemberDto {
            name: "Alice".into(), email: None, phone: None, instagram: None, rank: None,
        }).await.unwrap();

        let avail = create_availability(&pool, CreateAvailabilityDto {
            member_id: member.id.clone(), unavailable_date: "2026-03-15".into(), reason: Some("Viagem".into()),
        }).await.unwrap();
        assert_eq!(avail.unavailable_date, "2026-03-15");

        let list = list_by_member(&pool, &member.id).await.unwrap();
        assert_eq!(list.len(), 1);

        delete_availability(&pool, &avail.id).await.unwrap();
        assert!(list_by_member(&pool, &member.id).await.unwrap().is_empty());
    }

    #[tokio::test]
    async fn test_empty_date_fails() {
        let pool = setup_pool().await;
        let err = create_availability(&pool, CreateAvailabilityDto {
            member_id: "any".into(), unavailable_date: "  ".into(), reason: None,
        }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_delete_nonexistent() {
        let pool = setup_pool().await;
        let err = delete_availability(&pool, "nonexistent").await;
        assert!(matches!(err, Err(AppError::NotFound(_))));
    }
}
