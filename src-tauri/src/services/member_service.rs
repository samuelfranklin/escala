use crate::{
    db::member_repo,
    errors::AppError,
    models::member::{CreateMemberDto, Member, UpdateMemberDto},
};
use sqlx::SqlitePool;

fn validate_email(email: &str) -> bool {
    let parts: Vec<&str> = email.split('@').collect();
    parts.len() == 2 && parts[1].contains('.')
}

pub async fn list_members(pool: &SqlitePool) -> Result<Vec<Member>, AppError> {
    member_repo::list_all(pool).await
}

pub async fn get_member(pool: &SqlitePool, id: &str) -> Result<Member, AppError> {
    member_repo::get_by_id(pool, id).await
}

pub async fn create_member(pool: &SqlitePool, dto: CreateMemberDto) -> Result<Member, AppError> {
    if dto.name.trim().is_empty() {
        return Err(AppError::Validation("Name cannot be empty".into()));
    }
    if let Some(ref email) = dto.email {
        if !email.is_empty() && !validate_email(email) {
            return Err(AppError::Validation("Invalid email format".into()));
        }
    }
    member_repo::create(pool, dto).await
}

pub async fn update_member(pool: &SqlitePool, id: &str, dto: UpdateMemberDto) -> Result<Member, AppError> {
    if let Some(ref name) = dto.name {
        if name.trim().is_empty() {
            return Err(AppError::Validation("Name cannot be empty".into()));
        }
    }
    if let Some(ref email) = dto.email {
        if !email.is_empty() && !validate_email(email) {
            return Err(AppError::Validation("Invalid email format".into()));
        }
    }
    member_repo::update(pool, id, dto).await
}

pub async fn delete_member(pool: &SqlitePool, id: &str) -> Result<(), AppError> {
    member_repo::delete(pool, id).await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_email_valid() {
        assert!(validate_email("user@example.com"));
        assert!(validate_email("a@b.c"));
    }

    #[test]
    fn test_validate_email_invalid() {
        assert!(!validate_email("notanemail"));
        assert!(!validate_email("@nodomain"));
        assert!(!validate_email("nodot@domain"));
    }

    #[tokio::test]
    async fn test_create_validates_empty_name() {
        let pool = sqlx::SqlitePool::connect(":memory:").await.unwrap();
        let dto = CreateMemberDto { name: "  ".into(), email: None, phone: None, instagram: None, rank: None };
        let result = create_member(&pool, dto).await;
        assert!(matches!(result, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_create_validates_email_format() {
        let pool = sqlx::SqlitePool::connect(":memory:").await.unwrap();
        let dto = CreateMemberDto {
            name: "João".into(),
            email: Some("not-an-email".into()),
            phone: None, instagram: None, rank: None,
        };
        let result = create_member(&pool, dto).await;
        assert!(matches!(result, Err(AppError::Validation(_))));
    }

    async fn setup_pool() -> sqlx::SqlitePool {
        let pool = sqlx::SqlitePool::connect(":memory:").await.unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();
        pool
    }

    #[tokio::test]
    async fn test_crud_full_cycle() {
        let pool = setup_pool().await;
        // Create
        let member = create_member(&pool, CreateMemberDto {
            name: "Alice".into(), email: Some("alice@test.com".into()),
            phone: Some("123".into()), instagram: None, rank: None,
        }).await.unwrap();
        assert_eq!(member.name, "Alice");
        assert_eq!(member.email.as_deref(), Some("alice@test.com"));

        // List
        let all = list_members(&pool).await.unwrap();
        assert_eq!(all.len(), 1);

        // Get
        let fetched = get_member(&pool, &member.id).await.unwrap();
        assert_eq!(fetched.id, member.id);

        // Update
        let updated = update_member(&pool, &member.id, UpdateMemberDto {
            name: Some("Alice Updated".into()), email: None,
            phone: None, instagram: None, rank: None, active: Some(false),
        }).await.unwrap();
        assert_eq!(updated.name, "Alice Updated");
        assert!(!updated.active);

        // Update with empty name should fail
        let err = update_member(&pool, &member.id, UpdateMemberDto {
            name: Some("  ".into()), email: None,
            phone: None, instagram: None, rank: None, active: None,
        }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));

        // Update with invalid email should fail
        let err = update_member(&pool, &member.id, UpdateMemberDto {
            name: None, email: Some("bad".into()),
            phone: None, instagram: None, rank: None, active: None,
        }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));

        // Delete
        delete_member(&pool, &member.id).await.unwrap();
        let all = list_members(&pool).await.unwrap();
        assert!(all.is_empty());
    }

    #[tokio::test]
    async fn test_get_nonexistent_returns_not_found() {
        let pool = setup_pool().await;
        let result = get_member(&pool, "nonexistent").await;
        assert!(matches!(result, Err(AppError::NotFound(_))));
    }

    #[tokio::test]
    async fn test_delete_nonexistent_returns_not_found() {
        let pool = setup_pool().await;
        let result = delete_member(&pool, "nonexistent").await;
        assert!(matches!(result, Err(AppError::NotFound(_))));
    }
}
