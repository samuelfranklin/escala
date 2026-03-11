use crate::{
    errors::AppError,
    models::settings::{ScheduleConfig, UpdateScheduleConfigDto},
    services::settings_service,
    AppState,
};
use tauri::State;

#[tauri::command]
pub async fn get_schedule_config(state: State<'_, AppState>) -> Result<ScheduleConfig, AppError> {
    settings_service::get_config(&state.db).await
}

#[tauri::command]
pub async fn update_schedule_config(
    state: State<'_, AppState>,
    dto: UpdateScheduleConfigDto,
) -> Result<ScheduleConfig, AppError> {
    settings_service::update_config(&state.db, dto).await
}
