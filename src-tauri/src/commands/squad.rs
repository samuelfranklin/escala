use crate::{errors::AppError, models::{member::Member, squad::{CreateSquadDto, Squad, UpdateSquadDto}}, services::squad_service, AppState};
use tauri::State;

#[tauri::command] pub async fn get_squads(state: State<'_, AppState>) -> Result<Vec<Squad>, AppError> { squad_service::list_squads(&state.db).await }
#[tauri::command] pub async fn get_squad(state: State<'_, AppState>, id: String) -> Result<Squad, AppError> { squad_service::get_squad(&state.db, &id).await }
#[tauri::command] pub async fn create_squad(state: State<'_, AppState>, dto: CreateSquadDto) -> Result<Squad, AppError> { squad_service::create_squad(&state.db, dto).await }
#[tauri::command] pub async fn update_squad(state: State<'_, AppState>, id: String, dto: UpdateSquadDto) -> Result<Squad, AppError> { squad_service::update_squad(&state.db, &id, dto).await }
#[tauri::command] pub async fn delete_squad(state: State<'_, AppState>, id: String) -> Result<(), AppError> { squad_service::delete_squad(&state.db, &id).await }
#[tauri::command] pub async fn get_squad_members(state: State<'_, AppState>, squad_id: String) -> Result<Vec<Member>, AppError> { squad_service::get_squad_members(&state.db, &squad_id).await }
#[tauri::command] pub async fn add_member_to_squad(state: State<'_, AppState>, squad_id: String, member_id: String, role: String) -> Result<(), AppError> { squad_service::add_member_to_squad(&state.db, &squad_id, &member_id, &role).await }
#[tauri::command] pub async fn remove_member_from_squad(state: State<'_, AppState>, squad_id: String, member_id: String) -> Result<(), AppError> { squad_service::remove_member_from_squad(&state.db, &squad_id, &member_id).await }
