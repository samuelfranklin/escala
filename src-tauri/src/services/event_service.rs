use crate::{db::event_repo, errors::AppError, models::event::{CreateEventDto, Event, EventSquad, EventSquadDto, UpdateEventDto}};
use sqlx::SqlitePool;

pub async fn list_events(pool: &SqlitePool) -> Result<Vec<Event>, AppError> { event_repo::list_all(pool).await }
pub async fn get_event(pool: &SqlitePool, id: &str) -> Result<Event, AppError> { event_repo::get_by_id(pool, id).await }

pub async fn create_event(pool: &SqlitePool, dto: CreateEventDto) -> Result<Event, AppError> {
    if dto.name.trim().is_empty() { return Err(AppError::Validation("Name cannot be empty".into())); }
    if dto.event_date.trim().is_empty() { return Err(AppError::Validation("Event date cannot be empty".into())); }
    event_repo::create(pool, dto).await
}

pub async fn update_event(pool: &SqlitePool, id: &str, dto: UpdateEventDto) -> Result<Event, AppError> {
    if let Some(ref name) = dto.name { if name.trim().is_empty() { return Err(AppError::Validation("Name cannot be empty".into())); } }
    event_repo::update(pool, id, dto).await
}

pub async fn delete_event(pool: &SqlitePool, id: &str) -> Result<(), AppError> { event_repo::delete(pool, id).await }

pub async fn get_event_squads(pool: &SqlitePool, event_id: &str) -> Result<Vec<EventSquad>, AppError> {
    event_repo::get_event_squads(pool, event_id).await
}

pub async fn set_event_squads(pool: &SqlitePool, event_id: &str, items: Vec<EventSquadDto>) -> Result<Vec<EventSquad>, AppError> {
    for item in &items {
        if item.min_members < 1 {
            return Err(AppError::Validation(format!("min_members must be >= 1 (got {})", item.min_members)));
        }
        if item.max_members < item.min_members {
            return Err(AppError::Validation(format!(
                "max_members ({}) must be >= min_members ({})", item.max_members, item.min_members
            )));
        }
        if item.max_members > 10 {
            return Err(AppError::Validation(format!("max_members must be <= 10 (got {})", item.max_members)));
        }
    }
    // Verifica se o evento existe
    event_repo::get_by_id(pool, event_id).await?;
    event_repo::set_event_squads(pool, event_id, &items).await?;
    event_repo::get_event_squads(pool, event_id).await
}

#[cfg(test)]
mod tests {
    use super::*;
    use sqlx::SqlitePool;

    async fn setup_pool() -> SqlitePool {
        let pool = SqlitePool::connect(":memory:").await.unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();
        pool
    }

    async fn create_test_event(pool: &SqlitePool) -> Event {
        create_event(pool, CreateEventDto {
            name: "Culto Teste".into(),
            event_date: "2026-03-08".into(),
            event_type: None,
            notes: None,
        }).await.unwrap()
    }

    async fn create_test_squad(pool: &SqlitePool, name: &str) -> String {
        let id = uuid::Uuid::new_v4().to_string().replace('-', "");
        sqlx::query("INSERT INTO squads (id, name) VALUES (?, ?)")
            .bind(&id).bind(name)
            .execute(pool).await.unwrap();
        id
    }

    #[tokio::test]
    async fn test_set_and_get_event_squads_roundtrip() {
        let pool = setup_pool().await;
        let event = create_test_event(&pool).await;
        let squad_id = create_test_squad(&pool, "Câmera").await;

        let result = set_event_squads(&pool, &event.id, vec![
            EventSquadDto { squad_id: squad_id.clone(), min_members: 1, max_members: 3 },
        ]).await.unwrap();

        assert_eq!(result.len(), 1);
        assert_eq!(result[0].squad_id, squad_id);
        assert_eq!(result[0].squad_name, "Câmera");
        assert_eq!(result[0].min_members, 1);
        assert_eq!(result[0].max_members, 3);
    }

    #[tokio::test]
    async fn test_set_event_squads_replaces_previous() {
        let pool = setup_pool().await;
        let event = create_test_event(&pool).await;
        let sq1 = create_test_squad(&pool, "Câmera").await;
        let sq2 = create_test_squad(&pool, "Áudio").await;

        set_event_squads(&pool, &event.id, vec![
            EventSquadDto { squad_id: sq1.clone(), min_members: 1, max_members: 2 },
        ]).await.unwrap();

        let result = set_event_squads(&pool, &event.id, vec![
            EventSquadDto { squad_id: sq2.clone(), min_members: 2, max_members: 4 },
        ]).await.unwrap();

        assert_eq!(result.len(), 1);
        assert_eq!(result[0].squad_id, sq2);
    }

    #[tokio::test]
    async fn test_set_event_squads_empty_clears_all() {
        let pool = setup_pool().await;
        let event = create_test_event(&pool).await;
        let squad_id = create_test_squad(&pool, "Câmera").await;

        set_event_squads(&pool, &event.id, vec![
            EventSquadDto { squad_id: squad_id.clone(), min_members: 1, max_members: 3 },
        ]).await.unwrap();

        let result = set_event_squads(&pool, &event.id, vec![]).await.unwrap();
        assert_eq!(result.len(), 0);
    }

    #[tokio::test]
    async fn test_set_event_squads_validates_min_members() {
        let pool = setup_pool().await;
        let event = create_test_event(&pool).await;
        let squad_id = create_test_squad(&pool, "Câmera").await;

        let err = set_event_squads(&pool, &event.id, vec![
            EventSquadDto { squad_id, min_members: 0, max_members: 3 },
        ]).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_set_event_squads_validates_max_lt_min() {
        let pool = setup_pool().await;
        let event = create_test_event(&pool).await;
        let squad_id = create_test_squad(&pool, "Câmera").await;

        let err = set_event_squads(&pool, &event.id, vec![
            EventSquadDto { squad_id, min_members: 3, max_members: 1 },
        ]).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }
}
