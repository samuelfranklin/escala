//! Schedule generator — distribui membros por squads respeitando:
//! - Disponibilidade (tabela availability)
//! - Restrições de casais (tabela couples)
//! - Configuração mín/máx de membros por squad (tabela event_squads)
//! - Rotatividade: prioriza quem foi escalado há mais tempo

use crate::{db::schedule_repo, errors::AppError, models::schedule::ScheduleView};
use sqlx::SqlitePool;
use std::collections::{HashMap, HashSet};

pub async fn get_schedule(pool: &SqlitePool, event_id: &str) -> Result<ScheduleView, AppError> {
    schedule_repo::get_by_event(pool, event_id).await
}

pub async fn generate_schedule(pool: &SqlitePool, event_id: &str) -> Result<ScheduleView, AppError> {
    // 1. Busca o evento e sua data
    let event = sqlx::query!(
        r#"SELECT id as "id!", event_date as "event_date!" FROM events WHERE id = ?"#, event_id)
        .fetch_optional(pool).await.map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Event '{}' not found", event_id)))?;

    // 2. Busca squads configurados para o evento
    let event_squads = sqlx::query!(
        r#"SELECT squad_id as "squad_id!", min_members, max_members FROM event_squads WHERE event_id = ?"#, event_id)
        .fetch_all(pool).await.map_err(AppError::from)?;

    if event_squads.is_empty() {
        return Err(AppError::Validation("Event has no squads configured".into()));
    }

    // 3. Indisponibilidades na data do evento
    let unavailable: HashSet<String> = sqlx::query!(
        r#"SELECT member_id as "member_id!" FROM availability WHERE unavailable_date = ?"#, event.event_date)
        .fetch_all(pool).await.map_err(AppError::from)?
        .into_iter().map(|r| r.member_id).collect();

    // 4. Restrições de casais: id_a → {id_b, ...}
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
        // Membros elegíveis: ativos, no squad, não indisponíveis
        let mut candidates = sqlx::query!(
            r#"SELECT m.id as "id!" FROM members m
               INNER JOIN members_squads ms ON ms.member_id = m.id
               WHERE ms.squad_id = ? AND m.active = 1"#,
            es.squad_id)
            .fetch_all(pool).await.map_err(AppError::from)?
            .into_iter().map(|r| r.id)
            .filter(|id| !unavailable.contains(id))
            .collect::<Vec<_>>();

        // Ordena por menor contagem de escalas (rotatividade) e depois por id (determinístico)
        candidates.sort_by(|a, b| {
            let ca = count_map.get(a).copied().unwrap_or(0);
            let cb = count_map.get(b).copied().unwrap_or(0);
            ca.cmp(&cb).then(a.cmp(b))
        });

        let mut allocated_in_squad: Vec<String> = Vec::new();
        let max = es.max_members as usize;

        'outer: for candidate in &candidates {
            if allocated_in_squad.len() >= max { break; }
            // Verifica restrição de casal com já alocados globalmente
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

pub async fn clear_schedule(pool: &SqlitePool, event_id: &str) -> Result<(), AppError> {
    schedule_repo::clear_event(pool, event_id).await
}

#[cfg(test)]
mod tests {
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
}
