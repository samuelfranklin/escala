use crate::{errors::AppError, models::event::{CreateEventDto, Event, UpdateEventDto}, services::event_service, AppState};
use tauri::State;

#[tauri::command] pub async fn get_events(state: State<'_, AppState>) -> Result<Vec<Event>, AppError> { event_service::list_events(&state.db).await }
#[tauri::command] pub async fn get_event(state: State<'_, AppState>, id: String) -> Result<Event, AppError> { event_service::get_event(&state.db, &id).await }
#[tauri::command] pub async fn create_event(state: State<'_, AppState>, dto: CreateEventDto) -> Result<Event, AppError> { event_service::create_event(&state.db, dto).await }
#[tauri::command] pub async fn update_event(state: State<'_, AppState>, id: String, dto: UpdateEventDto) -> Result<Event, AppError> { event_service::update_event(&state.db, &id, dto).await }
#[tauri::command] pub async fn delete_event(state: State<'_, AppState>, id: String) -> Result<(), AppError> { event_service::delete_event(&state.db, &id).await }
