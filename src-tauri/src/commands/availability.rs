use crate::{errors::AppError, models::availability::{Availability, CreateAvailabilityDto}, services::availability_service, AppState};
use tauri::State;
#[tauri::command] pub async fn get_availability(state: State<'_, AppState>, member_id: String) -> Result<Vec<Availability>, AppError> { availability_service::list_by_member(&state.db, &member_id).await }
#[tauri::command] pub async fn create_availability(state: State<'_, AppState>, dto: CreateAvailabilityDto) -> Result<Availability, AppError> { availability_service::create_availability(&state.db, dto).await }
#[tauri::command] pub async fn delete_availability(state: State<'_, AppState>, id: String) -> Result<(), AppError> { availability_service::delete_availability(&state.db, &id).await }
