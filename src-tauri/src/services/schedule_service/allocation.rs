use std::collections::{HashMap, HashSet};
use super::scoring::compute_score;
use crate::models::settings::ScheduleConfig;

/// Filtra candidatos indisponíveis e ordena por score decrescente.
///
/// Retorna a lista ordenada de IDs aptos para alocação.
pub fn rank_candidates(
    candidates: &[String],
    unavailable: &HashSet<String>,
    historical_counts: &HashMap<String, i64>,
    days_idle: &HashMap<String, i64>,
    monthly_counts: &HashMap<String, i64>,
    config: &ScheduleConfig,
) -> Vec<String> {
    let mut sorted: Vec<String> = candidates.iter()
        .filter(|c| !unavailable.contains(c.as_str()))
        .cloned()
        .collect();

    sorted.sort_by(|a, b| {
        let sa = compute_score(
            historical_counts.get(a).copied().unwrap_or(0),
            days_idle.get(a).copied().unwrap_or(9999),
            monthly_counts.get(a).copied().unwrap_or(0),
            config,
        );
        let sb = compute_score(
            historical_counts.get(b).copied().unwrap_or(0),
            days_idle.get(b).copied().unwrap_or(9999),
            monthly_counts.get(b).copied().unwrap_or(0),
            config,
        );
        sb.partial_cmp(&sa).unwrap_or(std::cmp::Ordering::Equal).then(a.cmp(b))
    });

    sorted
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
        let ranked = rank_candidates(&candidates, &unavailable, &HashMap::new(), &HashMap::new(), &HashMap::new(), &cfg());
        assert!(!ranked.contains(&"b".to_string()));
        assert_eq!(ranked.len(), 2);
    }

    #[test]
    fn rank_sorts_by_score_descending() {
        let candidates = vec!["a".into(), "b".into()];
        let mut idle = HashMap::new();
        idle.insert("a".to_string(), 10i64);
        idle.insert("b".to_string(), 100i64);
        let ranked = rank_candidates(&candidates, &HashSet::new(), &HashMap::new(), &idle, &HashMap::new(), &cfg());
        assert_eq!(ranked[0], "b");
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
}
