use std::cmp::Ordering;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

/// Prioridade de um candidato para alocação, usando comparação multi-chave
/// explícita em vez de score float opaco.
///
/// Critérios (em ordem de importância):
/// 1. `times_this_month` ASC — quem serviu MENOS no mês tem prioridade
/// 2. `days_idle` DESC — quem está parado há mais tempo tem prioridade
/// 3. `historical_count` ASC — quem serviu MENOS no geral tem prioridade
/// 4. `tiebreak` — hash determinístico baseado em (member_id + date)
#[derive(Debug, Clone)]
pub struct CandidatePriority {
    pub times_this_month: i64,
    pub days_idle: i64,
    pub historical_count: i64,
    pub use_history: bool,
    pub tiebreak: u64,
}

impl CandidatePriority {
    /// Compara dois candidatos. Ordering::Less = MAIOR prioridade (será selecionado primeiro).
    pub fn cmp_priority(&self, other: &CandidatePriority) -> Ordering {
        // 1. Menos vezes no mês → maior prioridade
        self.times_this_month.cmp(&other.times_this_month)
            // 2. Mais dias parado → maior prioridade (invertido)
            .then(other.days_idle.cmp(&self.days_idle))
            // 3. Menos histórico total → maior prioridade (se habilitado)
            .then(if self.use_history {
                self.historical_count.cmp(&other.historical_count)
            } else {
                Ordering::Equal
            })
            // 4. Hash tiebreak — distribui deterministicamente por data
            .then(self.tiebreak.cmp(&other.tiebreak))
    }
}

/// Gera um hash determinístico baseado em (member_id, occurrence_date).
/// Garante distribuição variada entre datas sem depender da ordem de UUIDs.
pub fn tiebreak_hash(member_id: &str, occurrence_date: &str) -> u64 {
    let mut hasher = DefaultHasher::new();
    member_id.hash(&mut hasher);
    occurrence_date.hash(&mut hasher);
    hasher.finish()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn priority(month: i64, idle: i64, hist: i64, tb: u64) -> CandidatePriority {
        CandidatePriority {
            times_this_month: month,
            days_idle: idle,
            historical_count: hist,
            use_history: true,
            tiebreak: tb,
        }
    }

    #[test]
    fn fewer_times_this_month_wins() {
        let a = priority(0, 10, 5, 0);
        let b = priority(1, 10, 5, 0);
        assert_eq!(a.cmp_priority(&b), Ordering::Less); // a tem prioridade
    }

    #[test]
    fn more_idle_days_wins_when_month_equal() {
        let a = priority(1, 30, 5, 0);
        let b = priority(1, 7, 5, 0);
        assert_eq!(a.cmp_priority(&b), Ordering::Less); // a parado há mais tempo
    }

    #[test]
    fn fewer_historical_wins_when_month_and_idle_equal() {
        let a = priority(1, 30, 2, 0);
        let b = priority(1, 30, 10, 0);
        assert_eq!(a.cmp_priority(&b), Ordering::Less); // a serviu menos no total
    }

    #[test]
    fn tiebreak_hash_differentiates_equal_candidates() {
        let a = priority(0, 9999, 0, 100);
        let b = priority(0, 9999, 0, 200);
        assert_eq!(a.cmp_priority(&b), Ordering::Less); // hash menor ganha
    }

    #[test]
    fn month_count_dominates_over_idle() {
        let a = priority(0, 1, 0, 0); // 0 vezes no mês, idle de 1 dia
        let b = priority(1, 9999, 0, 0); // 1 vez no mês, idle de 9999 dias
        assert_eq!(a.cmp_priority(&b), Ordering::Less); // a ganha por ter 0 vezes no mês
    }

    #[test]
    fn history_disabled_ignores_historical_count() {
        let a = CandidatePriority {
            times_this_month: 0, days_idle: 30, historical_count: 100,
            use_history: false, tiebreak: 50,
        };
        let b = CandidatePriority {
            times_this_month: 0, days_idle: 30, historical_count: 1,
            use_history: false, tiebreak: 50,
        };
        assert_eq!(a.cmp_priority(&b), Ordering::Equal); // histórico ignorado
    }

    #[test]
    fn tiebreak_hash_varies_by_date() {
        let h1 = tiebreak_hash("member-1", "2026-03-01");
        let h2 = tiebreak_hash("member-1", "2026-03-08");
        assert_ne!(h1, h2); // mesmo membro, datas diferentes → hash diferente
    }

    #[test]
    fn tiebreak_hash_varies_by_member() {
        let h1 = tiebreak_hash("member-1", "2026-03-01");
        let h2 = tiebreak_hash("member-2", "2026-03-01");
        assert_ne!(h1, h2); // membros diferentes, mesma data → hash diferente
    }

    #[test]
    fn tiebreak_hash_is_deterministic() {
        let h1 = tiebreak_hash("member-1", "2026-03-01");
        let h2 = tiebreak_hash("member-1", "2026-03-01");
        assert_eq!(h1, h2); // mesma entrada → mesmo resultado
    }
}
