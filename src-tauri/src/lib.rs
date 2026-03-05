pub mod commands;
pub mod db;
pub mod errors;
pub mod models;
pub mod services;

use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};

pub struct AppState {
    pub db: SqlitePool,
}

async fn create_db_pool() -> SqlitePool {
    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "sqlite://escala.db".to_string());

    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await
        .expect("Failed to connect to SQLite database");

    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .expect("Failed to run database migrations");

    pool
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let rt = tokio::runtime::Runtime::new().expect("Failed to create tokio runtime");
    let pool = rt.block_on(create_db_pool());

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(AppState { db: pool })
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
