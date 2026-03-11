use crate::{
    errors::AppError,
    models::settings::{ScheduleConfig, UpdateScheduleConfigDto},
};
use sqlx::SqlitePool;

pub async fn get_config(pool: &SqlitePool) -> Result<ScheduleConfig, AppError> {
    sqlx::query_as!(
        ScheduleConfig,
        r#"SELECT apply_monthly_limit as "apply_monthly_limit: bool",
                  max_occurrences_per_month as "max_occurrences_per_month: i64",
                  propagate_couples as "propagate_couples: bool",
                  apply_history_scoring as "apply_history_scoring: bool"
           FROM schedule_config WHERE id = 1"#
    )
    .fetch_one(pool)
    .await
    .map_err(AppError::from)
}

pub async fn update_config(
    pool: &SqlitePool,
    dto: UpdateScheduleConfigDto,
) -> Result<ScheduleConfig, AppError> {
    sqlx::query!(
        r#"UPDATE schedule_config
           SET apply_monthly_limit = ?,
               max_occurrences_per_month = ?,
               propagate_couples = ?,
               apply_history_scoring = ?
           WHERE id = 1"#,
        dto.apply_monthly_limit,
        dto.max_occurrences_per_month,
        dto.propagate_couples,
        dto.apply_history_scoring,
    )
    .execute(pool)
    .await
    .map_err(AppError::from)?;

    get_config(pool).await
}
