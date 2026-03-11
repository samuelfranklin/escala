use crate::{errors::AppError, models::couple::{Couple, CreateCoupleDto}, services::couple_service, AppState};
use tauri::State;
#[tauri::command] pub async fn get_couples(state: State<'_, AppState>) -> Result<Vec<Couple>, AppError> { couple_service::list_couples(&state.db).await }
#[tauri::command] pub async fn create_couple(state: State<'_, AppState>, dto: CreateCoupleDto) -> Result<Couple, AppError> { couple_service::create_couple(&state.db, dto).await }
#[tauri::command] pub async fn delete_couple(state: State<'_, AppState>, id: String) -> Result<(), AppError> { couple_service::delete_couple(&state.db, &id).await }
