use crate::{errors::AppError, models::event::{CreateEventDto, Event, EventSquad, EventSquadDto, UpdateEventDto}, services::event_service, AppState};
use tauri::State;

#[tauri::command] pub async fn get_events(state: State<'_, AppState>) -> Result<Vec<Event>, AppError> { event_service::list_events(&state.db).await }
#[tauri::command] pub async fn get_event(state: State<'_, AppState>, id: String) -> Result<Event, AppError> { event_service::get_event(&state.db, &id).await }
#[tauri::command] pub async fn create_event(state: State<'_, AppState>, dto: CreateEventDto) -> Result<Event, AppError> { event_service::create_event(&state.db, dto).await }
#[tauri::command] pub async fn update_event(state: State<'_, AppState>, id: String, dto: UpdateEventDto) -> Result<Event, AppError> { event_service::update_event(&state.db, &id, dto).await }
#[tauri::command] pub async fn delete_event(state: State<'_, AppState>, id: String) -> Result<(), AppError> { event_service::delete_event(&state.db, &id).await }
#[tauri::command] pub async fn get_event_squads(state: State<'_, AppState>, event_id: String) -> Result<Vec<EventSquad>, AppError> { event_service::get_event_squads(&state.db, &event_id).await }
#[tauri::command] pub async fn set_event_squads(state: State<'_, AppState>, event_id: String, squads: Vec<EventSquadDto>) -> Result<Vec<EventSquad>, AppError> { event_service::set_event_squads(&state.db, &event_id, squads).await }
