use crate::{
    errors::AppError,
    models::member::{CreateMemberDto, Member, UpdateMemberDto},
    services::member_service,
    AppState,
};
use tauri::State;

#[tauri::command]
pub async fn get_members(state: State<'_, AppState>) -> Result<Vec<Member>, AppError> {
    member_service::list_members(&state.db).await
}

#[tauri::command]
pub async fn get_member(state: State<'_, AppState>, id: String) -> Result<Member, AppError> {
    member_service::get_member(&state.db, &id).await
}

#[tauri::command]
pub async fn create_member(
    state: State<'_, AppState>,
    dto: CreateMemberDto,
) -> Result<Member, AppError> {
    member_service::create_member(&state.db, dto).await
}

#[tauri::command]
pub async fn update_member(
    state: State<'_, AppState>,
    id: String,
    dto: UpdateMemberDto,
) -> Result<Member, AppError> {
    member_service::update_member(&state.db, &id, dto).await
}

#[tauri::command]
pub async fn delete_member(state: State<'_, AppState>, id: String) -> Result<(), AppError> {
    member_service::delete_member(&state.db, &id).await
}
