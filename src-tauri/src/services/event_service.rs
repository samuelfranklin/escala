use crate::{db::event_repo, errors::AppError, models::event::{CreateEventDto, Event, EventSquad, EventSquadDto, UpdateEventDto}};
use sqlx::SqlitePool;

pub async fn list_events(pool: &SqlitePool) -> Result<Vec<Event>, AppError> { event_repo::list_all(pool).await }
pub async fn get_event(pool: &SqlitePool, id: &str) -> Result<Event, AppError> { event_repo::get_by_id(pool, id).await }

pub async fn create_event(pool: &SqlitePool, dto: CreateEventDto) -> Result<Event, AppError> {
    if dto.name.trim().is_empty() { return Err(AppError::Validation("Name cannot be empty".into())); }
    let event_type = dto.event_type.as_deref().unwrap_or("regular");
    if event_type == "regular" {
        if dto.day_of_week.is_none() { return Err(AppError::Validation("day_of_week is required for regular events".into())); }
        if dto.recurrence.is_none()  { return Err(AppError::Validation("recurrence is required for regular events".into())); }
    } else if dto.event_date.as_deref().map(|d| d.trim().is_empty()).unwrap_or(true) {
        return Err(AppError::Validation("event_date is required for special/training events".into()));
    }
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
            event_date: Some("2026-03-08".into()),
            event_type: Some("special".into()),
            day_of_week: None,
            recurrence: None,
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

    #[tokio::test]
    async fn test_set_event_squads_validates_max_gt_10() {
        let pool = setup_pool().await;
        let event = create_test_event(&pool).await;
        let squad_id = create_test_squad(&pool, "Câmera").await;

        let err = set_event_squads(&pool, &event.id, vec![
            EventSquadDto { squad_id, min_members: 1, max_members: 11 },
        ]).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_crud_full_cycle() {
        let pool = setup_pool().await;

        // Create regular
        let event = create_event(&pool, CreateEventDto {
            name: "Culto Domingo".into(), event_date: None,
            event_type: Some("regular".into()),
            day_of_week: Some(0), recurrence: Some("weekly".into()), notes: None,
        }).await.unwrap();
        assert_eq!(event.name, "Culto Domingo");
        assert_eq!(event.event_type, "regular");

        // List
        let all = list_events(&pool).await.unwrap();
        assert_eq!(all.len(), 1);

        // Get
        let fetched = get_event(&pool, &event.id).await.unwrap();
        assert_eq!(fetched.id, event.id);

        // Update
        let updated = update_event(&pool, &event.id, UpdateEventDto {
            name: Some("Culto Atualizado".into()), event_date: None,
            event_type: None, day_of_week: None, recurrence: None, notes: Some("nota".into()),
        }).await.unwrap();
        assert_eq!(updated.name, "Culto Atualizado");

        // Update empty name fails
        let err = update_event(&pool, &event.id, UpdateEventDto {
            name: Some("  ".into()), event_date: None,
            event_type: None, day_of_week: None, recurrence: None, notes: None,
        }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));

        // Delete
        delete_event(&pool, &event.id).await.unwrap();
        assert!(list_events(&pool).await.unwrap().is_empty());
    }

    #[tokio::test]
    async fn test_create_empty_name_fails() {
        let pool = setup_pool().await;
        let err = create_event(&pool, CreateEventDto {
            name: "  ".into(), event_date: None,
            event_type: Some("regular".into()),
            day_of_week: Some(0), recurrence: Some("weekly".into()), notes: None,
        }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_create_regular_without_day_of_week_fails() {
        let pool = setup_pool().await;
        let err = create_event(&pool, CreateEventDto {
            name: "Culto".into(), event_date: None,
            event_type: Some("regular".into()),
            day_of_week: None, recurrence: Some("weekly".into()), notes: None,
        }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_create_regular_without_recurrence_fails() {
        let pool = setup_pool().await;
        let err = create_event(&pool, CreateEventDto {
            name: "Culto".into(), event_date: None,
            event_type: Some("regular".into()),
            day_of_week: Some(0), recurrence: None, notes: None,
        }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_create_special_without_date_fails() {
        let pool = setup_pool().await;
        let err = create_event(&pool, CreateEventDto {
            name: "Congresso".into(), event_date: None,
            event_type: Some("special".into()),
            day_of_week: None, recurrence: None, notes: None,
        }).await;
        assert!(matches!(err, Err(AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_delete_nonexistent_event() {
        let pool = setup_pool().await;
        let err = delete_event(&pool, "nonexistent").await;
        assert!(matches!(err, Err(AppError::NotFound(_))));
    }

    #[tokio::test]
    async fn test_get_event_squads_empty() {
        let pool = setup_pool().await;
        let event = create_test_event(&pool).await;
        let squads = get_event_squads(&pool, &event.id).await.unwrap();
        assert!(squads.is_empty());
    }
}
