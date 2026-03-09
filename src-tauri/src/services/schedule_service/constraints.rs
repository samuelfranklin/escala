use std::collections::{HashMap, HashSet};
use crate::models::settings::ScheduleConfig;

pub type CoupleMap = HashMap<String, HashSet<String>>;

/// Constrói o mapa bidirecional de casais a partir de pares (a, b).
pub fn build_couple_map(pairs: &[(String, String)]) -> CoupleMap {
    let mut map = CoupleMap::new();
    for (a, b) in pairs {
        map.entry(a.clone()).or_default().insert(b.clone());
        map.entry(b.clone()).or_default().insert(a.clone());
    }
    map
}

/// Aplica o limite mensal e propaga indisponibilidade por casais.
///
/// Retorna o conjunto expandido de membros indisponíveis.
/// As regras ativas são controladas por `config`.
pub fn build_unavailable(
    mut base: HashSet<String>,
    monthly_counts: &HashMap<String, i64>,
    couple_map: &CoupleMap,
    config: &ScheduleConfig,
) -> HashSet<String> {
    if config.apply_monthly_limit {
        apply_monthly_limit(&mut base, monthly_counts, config.max_occurrences_per_month);
    }
    if config.propagate_couples {
        propagate_couples(&mut base, couple_map);
    }
    base
}

fn apply_monthly_limit(
    unavailable: &mut HashSet<String>,
    monthly_counts: &HashMap<String, i64>,
    max: i64,
) {
    for (id, &count) in monthly_counts {
        if count >= max {
            unavailable.insert(id.clone());
        }
    }
}

fn propagate_couples(unavailable: &mut HashSet<String>, couple_map: &CoupleMap) {
    let extra: Vec<String> = unavailable.iter()
        .flat_map(|id| couple_map.get(id.as_str()).into_iter().flatten().cloned())
        .collect();
    unavailable.extend(extra);
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::settings::ScheduleConfig;

    fn default_config() -> ScheduleConfig { ScheduleConfig::default() }

    #[test]
    fn couple_map_is_bidirectional() {
        let pairs = vec![("a".into(), "b".into())];
        let map = build_couple_map(&pairs);
        assert!(map["a"].contains("b"));
        assert!(map["b"].contains("a"));
    }

    #[test]
    fn monthly_limit_blocks_member_at_max() {
        let mut unavailable = HashSet::new();
        let mut monthly = HashMap::new();
        monthly.insert("a".to_string(), 2i64);
        apply_monthly_limit(&mut unavailable, &monthly, 2);
        assert!(unavailable.contains("a"));
    }

    #[test]
    fn monthly_limit_allows_under_max() {
        let mut unavailable = HashSet::new();
        let mut monthly = HashMap::new();
        monthly.insert("a".to_string(), 1i64);
        apply_monthly_limit(&mut unavailable, &monthly, 2);
        assert!(!unavailable.contains("a"));
    }

    #[test]
    fn couple_propagation_blocks_partner() {
        let mut unavailable = HashSet::from(["b".to_string()]);
        let map = build_couple_map(&[("a".into(), "b".into())]);
        propagate_couples(&mut unavailable, &map);
        assert!(unavailable.contains("a"));
    }

    #[test]
    fn monthly_limit_disabled_skips_blocking() {
        let mut config = default_config();
        config.apply_monthly_limit = false;
        let mut monthly = HashMap::new();
        monthly.insert("a".to_string(), 99i64);
        let result = build_unavailable(HashSet::new(), &monthly, &HashMap::new(), &config);
        assert!(!result.contains("a"));
    }

    #[test]
    fn monthly_limit_custom_max() {
        let mut config = default_config();
        config.max_occurrences_per_month = 4;
        let mut monthly = HashMap::new();
        monthly.insert("a".to_string(), 3i64); // abaixo de 4 — não bloqueia
        monthly.insert("b".to_string(), 4i64); // igual a 4 — bloqueia
        let result = build_unavailable(HashSet::new(), &monthly, &HashMap::new(), &config);
        assert!(!result.contains("a"));
        assert!(result.contains("b"));
    }

    #[test]
    fn couple_propagation_disabled_does_not_block_partner() {
        let mut config = default_config();
        config.propagate_couples = false;
        let unavailable = HashSet::from(["b".to_string()]);
        let map = build_couple_map(&[("a".into(), "b".into())]);
        let result = build_unavailable(unavailable, &HashMap::new(), &map, &config);
        assert!(result.contains("b"));
        assert!(!result.contains("a")); // parceiro NÃO propagado
    }

    #[test]
    fn build_unavailable_combines_all_constraints() {
        let base = HashSet::from(["x".to_string()]);
        let mut monthly = HashMap::new();
        monthly.insert("a".to_string(), 2i64);
        let map = build_couple_map(&[("a".into(), "b".into())]);
        let config = default_config(); // apply_monthly_limit=true, propagate_couples=true, max=2

        let result = build_unavailable(base, &monthly, &map, &config);
        assert!(result.contains("x")); // original
        assert!(result.contains("a")); // monthly limit
        assert!(result.contains("b")); // couple propagation from a
    }
}
