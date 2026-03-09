pub mod commands;
pub mod db;
pub mod errors;
pub mod models;
pub mod services;

use sqlx::{sqlite::SqliteConnectOptions, sqlite::SqlitePoolOptions, SqlitePool};
use std::str::FromStr;
use tauri::Manager;
use tauri_plugin_log::{Target, TargetKind};

pub struct AppState {
    pub db: SqlitePool,
}

async fn create_db_pool(db_url: &str) -> SqlitePool {
    log::info!("Conectando ao banco: {}", db_url);
    let opts = SqliteConnectOptions::from_str(db_url)
        .expect("Invalid DATABASE_URL")
        .create_if_missing(true);

    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect_with(opts)
        .await
        .expect("Failed to connect to SQLite database");

    log::info!("Executando migrations...");
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .expect("Failed to run database migrations");

    log::info!("Banco pronto.");
    pool
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(
            tauri_plugin_log::Builder::new()
                .targets([
                    Target::new(TargetKind::Stdout),
                    Target::new(TargetKind::LogDir { file_name: None }),
                    Target::new(TargetKind::Webview),
                ])
                .level(log::LevelFilter::Info)
                .build(),
        )
        .setup(|app| {
            // Resolve database path: env var takes priority (CI/dev),
            // otherwise use Tauri's app data directory.
            let db_url = if let Ok(url) = std::env::var("DATABASE_URL") {
                url
            } else {
                let data_dir = app.path().app_data_dir()
                    .expect("Failed to resolve app data directory");
                std::fs::create_dir_all(&data_dir)
                    .expect("Failed to create app data directory");
                format!("sqlite://{}", data_dir.join("escala.db").display())
            };

            let rt = tokio::runtime::Runtime::new().expect("Failed to create tokio runtime");
            let pool = rt.block_on(create_db_pool(&db_url));
            app.manage(AppState { db: pool });
            Ok(())
        })
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
            commands::event::get_event_squads,
            commands::event::set_event_squads,
            // Schedule
            commands::schedule::get_schedule,
            commands::schedule::generate_schedule,
            commands::schedule::clear_schedule,
            commands::schedule::get_month_schedule,
            commands::schedule::generate_month_schedule,
            commands::schedule::clear_month_schedule,
            // Couple
            commands::couple::get_couples,
            commands::couple::create_couple,
            commands::couple::delete_couple,
            // Availability
            commands::availability::get_availability,
            commands::availability::create_availability,
            commands::availability::delete_availability,
            // Settings
            commands::settings::get_schedule_config,
            commands::settings::update_schedule_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
