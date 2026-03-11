use serde::{Deserialize, Serialize};

/// Configuração global das regras do gerador de escala.
/// Persiste na tabela `schedule_config` (linha única, id = 1).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleConfig {
    pub apply_monthly_limit: bool,
    pub max_occurrences_per_month: i64,
    pub propagate_couples: bool,
    pub apply_history_scoring: bool,
}

impl Default for ScheduleConfig {
    fn default() -> Self {
        Self {
            apply_monthly_limit: true,
            max_occurrences_per_month: 2,
            propagate_couples: true,
            apply_history_scoring: true,
        }
    }
}

/// DTO para atualização da configuração — todos os campos obrigatórios
/// (o frontend sempre envia o estado completo do formulário).
#[derive(Debug, Clone, Deserialize)]
pub struct UpdateScheduleConfigDto {
    pub apply_monthly_limit: bool,
    pub max_occurrences_per_month: i64,
    pub propagate_couples: bool,
    pub apply_history_scoring: bool,
}
