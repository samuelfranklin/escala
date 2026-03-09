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
