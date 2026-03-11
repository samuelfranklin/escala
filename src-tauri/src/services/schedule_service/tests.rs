use super::{allocation, constraints};
use crate::models::settings::ScheduleConfig;
use std::collections::{HashMap, HashSet};

/// Helper que compõe constraints + allocation para simular uma alocação completa.
/// Reproduz o fluxo de produção: build_unavailable → rank_candidates → allocate_top.
fn select_members(
    candidates: &[String],
    count_map: &HashMap<String, i64>,
    couple_map: &HashMap<String, HashSet<String>>,
    globally_allocated: &HashSet<String>,
    unavailable: &HashSet<String>,
    days_idle_map: &HashMap<String, i64>,
    monthly_count_map: &HashMap<String, i64>,
    max: usize,
) -> Vec<String> {
    select_members_for_date(
        candidates, count_map, couple_map, globally_allocated,
        unavailable, days_idle_map, monthly_count_map, max, "2026-03-01",
    )
}

/// Versão com data parametrizável para testar hash tiebreak.
fn select_members_for_date(
    candidates: &[String],
    count_map: &HashMap<String, i64>,
    couple_map: &HashMap<String, HashSet<String>>,
    globally_allocated: &HashSet<String>,
    unavailable: &HashSet<String>,
    days_idle_map: &HashMap<String, i64>,
    monthly_count_map: &HashMap<String, i64>,
    max: usize,
    occurrence_date: &str,
) -> Vec<String> {
    let config = ScheduleConfig::default();
    let effective_unavailable = constraints::build_unavailable(
        unavailable.clone(), monthly_count_map, couple_map, &config,
    );
    let ranked = allocation::rank_candidates(
        candidates, &effective_unavailable, count_map, days_idle_map, monthly_count_map, &config, occurrence_date,
    );
    allocation::allocate_top(&ranked, globally_allocated, max)
}

// ── Rotação ──

#[test]
fn test_rotation_prioritizes_less_scheduled() {
    let candidates = vec!["a".into(), "b".into(), "c".into()];
    let mut counts = HashMap::new();
    counts.insert("a".into(), 5i64);
    counts.insert("b".into(), 2i64);
    counts.insert("c".into(), 8i64);
    let result = select_members(&candidates, &counts, &HashMap::new(), &HashSet::new(), &HashSet::new(), &HashMap::new(), &HashMap::new(), 2);
    assert_eq!(result, vec!["b", "a"]);
}

// ── Casais ──

#[test]
fn test_couple_same_squad_both_available() {
    let candidates = vec!["a".into(), "b".into(), "c".into()];
    let mut couples: HashMap<String, HashSet<String>> = HashMap::new();
    couples.entry("a".into()).or_default().insert("b".into());
    couples.entry("b".into()).or_default().insert("a".into());
    let result = select_members(&candidates, &HashMap::new(), &couples, &HashSet::new(), &HashSet::new(), &HashMap::new(), &HashMap::new(), 3);
    assert!(result.contains(&"a".to_string()));
    assert!(result.contains(&"b".to_string()));
}

#[test]
fn test_couple_partner_in_different_squad_not_blocked() {
    let candidates = vec!["a".into(), "c".into()];
    let mut couples: HashMap<String, HashSet<String>> = HashMap::new();
    couples.entry("a".into()).or_default().insert("b".into());
    couples.entry("b".into()).or_default().insert("a".into());
    let result = select_members(&candidates, &HashMap::new(), &couples, &HashSet::new(), &HashSet::new(), &HashMap::new(), &HashMap::new(), 2);
    assert!(result.contains(&"a".to_string()));
    assert!(result.contains(&"c".to_string()));
}

#[test]
fn test_couple_one_unavailable_propagates() {
    let candidates = vec!["a".into(), "c".into()];
    let mut couples: HashMap<String, HashSet<String>> = HashMap::new();
    couples.entry("a".into()).or_default().insert("b".into());
    couples.entry("b".into()).or_default().insert("a".into());
    let mut unavailable = HashSet::new();
    unavailable.insert("b".to_string());
    let result = select_members(&candidates, &HashMap::new(), &couples, &HashSet::new(), &unavailable, &HashMap::new(), &HashMap::new(), 3);
    assert!(!result.contains(&"a".to_string()));
    assert!(result.contains(&"c".to_string()));
}

// ── Alocação multi-round ──

#[test]
fn test_count_map_updated_between_occurrences() {
    let candidates = vec!["a".into(), "b".into(), "c".into(), "d".into()];
    let mut count_map: HashMap<String, i64> = HashMap::new();
    let mut all_chosen: Vec<String> = Vec::new();
    for _ in 0..4 {
        let selected = select_members(&candidates, &count_map, &HashMap::new(), &HashSet::new(), &HashSet::new(), &HashMap::new(), &HashMap::new(), 1);
        assert_eq!(selected.len(), 1);
        let chosen = selected[0].clone();
        *count_map.entry(chosen.clone()).or_insert(0) += 1;
        all_chosen.push(chosen);
    }
    for member in &["a", "b", "c", "d"] {
        assert_eq!(all_chosen.iter().filter(|r| r.as_str() == *member).count(), 1);
    }
}

#[test]
fn test_max_members_respected() {
    let candidates = vec!["a".into(), "b".into(), "c".into(), "d".into()];
    let result = select_members(&candidates, &HashMap::new(), &HashMap::new(), &HashSet::new(), &HashSet::new(), &HashMap::new(), &HashMap::new(), 2);
    assert_eq!(result.len(), 2);
}

// ── Limite mensal ──

#[test]
fn test_monthly_limit_excludes_member() {
    let candidates = vec!["a".into(), "b".into(), "c".into()];
    let mut monthly = HashMap::new();
    monthly.insert("a".into(), 2i64);
    let result = select_members(
        &candidates, &HashMap::new(), &HashMap::new(),
        &HashSet::new(), &HashSet::new(), &HashMap::new(), &monthly, 3,
    );
    assert!(!result.contains(&"a".to_string()));
    assert!(result.contains(&"b".to_string()));
    assert!(result.contains(&"c".to_string()));
}

#[test]
fn test_monthly_limit_blocks_couple_partner() {
    let candidates = vec!["a".into(), "b".into(), "c".into()];
    let mut couples: HashMap<String, HashSet<String>> = HashMap::new();
    couples.entry("a".into()).or_default().insert("b".into());
    couples.entry("b".into()).or_default().insert("a".into());
    let mut monthly = HashMap::new();
    monthly.insert("a".into(), 2i64);
    let result = select_members(
        &candidates, &HashMap::new(), &couples,
        &HashSet::new(), &HashSet::new(), &HashMap::new(), &monthly, 3,
    );
    assert!(!result.contains(&"a".to_string()));
    assert!(!result.contains(&"b".to_string()));
    assert!(result.contains(&"c".to_string()));
}

#[test]
fn test_monthly_limit_enough_members() {
    let candidates = vec!["a".into(), "b".into(), "c".into(), "d".into()];
    let mut monthly_count: HashMap<String, i64> = HashMap::new();
    let mut appearances: HashMap<String, usize> = HashMap::new();
    for _ in 0..4 {
        let selected = select_members(
            &candidates, &HashMap::new(), &HashMap::new(),
            &HashSet::new(), &HashSet::new(), &HashMap::new(), &monthly_count, 2,
        );
        assert_eq!(selected.len(), 2);
        for m in &selected {
            *monthly_count.entry(m.clone()).or_insert(0) += 1;
            *appearances.entry(m.clone()).or_insert(0) += 1;
        }
    }
    for member in &["a", "b", "c", "d"] {
        assert_eq!(*appearances.get(*member).unwrap_or(&0), 2);
    }
}

// ── Scoring integrado ──

#[test]
fn test_score_recent_vs_old() {
    let candidates = vec!["a".into(), "b".into()];
    let mut counts = HashMap::new();
    counts.insert("a".into(), 3i64);
    counts.insert("b".into(), 3i64);
    let mut idle = HashMap::new();
    idle.insert("a".into(), 1i64);
    idle.insert("b".into(), 60i64);
    let result = select_members(&candidates, &counts, &HashMap::new(), &HashSet::new(), &HashSet::new(), &idle, &HashMap::new(), 2);
    assert_eq!(result[0], "b");
}

#[test]
fn test_score_monthly_count_penalty() {
    let candidates = vec!["a".into(), "b".into()];
    let mut counts = HashMap::new();
    counts.insert("a".into(), 1i64);
    counts.insert("b".into(), 1i64);
    let mut idle = HashMap::new();
    idle.insert("a".into(), 10i64);
    idle.insert("b".into(), 10i64);
    let mut monthly = HashMap::new();
    monthly.insert("a".into(), 2i64);
    let result = select_members(&candidates, &counts, &HashMap::new(), &HashSet::new(), &HashSet::new(), &idle, &monthly, 2);
    assert_eq!(result[0], "b");
}

#[test]
fn test_score_combined() {
    let candidates = vec!["m1".into(), "m2".into(), "m3".into()];
    let mut counts = HashMap::new();
    counts.insert("m1".into(), 5i64);
    counts.insert("m2".into(), 2i64);
    counts.insert("m3".into(), 0i64);
    let mut idle = HashMap::new();
    idle.insert("m1".into(), 100i64);
    idle.insert("m2".into(), 10i64);
    idle.insert("m3".into(), 5i64);
    let mut monthly = HashMap::new();
    monthly.insert("m1".into(), 1i64); 
    monthly.insert("m3".into(), 1i64);
    let result = select_members(&candidates, &counts, &HashMap::new(), &HashSet::new(), &HashSet::new(), &idle, &monthly, 3);
    // Prioridade: mensal primeiro (m2=0 < m1=m3=1), depois idle (m1=100 > m3=5)
    assert_eq!(result, vec!["m2", "m1", "m3"]);
}

// ── Regressão: idle não domina após primeira alocação ──

#[test]
fn test_idle_does_not_dominate_second_event_after_first_allocation() {
    let candidates = vec!["m1".into(), "m2".into()];
    let counts: HashMap<String, i64> = HashMap::new(); 
    let mut idle = HashMap::new();
    idle.insert("m1".into(), 9999i64); 
    idle.insert("m2".into(), 2i64);    

    let round1 = select_members(&candidates, &counts, &HashMap::new(), &HashSet::new(), &HashSet::new(), &idle, &HashMap::new(), 1);
    assert_eq!(round1, vec!["m1"]);

    let mut idle3 = idle.clone();
    idle3.insert("m1".into(), 2i64); 
    
    let mut monthly2 = HashMap::new();
    monthly2.insert("m1".into(), 1i64);

    let round3 = select_members(&candidates, &counts, &HashMap::new(), &HashSet::new(), &HashSet::new(), &idle3, &monthly2, 1);
    assert_eq!(round3, vec!["m2"]);
}

// ── Integration tests with SQLite in-memory ──

mod integration {
    use crate::{
        models::{
            event::{CreateEventDto, EventSquadDto},
            member::CreateMemberDto,
            schedule::MonthScheduleView,
        },
        services::{
            event_service, member_service, schedule_service, squad_service,
            couple_service, availability_service, settings_service,
        },
        models::couple::CreateCoupleDto,
        models::availability::CreateAvailabilityDto,
        models::settings::UpdateScheduleConfigDto,
        models::squad::CreateSquadDto,
    };
    use sqlx::SqlitePool;

    async fn setup_pool() -> SqlitePool {
        let pool = SqlitePool::connect(":memory:").await.unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();
        pool
    }

    async fn create_member(pool: &SqlitePool, name: &str) -> String {
        member_service::create_member(pool, CreateMemberDto {
            name: name.into(), email: None, phone: None, instagram: None, rank: None,
        }).await.unwrap().id
    }

    async fn create_squad(pool: &SqlitePool, name: &str) -> String {
        squad_service::create_squad(pool, CreateSquadDto {
            name: name.into(), description: None,
        }).await.unwrap().id
    }

    async fn create_regular_event(pool: &SqlitePool, name: &str, dow: i64, rec: &str) -> String {
        event_service::create_event(pool, CreateEventDto {
            name: name.into(), event_date: None, event_type: Some("regular".into()),
            day_of_week: Some(dow), recurrence: Some(rec.into()), notes: None,
        }).await.unwrap().id
    }

    async fn create_special_event(pool: &SqlitePool, name: &str, date: &str) -> String {
        event_service::create_event(pool, CreateEventDto {
            name: name.into(), event_date: Some(date.into()), event_type: Some("special".into()),
            day_of_week: None, recurrence: None, notes: None,
        }).await.unwrap().id
    }

    async fn setup_squad_with_members(pool: &SqlitePool, squad_name: &str, member_names: &[&str]) -> (String, Vec<String>) {
        let squad_id = create_squad(pool, squad_name).await;
        let mut member_ids = Vec::new();
        for name in member_names {
            let id = create_member(pool, name).await;
            squad_service::add_member_to_squad(pool, &squad_id, &id, "member").await.unwrap();
            member_ids.push(id);
        }
        (squad_id, member_ids)
    }

    // ── generate_schedule (single event) ──

    #[tokio::test]
    async fn test_generate_schedule_special_event() {
        let pool = setup_pool().await;
        let (squad_id, _members) = setup_squad_with_members(&pool, "Câmera", &["Alice", "Bob", "Carol"]).await;
        let event_id = create_special_event(&pool, "Culto Especial", "2026-03-08").await;

        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id, min_members: 1, max_members: 2 },
        ]).await.unwrap();

        let result = schedule_service::generate_schedule(&pool, &event_id).await.unwrap();
        assert_eq!(result.event_id, event_id);
        assert_eq!(result.entries.len(), 2);
    }

    #[tokio::test]
    async fn test_generate_schedule_no_squads_fails() {
        let pool = setup_pool().await;
        let event_id = create_special_event(&pool, "Culto Vazio", "2026-03-08").await;
        let err = schedule_service::generate_schedule(&pool, &event_id).await;
        assert!(matches!(err, Err(crate::errors::AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_generate_schedule_regular_event_fails() {
        let pool = setup_pool().await;
        let event_id = create_regular_event(&pool, "Culto Regular", 0, "weekly").await;
        let err = schedule_service::generate_schedule(&pool, &event_id).await;
        assert!(matches!(err, Err(crate::errors::AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_generate_schedule_not_enough_members() {
        let pool = setup_pool().await;
        let (squad_id, _) = setup_squad_with_members(&pool, "Câmera", &["Alice"]).await;
        let event_id = create_special_event(&pool, "Culto", "2026-03-08").await;

        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id, min_members: 3, max_members: 3 },
        ]).await.unwrap();

        let err = schedule_service::generate_schedule(&pool, &event_id).await;
        assert!(matches!(err, Err(crate::errors::AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_generate_schedule_nonexistent_event() {
        let pool = setup_pool().await;
        let err = schedule_service::generate_schedule(&pool, "nonexistent").await;
        assert!(matches!(err, Err(crate::errors::AppError::NotFound(_))));
    }

    // ── get_schedule / clear_schedule ──

    #[tokio::test]
    async fn test_get_and_clear_schedule() {
        let pool = setup_pool().await;
        let (squad_id, _) = setup_squad_with_members(&pool, "Câmera", &["Alice", "Bob"]).await;
        let event_id = create_special_event(&pool, "Culto", "2026-03-08").await;

        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id, min_members: 1, max_members: 1 },
        ]).await.unwrap();

        schedule_service::generate_schedule(&pool, &event_id).await.unwrap();

        let view = schedule_service::get_schedule(&pool, &event_id).await.unwrap();
        assert_eq!(view.entries.len(), 1);

        schedule_service::clear_schedule(&pool, &event_id).await.unwrap();
        let view = schedule_service::get_schedule(&pool, &event_id).await.unwrap();
        assert!(view.entries.is_empty());
    }

    // ── generate_month_schedule ──

    #[tokio::test]
    async fn test_generate_month_schedule_regular_events() {
        let pool = setup_pool().await;
        let (squad_id, _) = setup_squad_with_members(
            &pool, "Câmera", &["M1", "M2", "M3", "M4", "M5", "M6"],
        ).await;

        // Sunday weekly event (dow=0)
        let event_id = create_regular_event(&pool, "Culto Domingo", 0, "weekly").await;
        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id, min_members: 1, max_members: 1 },
        ]).await.unwrap();

        let result = schedule_service::generate_month_schedule(&pool, "2026-03").await.unwrap();
        assert_eq!(result.month, "2026-03");
        // March 2026 has 5 Sundays (1, 8, 15, 22, 29)
        assert_eq!(result.occurrences.len(), 5);
        for occ in &result.occurrences {
            assert_eq!(occ.entries.len(), 1);
        }
    }

    #[tokio::test]
    async fn test_generate_month_schedule_special_event_included() {
        let pool = setup_pool().await;
        let (squad_id, _) = setup_squad_with_members(&pool, "Câmera", &["Alice", "Bob"]).await;

        let event_id = create_special_event(&pool, "Congresso", "2026-04-10").await;
        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id, min_members: 1, max_members: 1 },
        ]).await.unwrap();

        let result = schedule_service::generate_month_schedule(&pool, "2026-04").await.unwrap();
        assert_eq!(result.occurrences.len(), 1);
        assert_eq!(result.occurrences[0].occurrence_date, "2026-04-10");
    }

    #[tokio::test]
    async fn test_generate_month_schedule_empty_month() {
        let pool = setup_pool().await;
        let result = schedule_service::generate_month_schedule(&pool, "2026-06").await.unwrap();
        assert!(result.occurrences.is_empty());
    }

    #[tokio::test]
    async fn test_get_and_clear_month_schedule() {
        let pool = setup_pool().await;
        let (squad_id, _) = setup_squad_with_members(&pool, "Câmera", &["Alice", "Bob"]).await;

        let event_id = create_special_event(&pool, "Congresso", "2026-05-10").await;
        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id, min_members: 1, max_members: 1 },
        ]).await.unwrap();

        schedule_service::generate_month_schedule(&pool, "2026-05").await.unwrap();

        let view = schedule_service::get_month_schedule(&pool, "2026-05").await.unwrap();
        assert_eq!(view.occurrences.len(), 1);

        schedule_service::clear_month_schedule(&pool, "2026-05").await.unwrap();
        let view = schedule_service::get_month_schedule(&pool, "2026-05").await.unwrap();
        assert!(view.occurrences.is_empty());
    }

    #[tokio::test]
    async fn test_parse_month_invalid_format() {
        let pool = setup_pool().await;
        let err = schedule_service::generate_month_schedule(&pool, "invalid").await;
        assert!(matches!(err, Err(crate::errors::AppError::Validation(_))));
    }

    #[tokio::test]
    async fn test_generate_month_with_availability_constraint() {
        let pool = setup_pool().await;
        let (squad_id, members) = setup_squad_with_members(&pool, "Câmera", &["Alice", "Bob"]).await;

        let event_id = create_special_event(&pool, "Culto", "2026-07-10").await;
        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id, min_members: 1, max_members: 1 },
        ]).await.unwrap();

        // Mark Alice unavailable on that date
        availability_service::create_availability(&pool, CreateAvailabilityDto {
            member_id: members[0].clone(), unavailable_date: "2026-07-10".into(), reason: None,
        }).await.unwrap();

        let result = schedule_service::generate_month_schedule(&pool, "2026-07").await.unwrap();
        assert_eq!(result.occurrences.len(), 1);
        // Should be Bob since Alice is unavailable
        assert_eq!(result.occurrences[0].entries[0].member_name, "Bob");
    }

    #[tokio::test]
    async fn test_generate_schedule_with_two_squads() {
        let pool = setup_pool().await;
        let (sq1, _) = setup_squad_with_members(&pool, "Câmera", &["Alice", "Bob"]).await;
        let (sq2, _) = setup_squad_with_members(&pool, "Som", &["Carol", "Dave"]).await;

        let event_id = create_special_event(&pool, "Culto", "2026-08-01").await;
        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id: sq1, min_members: 1, max_members: 1 },
            EventSquadDto { squad_id: sq2, min_members: 1, max_members: 1 },
        ]).await.unwrap();

        let result = schedule_service::generate_schedule(&pool, &event_id).await.unwrap();
        assert_eq!(result.entries.len(), 2);
    }

    #[tokio::test]
    async fn test_generate_month_skips_event_without_squads() {
        let pool = setup_pool().await;
        // Event with no squads configured → should be skipped
        create_special_event(&pool, "Vazio", "2026-09-01").await;

        let result = schedule_service::generate_month_schedule(&pool, "2026-09").await.unwrap();
        // No failures — just empty because the only event has no squads
        assert!(result.occurrences.is_empty());
    }

    #[tokio::test]
    async fn test_generate_month_with_biweekly_event() {
        let pool = setup_pool().await;
        let (squad_id, _) = setup_squad_with_members(&pool, "Câmera", &["A", "B", "C", "D"]).await;

        // Wednesday biweekly (dow=3)
        let event_id = create_regular_event(&pool, "Célula", 3, "biweekly").await;
        event_service::set_event_squads(&pool, &event_id, vec![
            EventSquadDto { squad_id, min_members: 1, max_members: 1 },
        ]).await.unwrap();

        let result = schedule_service::generate_month_schedule(&pool, "2026-03").await.unwrap();
        // March 2026 Wednesdays: 4, 11, 18, 25 → biweekly = 4, 18 (2 occurrences)
        assert_eq!(result.occurrences.len(), 2);
    }

    // ── Error types coverage ──

    #[tokio::test]
    async fn test_error_display() {
        use crate::errors::AppError;
        let err = AppError::NotFound("test".into());
        assert_eq!(format!("{}", err), "Not found: test");
        let err = AppError::Validation("bad".into());
        assert_eq!(format!("{}", err), "Validation error: bad");
        let err = AppError::Conflict("dup".into());
        assert_eq!(format!("{}", err), "Conflict: dup");
        let err = AppError::Database("db".into());
        assert_eq!(format!("{}", err), "Database error: db");
        let err = AppError::Internal("oops".into());
        assert_eq!(format!("{}", err), "Internal error: oops");
    }

    #[tokio::test]
    async fn test_sqlx_error_conversion() {
        use crate::errors::AppError;
        let err: AppError = sqlx::Error::RowNotFound.into();
        assert!(matches!(err, AppError::NotFound(_)));
    }
}
