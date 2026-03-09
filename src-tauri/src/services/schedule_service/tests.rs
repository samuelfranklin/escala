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
    let config = ScheduleConfig::default();
    let effective_unavailable = constraints::build_unavailable(
        unavailable.clone(), monthly_count_map, couple_map, &config,
    );
    let ranked = allocation::rank_candidates(
        candidates, &effective_unavailable, count_map, days_idle_map, monthly_count_map, &config,
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
    assert_eq!(result, vec!["m1", "m2", "m3"]);
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
