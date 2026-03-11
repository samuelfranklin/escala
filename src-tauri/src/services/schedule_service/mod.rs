//! Schedule generator — orquestra módulos de domínio + repositório.
//!
//! Responsabilidades deste arquivo:
//! - Buscar dados via `schedule_repo`
//! - Compor constraints, scoring e allocation
//! - Logging de diagnóstico
//!
//! Nenhuma query SQL vive aqui — todas estão em `db::schedule_repo`.

mod allocation;
mod constraints;
mod recurrence;
mod scoring;

use crate::{
    db::{schedule_repo, settings_repo},
    errors::AppError,
    models::schedule::{MonthScheduleView, ScheduleView},
    models::settings::ScheduleConfig,
};
use chrono::NaiveDate;
use log::{info, debug, warn};
use sqlx::SqlitePool;
use std::collections::{HashMap, HashSet};

use scoring::tiebreak_hash;
use recurrence::occurrence_dates;

// ── Leitura ──

pub async fn get_schedule(pool: &SqlitePool, event_id: &str) -> Result<ScheduleView, AppError> {
    schedule_repo::get_by_event(pool, event_id).await
}

pub async fn get_month_schedule(pool: &SqlitePool, month: &str) -> Result<MonthScheduleView, AppError> {
    schedule_repo::get_month_schedule(pool, month).await
}

// ── Geração: evento único ──

pub async fn generate_schedule(pool: &SqlitePool, event_id: &str) -> Result<ScheduleView, AppError> {
    info!("[generate_schedule] Iniciando para evento {}", event_id);

    // 1. Evento e validação
    let event = schedule_repo::fetch_event_basics(pool, event_id).await?
        .ok_or_else(|| AppError::NotFound(format!("Event '{}' not found", event_id)))?;

    let event_date = event.event_date.ok_or_else(|| {
        AppError::Validation("Eventos regulares (recorrentes) devem ser gerados pela escala mensal. Use 'Gerar Escala do Mês'.".into())
    })?;

    let event_squads = schedule_repo::fetch_event_squads(pool, event_id).await?;
    if event_squads.is_empty() {
        return Err(AppError::Validation("Event has no squads configured".into()));
    }

    // 2. Constraints
    let month = &event_date[..7];
    let base_unavailable = schedule_repo::fetch_unavailable_members(pool, &event_date).await?;
    let monthly_count_map = schedule_repo::fetch_monthly_counts(pool, month).await?;
    let couple_pairs = schedule_repo::fetch_couple_pairs(pool).await?;
    let couple_map = constraints::build_couple_map(&couple_pairs);

    let config = settings_repo::get_config(pool).await.unwrap_or_default();

    log_monthly_blocked(&monthly_count_map, "generate_schedule", None, &config);
    let unavailable = constraints::build_unavailable(base_unavailable, &monthly_count_map, &couple_map, &config);

    // 3. Scoring
    let historical_count_map = schedule_repo::fetch_historical_counts(pool, month).await?;
    let event_naive = NaiveDate::parse_from_str(&event_date, "%Y-%m-%d")
        .unwrap_or_else(|_| NaiveDate::from_ymd_opt(2000, 1, 1).unwrap());
    let last_dates = schedule_repo::fetch_last_dates_before(pool, &event_date).await?;
    let days_idle_map: HashMap<String, i64> = last_dates.into_iter()
        .map(|(id, last)| (id, (event_naive - last).num_days()))
        .collect();

    debug!("[generate_schedule] Indisponíveis: {:?}", unavailable);
    debug!("[generate_schedule] Histórico: {:?}", historical_count_map);
    debug!("[generate_schedule] Days idle: {:?}", days_idle_map);

    // 4. Alocação por squad
    schedule_repo::clear_event(pool, event_id).await?;
    let mut globally_allocated: HashSet<String> = HashSet::new();

    for es in &event_squads {
        let candidates = schedule_repo::fetch_squad_candidates(pool, &es.squad_id).await?;

        let ranked = allocation::rank_candidates(
            &candidates, &unavailable, &historical_count_map, &days_idle_map, &monthly_count_map, &config, &event_date,
        );
        log_candidate_ranking(
            &format!("[generate_schedule] Squad {} candidatos:", es.squad_id),
            &ranked, &monthly_count_map, &days_idle_map, &historical_count_map, &event_date,
        );

        let allocated = allocation::allocate_top(&ranked, &globally_allocated, es.max_members as usize);

        if (allocated.len() as i64) < es.min_members {
            return Err(AppError::Validation(format!(
                "Not enough available members for squad '{}' (need {}, got {})",
                es.squad_id, es.min_members, allocated.len()
            )));
        }

        for member_id in &allocated {
            globally_allocated.insert(member_id.clone());
            schedule_repo::insert_entry(pool, event_id, &es.squad_id, member_id).await?;
        }
        info!("[generate_schedule] Squad {} → alocados: {:?}", es.squad_id, allocated);
    }

    schedule_repo::get_by_event(pool, event_id).await
}

// ── Geração: mês inteiro ──

pub async fn generate_month_schedule(pool: &SqlitePool, month: &str) -> Result<MonthScheduleView, AppError> {
    info!("[generate_month] Iniciando geração para mês {}", month);
    let (year, month_num) = parse_month(month)?;

    // 1. Eventos → ocorrências
    let events = schedule_repo::fetch_all_events(pool).await?;

    let mut all_occurrences: Vec<(String, String, String)> = Vec::new();
    for ev in &events {
        if ev.event_type == "regular" {
            if let (Some(dow), Some(rec)) = (ev.day_of_week, &ev.recurrence) {
                for date in occurrence_dates(year, month_num, dow, rec) {
                    all_occurrences.push((ev.id.clone(), ev.name.clone(), date));
                }
            }
        } else if let Some(ref date) = ev.event_date {
            if date.starts_with(month) {
                all_occurrences.push((ev.id.clone(), ev.name.clone(), date.clone()));
            }
        }
    }

    all_occurrences.sort_by(|a, b| a.2.cmp(&b.2).then(a.1.cmp(&b.1)));

    info!("[generate_month] {} eventos carregados, {} ocorrências no mês", events.len(), all_occurrences.len());
    for (eid, ename, odate) in &all_occurrences {
        info!("[generate_month]   ocorrência: {} ({}) em {}", ename, eid, odate);
    }

    if all_occurrences.is_empty() {
        schedule_repo::clear_month(pool, month).await?;
        return Ok(MonthScheduleView { month: month.to_string(), occurrences: vec![] });
    }

    // 2. Dados compartilhados
    let config = settings_repo::get_config(pool).await.unwrap_or_default();
    let couple_pairs = schedule_repo::fetch_couple_pairs(pool).await?;
    let couple_map = constraints::build_couple_map(&couple_pairs);
    let historical_count_map = schedule_repo::fetch_historical_counts_with_nulls(pool, month).await?;
    let mut last_date_map = schedule_repo::fetch_last_dates_excluding_month(pool, month).await?;
    let mut monthly_count_map: HashMap<String, i64> = HashMap::new();

    // ── PHASE 1: Calcula todas as alocações em memória ──
    let mut allocations: Vec<(String, String, String, String)> = Vec::new();

    for (event_id, _, occurrence_date) in &all_occurrences {
        let event_squads = schedule_repo::fetch_event_squads(pool, event_id).await?;

        if event_squads.is_empty() {
            warn!("[generate_month] Evento {} sem squads configurados — pulando", event_id);
            continue;
        }

        let base_unavailable = schedule_repo::fetch_unavailable_members(pool, occurrence_date).await?;

        log_monthly_blocked(&monthly_count_map, "generate_month", Some(occurrence_date), &config);
        let unavailable = constraints::build_unavailable(base_unavailable, &monthly_count_map, &couple_map, &config);

        let occurrence_naive = NaiveDate::parse_from_str(occurrence_date, "%Y-%m-%d")
            .unwrap_or_else(|_| NaiveDate::from_ymd_opt(2000, 1, 1).unwrap());

        let mut globally_allocated: HashSet<String> = HashSet::new();

        for es in &event_squads {
            let candidates = schedule_repo::fetch_squad_candidates(pool, &es.squad_id).await?;

            let days_idle: HashMap<String, i64> = candidates.iter()
                .map(|id| {
                    let idle = last_date_map.get(id)
                        .map(|&last| (occurrence_naive - last).num_days())
                        .unwrap_or(9999);
                    (id.clone(), idle)
                })
                .collect();

            let ranked = allocation::rank_candidates(
                &candidates, &unavailable, &historical_count_map, &days_idle, &monthly_count_map, &config, occurrence_date,
            );
            log_candidate_ranking(
                &format!("[generate_month] {} em {} — Squad '{}' candidatos:", event_id, occurrence_date, es.squad_name),
                &ranked, &monthly_count_map, &days_idle, &historical_count_map, occurrence_date,
            );

            let allocated = allocation::allocate_top(&ranked, &globally_allocated, es.max_members as usize);

            if (allocated.len() as i64) < es.min_members {
                warn!(
                    "[generate_month] FALHA em '{}' em {} — time '{}': necessário {}, disponível {} após filtros. \
                     Candidatos totais: {}. Indisponíveis (data+limite+casal): {:?}. globally_allocated: {:?}.",
                    event_id, occurrence_date, es.squad_name,
                    es.min_members, allocated.len(),
                    candidates.len(),
                    unavailable,
                    globally_allocated,
                );
                return Err(AppError::Validation(format!(
                    "Membros insuficientes para o time '{}' em {} (mínimo: {}, disponível: {}). \
                     Verifique disponibilidades, restrições de casais e o limite mensal de {} escalas por membro.",
                    es.squad_name, occurrence_date, es.min_members, allocated.len(),
                    config.max_occurrences_per_month
                )));
            }

            for member_id in &allocated {
                globally_allocated.insert(member_id.clone());
                allocations.push((event_id.clone(), occurrence_date.clone(), es.squad_id.clone(), member_id.clone()));
                *monthly_count_map.entry(member_id.clone()).or_insert(0) += 1;
                last_date_map.insert(member_id.clone(), occurrence_naive);
            }
            info!("[generate_month] {} em {} — Squad '{}' → {:?}",
                event_id, occurrence_date, es.squad_name, allocated);
        }
    }

    info!("[generate_month] Phase 1 completa: {} alocações totais", allocations.len());

    // ── PHASE 2: Gravação atômica ──
    schedule_repo::save_month_allocations(pool, month, &allocations).await?;

    info!("[generate_month] Phase 2 completa — {} entradas salvas no DB", allocations.len());

    schedule_repo::get_month_schedule(pool, month).await
}

// ── Limpeza ──

pub async fn clear_schedule(pool: &SqlitePool, event_id: &str) -> Result<(), AppError> {
    schedule_repo::clear_event(pool, event_id).await
}

pub async fn clear_month_schedule(pool: &SqlitePool, month: &str) -> Result<(), AppError> {
    schedule_repo::clear_month(pool, month).await
}

// ── Helpers privados ──

fn parse_month(month: &str) -> Result<(i32, u32), AppError> {
    let parts: Vec<&str> = month.split('-').collect();
    if parts.len() != 2 {
        return Err(AppError::Validation("Formato de mês inválido (esperado YYYY-MM)".into()));
    }
    let year: i32 = parts[0].parse().map_err(|_| AppError::Validation("Ano inválido".into()))?;
    let month_num: u32 = parts[1].parse().map_err(|_| AppError::Validation("Mês inválido".into()))?;
    Ok((year, month_num))
}

fn log_monthly_blocked(monthly_counts: &HashMap<String, i64>, label: &str, date: Option<&str>, config: &ScheduleConfig) {
    if !config.apply_monthly_limit { return; }
    let max = config.max_occurrences_per_month;
    for (id, &count) in monthly_counts {
        if count >= max {
            match date {
                Some(d) => debug!("[{}] {} bloqueado em {} (mensal: {} >= {})", label, id, d, count, max),
                None => info!("[{}] Membro {} bloqueado (limite mensal: {} >= {})", label, id, count, max),
            }
        }
    }
}

fn log_candidate_ranking(
    label: &str,
    ranked: &[String],
    monthly_counts: &HashMap<String, i64>,
    days_idle: &HashMap<String, i64>,
    historical_counts: &HashMap<String, i64>,
    occurrence_date: &str,
) {
    debug!("{}", label);
    for (pos, c) in ranked.iter().enumerate() {
        debug!("  #{} {} → mes={}, idle={}, hist={}, hash={}",
            pos + 1, c,
            monthly_counts.get(c).copied().unwrap_or(0),
            days_idle.get(c).copied().unwrap_or(9999),
            historical_counts.get(c).copied().unwrap_or(0),
            tiebreak_hash(c, occurrence_date));
    }
}

#[cfg(test)]
mod tests;