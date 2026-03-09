use crate::models::settings::ScheduleConfig;

/// Score de prioridade multi-fator revisado.
///
/// Penaliza severamente escalas sequenciais no mesmo mês, enquanto usa o histórico geral
/// apenas como um peso leve de desempate para não esmagar membros ativos.
/// Se `config.apply_history_scoring == false`, o peso do histórico é zerado.
pub fn compute_score(count_historico: i64, days_idle: i64, vezes_no_mes: i64, config: &ScheduleConfig) -> f64 {
    let base = (days_idle + 1) as f64;
    let penalty_mes = (vezes_no_mes * 5 + 1) as f64;
    let penalty_historico = if config.apply_history_scoring {
        (count_historico as f64) * 0.1
    } else {
        0.0
    };

    let score = (base / penalty_mes) - penalty_historico;

    if score < 0.0 { 0.0 } else { score }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_config() -> ScheduleConfig { ScheduleConfig::default() }

    #[test]
    fn never_scheduled_scores_highest() {
        let score_never = compute_score(0, 9999, 0, &default_config());
        let score_experienced = compute_score(1, 30, 0, &default_config());
        assert!(score_never > score_experienced);
    }

    #[test]
    fn monthly_penalty_reduces_score() {
        let without = compute_score(0, 10, 0, &default_config());
        let with_one = compute_score(0, 10, 1, &default_config());
        let with_two = compute_score(0, 10, 2, &default_config());
        assert!(without > with_one);
        assert!(with_one > with_two);
    }

    #[test]
    fn historical_penalty_reduces_score() {
        let few = compute_score(1, 30, 0, &default_config());
        let many = compute_score(10, 30, 0, &default_config());
        assert!(few > many);
    }

    #[test]
    fn score_never_negative() {
        let score = compute_score(9999, 0, 9999, &default_config());
        assert!(score >= 0.0);
    }

    #[test]
    fn history_scoring_disabled_ignores_historical_count() {
        let mut config = default_config();
        config.apply_history_scoring = false;
        let score_low = compute_score(1, 30, 0, &config);
        let score_high = compute_score(1000, 30, 0, &config);
        assert_eq!(score_low, score_high); // histórico não afeta o score
    }
}
