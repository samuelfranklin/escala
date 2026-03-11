use std::collections::{HashMap, HashSet};
use super::scoring::{CandidatePriority, tiebreak_hash};
use crate::models::settings::ScheduleConfig;

/// Filtra candidatos indisponíveis e ordena por prioridade multi-chave.
///
/// Candidatos com menor `times_this_month` vêm primeiro; em caso de empate,
/// quem está parado há mais tempo tem prioridade; depois histórico total;
/// e finalmente um hash determinístico baseado na data para variar a distribuição.
pub fn rank_candidates(
    candidates: &[String],
    unavailable: &HashSet<String>,
    historical_counts: &HashMap<String, i64>,
    days_idle: &HashMap<String, i64>,
    monthly_counts: &HashMap<String, i64>,
    config: &ScheduleConfig,
    occurrence_date: &str,
) -> Vec<String> {
    let mut eligible: Vec<String> = candidates.iter()
        .filter(|c| !unavailable.contains(c.as_str()))
        .cloned()
        .collect();

    eligible.sort_by(|a, b| {
        let pa = CandidatePriority {
            times_this_month: monthly_counts.get(a).copied().unwrap_or(0),
            days_idle: days_idle.get(a).copied().unwrap_or(9999),
            historical_count: historical_counts.get(a).copied().unwrap_or(0),
            use_history: config.apply_history_scoring,
            tiebreak: tiebreak_hash(a, occurrence_date),
        };
        let pb = CandidatePriority {
            times_this_month: monthly_counts.get(b).copied().unwrap_or(0),
            days_idle: days_idle.get(b).copied().unwrap_or(9999),
            historical_count: historical_counts.get(b).copied().unwrap_or(0),
            use_history: config.apply_history_scoring,
            tiebreak: tiebreak_hash(b, occurrence_date),
        };
        pa.cmp_priority(&pb)
    });

    eligible
}

/// Seleciona os primeiros `max` candidatos que não estão globalmente alocados.
pub fn allocate_top(
    ranked: &[String],
    globally_allocated: &HashSet<String>,
    max: usize,
) -> Vec<String> {
    let mut result = Vec::new();
    for c in ranked {
        if result.len() >= max { break; }
        if globally_allocated.contains(c.as_str()) { continue; }
        result.push(c.clone());
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::settings::ScheduleConfig;

    fn cfg() -> ScheduleConfig { ScheduleConfig::default() }

    #[test]
    fn rank_filters_unavailable() {
        let candidates = vec!["a".into(), "b".into(), "c".into()];
        let unavailable = HashSet::from(["b".to_string()]);
        let ranked = rank_candidates(&candidates, &unavailable, &HashMap::new(), &HashMap::new(), &HashMap::new(), &cfg(), "2026-03-01");
        assert!(!ranked.contains(&"b".to_string()));
        assert_eq!(ranked.len(), 2);
    }

    #[test]
    fn rank_prefers_less_monthly() {
        let candidates = vec!["a".into(), "b".into()];
        let mut monthly = HashMap::new();
        monthly.insert("a".to_string(), 2i64);
        monthly.insert("b".to_string(), 0i64);
        let ranked = rank_candidates(&candidates, &HashSet::new(), &HashMap::new(), &HashMap::new(), &monthly, &cfg(), "2026-03-01");
        assert_eq!(ranked[0], "b");
    }

    #[test]
    fn rank_prefers_more_idle_when_monthly_equal() {
        let candidates = vec!["a".into(), "b".into()];
        let mut idle = HashMap::new();
        idle.insert("a".to_string(), 10i64);
        idle.insert("b".to_string(), 100i64);
        let ranked = rank_candidates(&candidates, &HashSet::new(), &HashMap::new(), &idle, &HashMap::new(), &cfg(), "2026-03-01");
        assert_eq!(ranked[0], "b");
    }

    #[test]
    fn rank_prefers_less_historical_when_month_and_idle_equal() {
        let candidates = vec!["a".into(), "b".into()];
        let mut hist = HashMap::new();
        hist.insert("a".to_string(), 10i64);
        hist.insert("b".to_string(), 2i64);
        let mut idle = HashMap::new();
        idle.insert("a".to_string(), 30i64);
        idle.insert("b".to_string(), 30i64);
        let ranked = rank_candidates(&candidates, &HashSet::new(), &hist, &idle, &HashMap::new(), &cfg(), "2026-03-01");
        assert_eq!(ranked[0], "b");
    }

    #[test]
    fn rank_tiebreak_varies_by_date() {
        let candidates: Vec<String> = (0..10).map(|i| format!("member-{}", i)).collect();
        let ranked_d1 = rank_candidates(&candidates, &HashSet::new(), &HashMap::new(), &HashMap::new(), &HashMap::new(), &cfg(), "2026-03-01");
        let ranked_d2 = rank_candidates(&candidates, &HashSet::new(), &HashMap::new(), &HashMap::new(), &HashMap::new(), &cfg(), "2026-03-08");
        // Com todos os dados iguais e apenas a data diferente, a ordem deve variar
        assert_ne!(ranked_d1, ranked_d2);
    }

    #[test]
    fn allocate_respects_max() {
        let ranked = vec!["a".into(), "b".into(), "c".into()];
        let result = allocate_top(&ranked, &HashSet::new(), 2);
        assert_eq!(result.len(), 2);
    }

    #[test]
    fn allocate_skips_globally_allocated() {
        let ranked = vec!["a".into(), "b".into(), "c".into()];
        let allocated = HashSet::from(["a".to_string()]);
        let result = allocate_top(&ranked, &allocated, 2);
        assert_eq!(result, vec!["b", "c"]);
    }

    // ── Teste de rotação completa: cenário do usuário ──

    #[test]
    fn rotation_60_members_10_squads_5_weeks() {
        use chrono::NaiveDate;

        let cfg = ScheduleConfig::default();
        let dates = vec!["2026-03-01", "2026-03-08", "2026-03-15", "2026-03-22", "2026-03-29"];

        // 10 squads, cada um com 6 membros distintos (60 membros total)
        let squads: Vec<Vec<String>> = (0..10).map(|s| {
            (0..6).map(|m| format!("squad{}-member{}", s, m)).collect()
        }).collect();

        let mut monthly_counts: HashMap<String, i64> = HashMap::new();
        let mut last_dates: HashMap<String, NaiveDate> = HashMap::new();
        let historical: HashMap<String, i64> = HashMap::new();

        let mut squad_allocations: Vec<Vec<String>> = vec![vec![]; 10];

        for date_str in &dates {
            let occurrence = NaiveDate::parse_from_str(date_str, "%Y-%m-%d").unwrap();
            let unavailable: HashSet<String> = HashSet::new();
            let mut globally_allocated: HashSet<String> = HashSet::new();

            for (s_idx, squad_members) in squads.iter().enumerate() {
                let days_idle: HashMap<String, i64> = squad_members.iter()
                    .map(|id| {
                        let idle = last_dates.get(id)
                            .map(|&last| (occurrence - last).num_days())
                            .unwrap_or(9999);
                        (id.clone(), idle)
                    })
                    .collect();

                let ranked = rank_candidates(
                    squad_members, &unavailable, &historical, &days_idle, &monthly_counts, &cfg, date_str,
                );
                let allocated = allocate_top(&ranked, &globally_allocated, 1);
                assert_eq!(allocated.len(), 1, "Squad {} em {} deveria alocar 1 membro", s_idx, date_str);

                let member = &allocated[0];
                globally_allocated.insert(member.clone());
                *monthly_counts.entry(member.clone()).or_insert(0) += 1;
                last_dates.insert(member.clone(), occurrence);
                squad_allocations[s_idx].push(member.clone());
            }
        }

        // Nenhum membro repete em todas as semanas no mesmo squad
        for (s_idx, allocs) in squad_allocations.iter().enumerate() {
            assert_eq!(allocs.len(), 5, "Squad {} deveria ter 5 alocações", s_idx);
            let unique: HashSet<&String> = allocs.iter().collect();
            assert!(unique.len() > 1,
                "Squad {} alocou o mesmo membro em todas as semanas: {:?}", s_idx, allocs);
            assert_eq!(unique.len(), 5,
                "Squad {} deveria ter 5 membros únicos em 5 semanas, teve {}: {:?}",
                s_idx, unique.len(), allocs);
        }

        // Nenhum membro excede max_occurrences
        for (id, &count) in &monthly_counts {
            assert!(count <= cfg.max_occurrences_per_month,
                "Membro {} excedeu limite mensal: {} > {}", id, count, cfg.max_occurrences_per_month);
        }
    }

    #[test]
    fn rotation_small_squad_alternates() {
        let cfg = ScheduleConfig::default();
        let dates = vec!["2026-03-01", "2026-03-08", "2026-03-15", "2026-03-22"];
        let candidates = vec!["alice".into(), "bob".into()];

        let mut monthly: HashMap<String, i64> = HashMap::new();
        let mut last: HashMap<String, chrono::NaiveDate> = HashMap::new();
        let mut allocations: Vec<String> = Vec::new();

        for date_str in &dates {
            let occurrence = chrono::NaiveDate::parse_from_str(date_str, "%Y-%m-%d").unwrap();
            let idle: HashMap<String, i64> = candidates.iter()
                .map(|id: &String| {
                    let d = last.get(id).map(|&l| (occurrence - l).num_days()).unwrap_or(9999);
                    (id.clone(), d)
                }).collect();

            let ranked = rank_candidates(&candidates, &HashSet::new(), &HashMap::new(), &idle, &monthly, &cfg, date_str);
            let selected = allocate_top(&ranked, &HashSet::new(), 1);
            assert_eq!(selected.len(), 1);

            let member = &selected[0];
            *monthly.entry(member.clone()).or_insert(0) += 1;
            last.insert(member.clone(), occurrence);
            allocations.push(member.clone());
        }

        // Com max_occurrences=2 e 2 membros, cada um serve exatamente 2x em 4 semanas
        let alice_count = allocations.iter().filter(|m| *m == "alice").count();
        let bob_count = allocations.iter().filter(|m| *m == "bob").count();
        assert_eq!(alice_count, 2, "Alice deveria servir 2x, serviu {}", alice_count);
        assert_eq!(bob_count, 2, "Bob deveria servir 2x, serviu {}", bob_count);

        // Ninguém serve duas semanas seguidas
        for i in 0..allocations.len() - 1 {
            assert_ne!(allocations[i], allocations[i + 1],
                "Mesmo membro em semanas consecutivas: {} em {} e {}", allocations[i], dates[i], dates[i + 1]);
        }
    }
}
