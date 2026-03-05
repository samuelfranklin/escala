pub mod commands;
pub mod db;
pub mod errors;
pub mod models;
pub mod services;

use sqlx::SqlitePool;

pub struct AppState {
    pub db: SqlitePool,
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            // Member
            commands::member::get_members,
            commands::member::get_member,
            commands::member::create_member,
            commands::member::update_member,
            commands::member::delete_member,
            // Squad
            commands::squad::get_squads,
            commands::squad::get_squad,
            commands::squad::create_squad,
            commands::squad::update_squad,
            commands::squad::delete_squad,
            commands::squad::get_squad_members,
            commands::squad::add_member_to_squad,
            commands::squad::remove_member_from_squad,
            // Event
            commands::event::get_events,
            commands::event::get_event,
            commands::event::create_event,
            commands::event::update_event,
            commands::event::delete_event,
            // Schedule
            commands::schedule::get_schedule,
            commands::schedule::generate_schedule,
            commands::schedule::clear_schedule,
            // Couple
            commands::couple::get_couples,
            commands::couple::create_couple,
            commands::couple::delete_couple,
            // Availability
            commands::availability::get_availability,
            commands::availability::create_availability,
            commands::availability::delete_availability,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
