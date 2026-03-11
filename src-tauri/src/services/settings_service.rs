use crate::{
    db::settings_repo,
    errors::AppError,
    models::settings::{ScheduleConfig, UpdateScheduleConfigDto},
};
use sqlx::SqlitePool;

pub async fn get_config(pool: &SqlitePool) -> Result<ScheduleConfig, AppError> {
    settings_repo::get_config(pool).await
}

pub async fn update_config(
    pool: &SqlitePool,
    dto: UpdateScheduleConfigDto,
) -> Result<ScheduleConfig, AppError> {
    settings_repo::update_config(pool, dto).await
}

#[cfg(test)]
mod tests {
    use super::*;

    async fn setup_pool() -> sqlx::SqlitePool {
        let pool = sqlx::SqlitePool::connect(":memory:").await.unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();
        pool
    }

    #[tokio::test]
    async fn test_get_default_config() {
        let pool = setup_pool().await;
        let config = get_config(&pool).await.unwrap();
        assert!(config.apply_monthly_limit);
        assert_eq!(config.max_occurrences_per_month, 2);
        assert!(config.propagate_couples);
        assert!(config.apply_history_scoring);
    }

    #[tokio::test]
    async fn test_update_and_get_config() {
        let pool = setup_pool().await;
        let updated = update_config(&pool, UpdateScheduleConfigDto {
            apply_monthly_limit: false,
            max_occurrences_per_month: 5,
            propagate_couples: false,
            apply_history_scoring: false,
        }).await.unwrap();
        assert!(!updated.apply_monthly_limit);
        assert_eq!(updated.max_occurrences_per_month, 5);
        assert!(!updated.propagate_couples);
        assert!(!updated.apply_history_scoring);

        // Verify persistence
        let fetched = get_config(&pool).await.unwrap();
        assert_eq!(fetched.max_occurrences_per_month, 5);
    }
}
