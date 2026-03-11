# TASK-032 — Correção do Algoritmo de Geração de Escala

**Domínio:** BACKEND  
**Status:** DONE  
**Prioridade:** P0 — bugs críticos que invalidam a feature principal  
**Depende de:** TASK-006 (schedule generator — base do código a corrigir)  
**Estimativa:** L (6–12h)

---

## Descrição

O motor de geração de escala (`schedule_service.rs`) possui quatro bugs que tornam
a escala gerada incorreta em dois cenários comuns: uso de casais e geração mensal.

### Bug #1 — Semântica dos casais invertida (crítico)

A tabela `couples` define pares que **servem na mesma data** (tutela de indisponibilidade
mútua): se um não pode servir, o outro também não serve naquela ocorrência.
Os dois podem estar em **squads distintos** — a restrição é temporal, não de squad.

O algoritmo original implementava o comportamento **inverso**: quando o membro A já estava
em `globally_allocated`, o membro B (seu parceiro) era bloqueado via `continue 'outer`.
Resultado: o casal nunca coincidia — exatamente o oposto do esperado.

**Implementação correta (aplicada):** propagação de indisponibilidade antes do loop de seleção.
Após carregar `unavailable` do banco, o set é expandido: para cada membro em `unavailable`,
seus parceiros também são inseridos. O loop de seleção por squad é greedy simples,
sem lógica especial de casal — a restrição já foi resolvida na etapa anterior.

```rust
// Propaga indisponibilidade para parceiros de casal
let extra_unavailable: Vec<String> = unavailable.iter()
    .flat_map(|id| couple_map.get(id.as_str()).into_iter().flatten().cloned())
    .collect();
unavailable.extend(extra_unavailable);
```

### Bug #2 — `count_map` não atualizado intra-mês (crítico)

Em `generate_month_schedule`, o `count_map` (contagem de escalas anteriores por membro)
é carregado **uma única vez** antes do loop de ocorrências e nunca é incrementado após
cada alocação na Phase 1.

Resultado: o membro com menor contagem histórica é selecionado para **todas** as
ocorrências do mês. Ex.: João com 2 escalas históricas é escolhido em todos os 4
domingos de março, enquanto Maria com 5 históricas nunca é escolhida no mês.

### Bug #3 — Casal com disponibilidade parcial

Se A está disponível mas B (parceiro) está em `unavailable` na data, o algoritmo
atual escalaria A sozinho (ou bloquearia A erroneamente, conforme Bug #1). Com a
semântica correta de "juntos ou nenhum": se qualquer um dos dois está indisponível
na data, nenhum deve ser escalado naquela ocorrência.

### Bug #4 — `globally_allocated` não cobre a unidade casal

Ao alocar o casal A+B atomicamente, ambos devem ser inseridos em `globally_allocated`
imediatamente, impedindo que A ou B seja escalado novamente em outro squad da mesma
ocorrência. O código atual não trata isso para a unidade casal.

---

## Escopo

### Arquivos a modificar

- `src-tauri/src/services/schedule_service.rs` — algoritmo de seleção em ambas as
  funções: `generate_schedule` e `generate_month_schedule`
- `src/routes/couples/+page.svelte` — corrigir texto descritivo da página
  (atualmente diz "não são escalados juntos"; deve dizer "são sempre escalados juntos")

### Algoritmo corrigido — lógica de seleção por squad

```
// Fase pré-seleção (uma vez por ocorrência):
1. Carregar unavailable da DB (indisponibilidades declaradas na data)
2. Expandir unavailable: para cada id em unavailable, adicionar seus parceiros de casal
   → se um do casal está bloqueado, o outro também fica bloqueado naquela ocorrência

// Por squad (greedy simples, sem lógica especial de casal):
Para cada candidato c (ordenado por count asc):
  se len(alocados) >= max: para
  se c ∈ unavailable (expandido): pula   [filtrado antes de chegar aqui]
  se c ∈ globally_allocated: pula        [já alocado em outro squad nesta ocorrência]
  aloca c
  globally_allocated.insert(c)
  count_map[c] += 1
```

O `count_map` é `mut` e incrementado a cada alocação dentro da Phase 1
de `generate_month_schedule`, garantindo rotatividade correta entre ocorrências.

---

## Critérios de Aceite

### Backend — `schedule_service.rs`

- [x] Se um dos dois do casal está em `unavailable` na data: nenhum dos dois é escalado naquela ocorrência (propagação automática via expansão do set)
- [x] A e B são casal em **squads distintos** (ex.: Som e Luzes): ambos são selecionados normalmente quando ambos estão disponíveis, cada um pelo greedy do seu squad
- [x] A disponível, B indisponível → A também é excluído por propagação de indisponibilidade
- [x] `count_map` incrementado após cada alocação na Phase 1 de `generate_month_schedule`
- [x] Em um mês com 4 ocorrências e 4 membros com counts iguais: cada membro aparece em exatamente 1 ocorrência (distribuição round-robin)
- [x] Funções `generate_schedule` e `generate_month_schedule` ambas corrigidas com a mesma lógica

### Testes unitários — `schedule_service.rs` (módulo `tests`)

- [x] `test_couple_same_squad_both_available`: A e B casal, ambos disponíveis no mesmo squad → ambos no resultado
- [x] `test_couple_partner_in_different_squad_not_blocked`: A (Som) e B (Luzes); apenas A nos candidatos; B não indisponível → A selecionado normalmente
- [x] `test_couple_one_unavailable_propagates`: B em `unavailable` → A excluído por propagação; C (sem casal) alocado normalmente
- [x] `test_count_map_updated_between_occurrences`: 4 ocorrências acumulando `count_map` → membro diferente selecionado em cada rodada
- [x] `test_rotation_prioritizes_less_scheduled`, `test_max_members_respected`, testes de `occurrence_dates`: todos passando

### Frontend — `src/routes/couples/+page.svelte`

- [x] Texto `<p>` alterado para *"Casais cadastrados são sempre escalados juntos no mesmo evento."*

### Geral

- [x] `cargo test` 19/19 passou
- [x] `cargo clippy` sem warnings novos
- [x] `tsc --noEmit` no frontend sem erros

---

## Notas Técnicas

- A função auxiliar `select_members` recebe `unavailable: &HashSet<String>` e internamente
  realiza a propagação de casal antes de filtrar candidatos.
- O `count_map` na Phase 1 de `generate_month_schedule` é `mut` e incrementado a cada
  alocação, garantindo rotatividade intra-mês.
- **Casais em squads distintos (decisão de design):** A restrição é temporal, não de squad.
  A propagação de indisponibilidade garante que, se um do casal está bloqueado naquela data,
  o outro também fica bloqueado — independente do squad de cada um. Quando ambos estão
  disponíveis, cada um é selecionado pelo greedy do seu próprio squad.
- A Phase 2 (transação atômica de DB) não foi alterada.

---

## Progresso

- [x] Atualizar assinatura e lógica de `select_members` com propagação de casal
- [x] Implementar propagação de indisponibilidade em `generate_schedule`
- [x] Implementar propagação de indisponibilidade em `generate_month_schedule`
- [x] Tornar `count_map` mutável e incrementar a cada alocação na Phase 1
- [x] Escrever/atualizar testes unitários
- [x] `cargo test` verde (19/19)
- [x] Corrigir texto da página `/couples` no frontend
- [x] `tsc --noEmit` verde
