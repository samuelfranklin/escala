# TASK-033 — Score Multi-fator de Rotatividade no Algoritmo de Escala

**Domínio:** BACKEND  
**Status:** DONE  
**Prioridade:** P1  
**Depende de:** TASK-032 (correção dos bugs críticos do algoritmo)  
**Estimativa:** M (2–6h)

---

## Descrição

O critério de rotatividade atual usa apenas a contagem total histórica de escalas
por membro (`count asc`). Isso ignora o **tempo decorrido desde o último serviço**:
um membro que serviu muitas vezes no passado mas não serve há 3 meses deveria ter
prioridade maior do que outro com contagem menor mas que serviu na semana passada.

Substituir a ordenação simples por um **score ponderado multi-fator** que equilibre
frequência histórica, tempo de descanso e uso no mês atual.

### Fórmula do Score

```
score(m) = (dias_sem_servir(m) + 1)
           ─────────────────────────────────────────────────
           (count_historico(m) + 1) × (vezes_no_mes(m) + 1)
```

- **`dias_sem_servir`**: dias desde a última `occurrence_date` do membro.
  Membro nunca escalado → valor sentinela `9999` (prioridade máxima).
- **`count_historico`**: total de escalas fora do mês atual (já existente no código).
- **`vezes_no_mes`**: contador incrementado a cada alocação durante a Phase 1
  (introduzido pelo `count_map` mutável da TASK-032).

Score **maior = maior prioridade** (ordenação `desc`). Substitui o `count asc` atual.

---

## Escopo

### Arquivos a modificar

- `src-tauri/src/services/schedule_service.rs`
  - Adicionar query para `last_service_date` por membro (MAX de `occurrence_date`
    excluindo o mês atual), carregada uma vez antes do loop principal
  - Adicionar `days_idle_map: HashMap<String, i64>` populado com o resultado
  - Implementar função pura `compute_score(count_historico: i64, days_idle: i64, vezes_no_mes: i64) -> f64`
  - Substituir `sort_by(count asc)` por `sort_by(score desc)` em ambas as funções:
    `generate_schedule` e `generate_month_schedule`
  - O `monthly_count_map` (renomear o `count_map` mutável da TASK-032 para clareza)
    continua sendo usado como `vezes_no_mes`

---

## Critérios de Aceite

### Lógica do Score

- [x] Membro nunca escalado tem score maior que qualquer membro já escalado com mesma `vezes_no_mes`
- [x] Dois membros com mesmo `count_historico` e `vezes_no_mes`: aquele que serviu há mais tempo tem score maior
- [x] Membro que já foi escalado 2x no mês em curso tem score menor que membro ainda não escalado no mês, independente do histórico anterior
- [x] Query de `last_service_date` executada uma única vez antes do loop (sem N+1 queries)

### Testes unitários — `schedule_service.rs` (módulo `tests`)

- [x] `test_score_never_scheduled`: membro com `count=0, days_idle=9999, monthly=0` tem score maior que membro com `count=1, days_idle=30, monthly=0`
- [x] `test_score_recent_vs_old`: A com `days_idle=1`, B com `days_idle=60`, mesmo `count` e `monthly` → score de B maior → B selecionado primeiro
- [x] `test_score_monthly_count_penalty`: A com `vezes_no_mes=2`, B com `vezes_no_mes=0`, mesmo `count` e `days_idle` → score de B maior → B selecionado primeiro
- [x] `test_score_combined`: três membros com combinações distintas dos três fatores — resultado de ordenação por score bate com expectativa calculada manualmente

### Geral

- [x] `cargo test` 23/23 passou (incluindo todos os testes de TASK-032)
- [x] `cargo clippy` sem warnings novos

---

## Notas Técnicas

- Query sugerida para `last_service_date`:
  ```sql
  SELECT member_id as "member_id!", MAX(occurrence_date) as "last_date!"
  FROM schedule_entries
  WHERE occurrence_date NOT LIKE ?
  GROUP BY member_id
  ```
  onde `?` é o padrão `YYYY-MM%` do mês atual.
- `days_idle` calculado como: `(data_da_ocorrência_atual - last_date).num_days()`.
  Para `generate_month_schedule`, usar a `occurrence_date` da ocorrência sendo processada
  como referência (não `chrono::Local::now()`), garantindo determinismo nos testes.
- Para membros sem linha no resultado da query (nunca escalados): usar `days_idle = 9999`.
- A função `compute_score` deve ser pura e independente de I/O para facilitar testes
  unitários sem banco de dados.
- O tipo de retorno `f64` é suficiente; não é necessário precisão arbitrária.
- Não alterar a assinatura dos commands Tauri — a mudança é completamente interna ao service.

---

## Progresso

- [x] Adicionar query `last_service_date` em `schedule_service.rs`
- [x] Popular `days_idle_map` / `last_date_map` antes do loop
- [x] Implementar função pura `compute_score(count_historico, days_idle, vezes_no_mes) -> f64`
- [x] Substituir `sort_by` em `generate_schedule` para usar `compute_score`
- [x] Substituir `sort_by` em `generate_month_schedule` para usar `compute_score`
- [x] `count_map` renomeado: `historical_count_map` (imutável) + `monthly_count_map` (mut)
- [x] Escrever 4 testes unitários do score
- [x] `cargo test` 23/23 verde
- [x] Cache `.sqlx` regenerado com `cargo sqlx prepare`
