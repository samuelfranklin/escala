use crate::{errors::AppError, models::schedule::ScheduleView, services::schedule_service, AppState};
use tauri::State;

#[tauri::command] pub async fn get_schedule(state: State<'_, AppState>, event_id: String) -> Result<ScheduleView, AppError> { schedule_service::get_schedule(&state.db, &event_id).await }
#[tauri::command] pub async fn generate_schedule(state: State<'_, AppState>, event_id: String) -> Result<ScheduleView, AppError> { schedule_service::generate_schedule(&state.db, &event_id).await }
#[tauri::command] pub async fn clear_schedule(state: State<'_, AppState>, event_id: String) -> Result<(), AppError> { schedule_service::clear_schedule(&state.db, &event_id).await }
