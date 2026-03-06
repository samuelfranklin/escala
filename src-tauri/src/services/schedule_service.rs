//! Schedule generator — distribui membros por squads respeitando:
//! - Disponibilidade (tabela availability)
//! - Restrições de casais (tabela couples)
//! - Configuração mín/máx de membros por squad (tabela event_squads)
//! - Rotatividade: prioriza quem foi escalado há mais tempo

use crate::{db::schedule_repo, errors::AppError, models::schedule::{MonthScheduleView, ScheduleView}};
use chrono::{Datelike, NaiveDate};
use sqlx::SqlitePool;
use std::collections::{HashMap, HashSet};
use uuid::Uuid;

pub async fn get_schedule(pool: &SqlitePool, event_id: &str) -> Result<ScheduleView, AppError> {
    schedule_repo::get_by_event(pool, event_id).await
}

pub async fn get_month_schedule(pool: &SqlitePool, month: &str) -> Result<MonthScheduleView, AppError> {
    schedule_repo::get_month_schedule(pool, month).await
}

pub async fn generate_schedule(pool: &SqlitePool, event_id: &str) -> Result<ScheduleView, AppError> {
    // 1. Busca o evento e sua data
    let event = sqlx::query!(
        r#"SELECT id as "id!", event_date, event_type as "event_type!" FROM events WHERE id = ?"#, event_id)
        .fetch_optional(pool).await.map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Event '{}' not found", event_id)))?;

    let event_date = event.event_date.ok_or_else(|| {
        AppError::Validation("Eventos regulares (recorrentes) devem ser gerados pela escala mensal. Use 'Gerar Escala do Mês'.".into())
    })?;

    // 2. Busca squads configurados para o evento
    let event_squads = sqlx::query!(
        r#"SELECT squad_id as "squad_id!", min_members, max_members FROM event_squads WHERE event_id = ?"#, event_id)
        .fetch_all(pool).await.map_err(AppError::from)?;

    if event_squads.is_empty() {
        return Err(AppError::Validation("Event has no squads configured".into()));
    }

    // 3. Indisponibilidades na data do evento
    let unavailable: HashSet<String> = sqlx::query!(
        r#"SELECT member_id as "member_id!" FROM availability WHERE unavailable_date = ?"#, event_date)
        .fetch_all(pool).await.map_err(AppError::from)?
        .into_iter().map(|r| r.member_id).collect();

    // 4. Restrições de casais
    let couple_rows = sqlx::query!(
        r#"SELECT member_a_id as "member_a_id!", member_b_id as "member_b_id!" FROM couples"#)
        .fetch_all(pool).await.map_err(AppError::from)?;
    let mut couple_map: HashMap<String, HashSet<String>> = HashMap::new();
    for r in &couple_rows {
        couple_map.entry(r.member_a_id.clone()).or_default().insert(r.member_b_id.clone());
        couple_map.entry(r.member_b_id.clone()).or_default().insert(r.member_a_id.clone());
    }

    // 5. Contagem de escalas anteriores por membro (rotatividade)
    let schedule_counts = sqlx::query!(
        r#"SELECT member_id as "member_id!", COUNT(*) as "cnt: i64" FROM schedule_entries GROUP BY member_id"#)
        .fetch_all(pool).await.map_err(AppError::from)?;
    let count_map: HashMap<String, i64> = schedule_counts.into_iter()
        .map(|r| (r.member_id, r.cnt)).collect();

    // 6. Limpa escala anterior do evento
    schedule_repo::clear_event(pool, event_id).await?;

    // 7. Para cada squad, seleciona membros
    let mut globally_allocated: HashSet<String> = HashSet::new();

    for es in &event_squads {
        let mut candidates = sqlx::query!(
            r#"SELECT m.id as "id!" FROM members m
               INNER JOIN members_squads ms ON ms.member_id = m.id
               WHERE ms.squad_id = ? AND m.active = 1"#,
            es.squad_id)
            .fetch_all(pool).await.map_err(AppError::from)?
            .into_iter().map(|r| r.id)
            .filter(|id| !unavailable.contains(id))
            .collect::<Vec<_>>();

        candidates.sort_by(|a, b| {
            let ca = count_map.get(a).copied().unwrap_or(0);
            let cb = count_map.get(b).copied().unwrap_or(0);
            ca.cmp(&cb).then(a.cmp(b))
        });

        let mut allocated_in_squad: Vec<String> = Vec::new();
        let max = es.max_members as usize;

        'outer: for candidate in &candidates {
            if allocated_in_squad.len() >= max { break; }
            if let Some(restricted) = couple_map.get(candidate.as_str()) {
                for already in &globally_allocated {
                    if restricted.contains(already) { continue 'outer; }
                }
            }
            allocated_in_squad.push(candidate.clone());
            globally_allocated.insert(candidate.clone());
        }

        if (allocated_in_squad.len() as i64) < es.min_members {
            return Err(AppError::Validation(format!(
                "Not enough available members for squad '{}' (need {}, got {})",
                es.squad_id, es.min_members, allocated_in_squad.len()
            )));
        }

        for member_id in &allocated_in_squad {
            schedule_repo::insert_entry(pool, event_id, &es.squad_id, member_id).await?;
        }
    }

    schedule_repo::get_by_event(pool, event_id).await
}

/// Gera a escala para todos os eventos de um mês (YYYY-MM).
/// Eventos regulares: cada ocorrência calculada pela recorrência.
/// Eventos fixos (special/training): incluídos se event_date cair no mês.
///
/// Estratégia two-phase para garantir atomicidade:
///   Phase 1 — Calcula todas as alocações em memória (sem writes ao DB).
///              Se min_members não for atingido, retorna Err sem alterar o BD.
///   Phase 2 — Transação atômica: limpa o mês e insere todas as alocações.
///              Qualquer falha faz rollback automático, preservando a escala anterior.
pub async fn generate_month_schedule(pool: &SqlitePool, month: &str) -> Result<MonthScheduleView, AppError> {
    let parts: Vec<&str> = month.split('-').collect();
    if parts.len() != 2 {
        return Err(AppError::Validation("Formato de mês inválido (esperado YYYY-MM)".into()));
    }
    let year: i32 = parts[0].parse().map_err(|_| AppError::Validation("Ano inválido".into()))?;
    let month_num: u32 = parts[1].parse().map_err(|_| AppError::Validation("Mês inválido".into()))?;

    let month_pattern = format!("{}%", month);

    // 1. Carrega todos os eventos
    let events = sqlx::query!(
        r#"SELECT id as "id!", name as "name!", event_date, event_type as "event_type!", day_of_week, recurrence
           FROM events"#
    ).fetch_all(pool).await.map_err(AppError::from)?;

    // 2. Calcula as ocorrências do mês: (event_id, event_name, occurrence_date)
    let mut all_occurrences: Vec<(String, String, String)> = Vec::new();
    for ev in &events {
        if ev.event_type == "regular" {
            if let (Some(dow), Some(rec)) = (ev.day_of_week, &ev.recurrence) {
                let dates = occurrence_dates(year, month_num, dow, rec);
                for date in dates {
                    all_occurrences.push((ev.id.clone(), ev.name.clone(), date));
                }
            }
        } else if let Some(ref date) = ev.event_date {
            if date.starts_with(month) {
                all_occurrences.push((ev.id.clone(), ev.name.clone(), date.clone()));
            }
        }
    }

    // Ordena cronologicamente
    all_occurrences.sort_by(|a, b| a.2.cmp(&b.2).then(a.1.cmp(&b.1)));

    if all_occurrences.is_empty() {
        // Sem ocorrências: limpa o mês atomicamente e retorna vazio
        let mut tx = pool.begin().await.map_err(AppError::from)?;
        sqlx::query!("DELETE FROM schedule_entries WHERE occurrence_date LIKE ?", month_pattern)
            .execute(&mut *tx).await.map_err(AppError::from)?;
        tx.commit().await.map_err(AppError::from)?;
        return Ok(MonthScheduleView { month: month.to_string(), occurrences: vec![] });
    }

    // 3. Restrições de casais (carregadas uma vez)
    let couple_rows = sqlx::query!(
        r#"SELECT member_a_id as "member_a_id!", member_b_id as "member_b_id!" FROM couples"#)
        .fetch_all(pool).await.map_err(AppError::from)?;
    let mut couple_map: HashMap<String, HashSet<String>> = HashMap::new();
    for r in &couple_rows {
        couple_map.entry(r.member_a_id.clone()).or_default().insert(r.member_b_id.clone());
        couple_map.entry(r.member_b_id.clone()).or_default().insert(r.member_a_id.clone());
    }

    // 4. Histórico de escalas por membro, EXCLUINDO o mês atual.
    //    Garante rotação correta tanto na geração inicial quanto na regeração
    //    (ao regenerar Abril, não conta as entradas antigas de Abril que serão substituídas).
    let schedule_counts = sqlx::query!(
        r#"SELECT member_id as "member_id!", COUNT(*) as "cnt: i64"
           FROM schedule_entries
           WHERE occurrence_date NOT LIKE ? OR occurrence_date IS NULL
           GROUP BY member_id"#,
        month_pattern)
        .fetch_all(pool).await.map_err(AppError::from)?;
    let mut count_map: HashMap<String, i64> = schedule_counts.into_iter()
        .map(|r| (r.member_id, r.cnt)).collect();

    // ── PHASE 1: Calcula todas as alocações em memória (sem writes ao DB) ──
    // Qualquer falha aqui (ex: membros insuficientes) retorna Err sem alterar o DB.
    let mut allocations: Vec<(String, String, String, String)> = Vec::new();

    for (event_id, _, occurrence_date) in &all_occurrences {
        let event_squads = sqlx::query!(
            r#"SELECT es.squad_id as "squad_id!", s.name as "squad_name!", es.min_members, es.max_members
               FROM event_squads es
               JOIN squads s ON s.id = es.squad_id
               WHERE es.event_id = ?"#,
            event_id)
            .fetch_all(pool).await.map_err(AppError::from)?;

        if event_squads.is_empty() {
            continue; // Evento sem times configurados — pula mas não falha o mês inteiro
        }

        let unavailable: HashSet<String> = sqlx::query!(
            r#"SELECT member_id as "member_id!" FROM availability WHERE unavailable_date = ?"#,
            occurrence_date)
            .fetch_all(pool).await.map_err(AppError::from)?
            .into_iter().map(|r| r.member_id).collect();

        let mut globally_allocated: HashSet<String> = HashSet::new();

        for es in &event_squads {
            let mut candidates = sqlx::query!(
                r#"SELECT m.id as "id!" FROM members m
                   INNER JOIN members_squads ms ON ms.member_id = m.id
                   WHERE ms.squad_id = ? AND m.active = 1"#,
                es.squad_id)
                .fetch_all(pool).await.map_err(AppError::from)?
                .into_iter().map(|r| r.id)
                .filter(|id| !unavailable.contains(id))
                .collect::<Vec<_>>();

            candidates.sort_by(|a, b| {
                let ca = count_map.get(a).copied().unwrap_or(0);
                let cb = count_map.get(b).copied().unwrap_or(0);
                ca.cmp(&cb).then(a.cmp(b))
            });

            let mut allocated_in_squad: Vec<String> = Vec::new();
            let max = es.max_members as usize;

            'outer: for candidate in &candidates {
                if allocated_in_squad.len() >= max { break; }
                if let Some(restricted) = couple_map.get(candidate.as_str()) {
                    for already in &globally_allocated {
                        if restricted.contains(already) { continue 'outer; }
                    }
                }
                allocated_in_squad.push(candidate.clone());
                globally_allocated.insert(candidate.clone());
            }

            if (allocated_in_squad.len() as i64) < es.min_members {
                // Falha na Phase 1 → nenhum write ao DB → escala anterior intacta
                return Err(AppError::Validation(format!(
                    "Membros insuficientes para o time '{}' em {} (mínimo: {}, disponível: {}). Verifique disponibilidades e restrições de casais.",
                    es.squad_name, occurrence_date, es.min_members, allocated_in_squad.len()
                )));
            }

            for member_id in &allocated_in_squad {
                allocations.push((event_id.clone(), occurrence_date.clone(), es.squad_id.clone(), member_id.clone()));
                // Atualiza rotatividade em memória para as próximas ocorrências do mês
                *count_map.entry(member_id.clone()).or_insert(0) += 1;
            }
        }
    }

    // ── PHASE 2: Transação atômica — limpa o mês e insere todas as alocações ──
    // O rollback automático (ao soltar `tx` sem commit) preserva a escala anterior.
    let mut tx = pool.begin().await.map_err(AppError::from)?;

    sqlx::query!("DELETE FROM schedule_entries WHERE occurrence_date LIKE ?", month_pattern)
        .execute(&mut *tx).await.map_err(AppError::from)?;

    for (event_id, occurrence_date, squad_id, member_id) in &allocations {
        let id = Uuid::new_v4().to_string().replace('-', "");
        sqlx::query!(
            "INSERT INTO schedule_entries (id, event_id, occurrence_date, squad_id, member_id) VALUES (?, ?, ?, ?, ?)",
            id, event_id, occurrence_date, squad_id, member_id)
            .execute(&mut *tx).await.map_err(AppError::from)?;
    }

    tx.commit().await.map_err(AppError::from)?;

    schedule_repo::get_month_schedule(pool, month).await
}

pub async fn clear_schedule(pool: &SqlitePool, event_id: &str) -> Result<(), AppError> {
    schedule_repo::clear_event(pool, event_id).await
}

pub async fn clear_month_schedule(pool: &SqlitePool, month: &str) -> Result<(), AppError> {
    schedule_repo::clear_month(pool, month).await
}

/// Calcula as datas de ocorrência de um evento regular em um mês.
/// day_of_week: 0=Dom, 1=Seg, 2=Ter, 3=Qua, 4=Qui, 5=Sex, 6=Sáb
/// recurrence: weekly | biweekly | monthly_1 | monthly_2 | monthly_3 | monthly_4
fn occurrence_dates(year: i32, month_num: u32, day_of_week: i64, recurrence: &str) -> Vec<String> {
    // Converte nosso dow (0=Dom) para chrono num_days_from_monday (Mon=0..Sun=6)
    let target: u32 = match day_of_week {
        0 => 6, // Dom → chrono 6
        n @ 1..=6 => (n - 1) as u32, // Seg→0, Ter→1, ..., Sáb→5
        _ => return vec![],
    };

    let Some(mut cursor) = NaiveDate::from_ymd_opt(year, month_num, 1) else {
        return vec![];
    };

    let mut all: Vec<NaiveDate> = Vec::new();
    while cursor.month() == month_num {
        if cursor.weekday().num_days_from_monday() == target {
            all.push(cursor);
        }
        let Some(next) = cursor.succ_opt() else { break };
        cursor = next;
    }

    let selected: Vec<NaiveDate> = match recurrence {
        "weekly" => all,
        "biweekly" => all.into_iter().enumerate().filter(|(i, _)| i % 2 == 0).map(|(_, d)| d).collect(),
        "monthly_1" => all.into_iter().take(1).collect(),
        "monthly_2" => all.into_iter().skip(1).take(1).collect(),
        "monthly_3" => all.into_iter().skip(2).take(1).collect(),
        "monthly_4" => all.into_iter().skip(3).take(1).collect(),
        _ => vec![],
    };

    selected.into_iter().map(|d| d.format("%Y-%m-%d").to_string()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::{HashMap, HashSet};

    /// Algoritmo de seleção puro (sem DB) — testável sem sistema de ficheiros
    fn select_members(
        candidates: &[String],
        count_map: &HashMap<String, i64>,
        couple_map: &HashMap<String, HashSet<String>>,
        globally_allocated: &HashSet<String>,
        max: usize,
    ) -> Vec<String> {
        let mut sorted = candidates.to_vec();
        sorted.sort_by(|a, b| {
            let ca = count_map.get(a).copied().unwrap_or(0);
            let cb = count_map.get(b).copied().unwrap_or(0);
            ca.cmp(&cb).then(a.cmp(b))
        });
        let mut result = Vec::new();
        'outer: for c in &sorted {
            if result.len() >= max { break; }
            if let Some(restricted) = couple_map.get(c) {
                for already in globally_allocated { if restricted.contains(already) { continue 'outer; } }
            }
            result.push(c.clone());
        }
        result
    }

    #[test]
    fn test_rotation_prioritizes_less_scheduled() {
        let candidates = vec!["a".into(), "b".into(), "c".into()];
        let mut counts = HashMap::new();
        counts.insert("a".into(), 5i64);
        counts.insert("b".into(), 2i64);
        counts.insert("c".into(), 8i64);
        let result = select_members(&candidates, &counts, &HashMap::new(), &HashSet::new(), 2);
        assert_eq!(result, vec!["b", "a"]);
    }

    #[test]
    fn test_couple_restriction_respected() {
        let candidates = vec!["a".into(), "b".into(), "c".into()];
        let mut couples: HashMap<String, HashSet<String>> = HashMap::new();
        couples.entry("a".into()).or_default().insert("x".into());
        let mut allocated = HashSet::new();
        allocated.insert("x".into()); // x já está alocado globalmente
        let result = select_members(&candidates, &HashMap::new(), &couples, &allocated, 3);
        // "a" deve ser excluído porque está restrito com "x" que já foi alocado
        assert!(!result.contains(&"a".to_string()));
        assert!(result.contains(&"b".to_string()));
        assert!(result.contains(&"c".to_string()));
    }

    #[test]
    fn test_max_members_respected() {
        let candidates = vec!["a".into(), "b".into(), "c".into(), "d".into()];
        let result = select_members(&candidates, &HashMap::new(), &HashMap::new(), &HashSet::new(), 2);
        assert_eq!(result.len(), 2);
    }

    // ── Testes de occurrence_dates ──────────────────────────────────────────

    #[test]
    fn test_occurrence_dates_weekly_domingo_marco_2026() {
        // Domingos de março 2026: 01, 08, 15, 22, 29
        let dates = occurrence_dates(2026, 3, 0, "weekly");
        assert_eq!(dates, vec!["2026-03-01", "2026-03-08", "2026-03-15", "2026-03-22", "2026-03-29"]);
    }

    #[test]
    fn test_occurrence_dates_monthly_2_terca_marco_2026() {
        // Terças de março 2026: 03, 10, 17, 24, 31 → 2ª = 10/03
        let dates = occurrence_dates(2026, 3, 2, "monthly_2");
        assert_eq!(dates, vec!["2026-03-10"]);
    }

    #[test]
    fn test_occurrence_dates_biweekly_domingo_marco_2026() {
        // Domingos: 01, 08, 15, 22, 29 → quinzenal (índices 0,2,4) = 01, 15, 29
        let dates = occurrence_dates(2026, 3, 0, "biweekly");
        assert_eq!(dates, vec!["2026-03-01", "2026-03-15", "2026-03-29"]);
    }

    #[test]
    fn test_occurrence_dates_monthly_1_segunda_marco_2026() {
        // Segundas de março 2026: 02, 09, 16, 23, 30 → 1ª = 02/03
        let dates = occurrence_dates(2026, 3, 1, "monthly_1");
        assert_eq!(dates, vec!["2026-03-02"]);
    }
}
