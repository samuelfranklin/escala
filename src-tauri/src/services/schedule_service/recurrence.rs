use chrono::{Datelike, NaiveDate};

/// Calcula as datas de ocorrência de um evento recorrente dentro de um mês.
///
/// `day_of_week`: 0 = Domingo, 1 = Segunda, ..., 6 = Sábado (convenção JS/SQLite).
/// `recurrence`: "weekly", "biweekly", "monthly_1" .. "monthly_4".
pub fn occurrence_dates(year: i32, month_num: u32, day_of_week: i64, recurrence: &str) -> Vec<String> {
    let target: u32 = match day_of_week {
        0 => 6,
        n @ 1..=6 => (n - 1) as u32,
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

    #[test]
    fn weekly_domingo_marco_2026() {
        let dates = occurrence_dates(2026, 3, 0, "weekly");
        assert_eq!(dates, vec!["2026-03-01", "2026-03-08", "2026-03-15", "2026-03-22", "2026-03-29"]);
    }

    #[test]
    fn monthly_2_terca_marco_2026() {
        let dates = occurrence_dates(2026, 3, 2, "monthly_2");
        assert_eq!(dates, vec!["2026-03-10"]);
    }

    #[test]
    fn biweekly_domingo_marco_2026() {
        let dates = occurrence_dates(2026, 3, 0, "biweekly");
        assert_eq!(dates, vec!["2026-03-01", "2026-03-15", "2026-03-29"]);
    }

    #[test]
    fn monthly_1_segunda_marco_2026() {
        let dates = occurrence_dates(2026, 3, 1, "monthly_1");
        assert_eq!(dates, vec!["2026-03-02"]);
    }

    #[test]
    fn invalid_day_of_week_returns_empty() {
        let dates = occurrence_dates(2026, 3, 7, "weekly");
        assert!(dates.is_empty());
    }

    #[test]
    fn unknown_recurrence_returns_empty() {
        let dates = occurrence_dates(2026, 3, 0, "daily");
        assert!(dates.is_empty());
    }
}
