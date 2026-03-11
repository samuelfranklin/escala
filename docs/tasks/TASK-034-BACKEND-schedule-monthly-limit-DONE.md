# TASK-034 — Limite Máximo de Escalas por Membro por Mês

**Domínio:** BACKEND  
**Status:** DONE  
**Prioridade:** P2  
**Depende de:** TASK-032 (correção de bugs), TASK-033 (score multi-fator — `monthly_count_map` deve existir)  
**Estimativa:** S (< 2h)

---

## Descrição

Mesmo com o score multi-fator (TASK-033), em times pequenos com muitas ocorrências
um membro pode ser escalado mais vezes no mês do que é saudável para a equipe.
Esta task adiciona um **teto máximo de escalas por membro dentro do mesmo mês**.

Valor padrão: **2 vezes por mês** (constante `MAX_MEMBER_OCCURRENCES_PER_MONTH`).

Quando um membro atinge o limite, ele é excluído dos candidatos para as ocorrências
seguintes do mesmo mês — mesmo que seja o único disponível para o squad. Nesse caso,
o algoritmo retorna um erro informativo ao invés de violar o limite silenciosamente.

---

## Escopo

### Arquivos a modificar

- `src-tauri/src/services/schedule_service.rs`
  - Declarar `const MAX_MEMBER_OCCURRENCES_PER_MONTH: usize = 2;` no topo do módulo
  - No início do processamento de cada ocorrência (Phase 1), **antes** da propagação de
    indisponibilidade de casais: coletar os membros que já atingiram o limite mensal e
    inseri-los no set `unavailable`. A propagação existente (TASK-032) cuidará
    automaticamente de bloquear seus parceiros de casal.
    ```rust
    // Adicionar membros que atingiram o limite mensal ao set unavailable,
    // ANTES da propagação de casais
    for (id, count) in &monthly_count_map {
        if *count >= MAX_MEMBER_OCCURRENCES_PER_MONTH as i64 {
            unavailable.insert(id.clone());
        }
    }
    // ... propagação de casais já existente roda a seguir ...
    ```
  - Diferenciar a mensagem de `AppError::Validation` por causa do limite mensal:
    ```
    "Squad '{name}': membros insuficientes no mês (limite de {MAX} escalas/membro atingido).
     Adicione mais membros ao squad ou reduza o número de eventos."
    ```

---

## Critérios de Aceite

### Comportamento

- [x] Membro que já foi escalado `MAX_MEMBER_OCCURRENCES_PER_MONTH` (2) vezes no mês corrente
  **não aparece como candidato** nas ocorrências seguintes dentro da mesma geração mensal
- [x] A constante `MAX_MEMBER_OCCURRENCES_PER_MONTH = 2` está declarada no topo do arquivo,
  fácil de localizar e alterar futuramente
- [x] Quando `min_members` não pode ser atingido por causa do limite mensal:
  - Retorna `AppError::Validation`
  - Mensagem menciona "limite" ou "MAX_MEMBER_OCCURRENCES_PER_MONTH" — distinguível da
    mensagem genérica de membros indisponíveis por data
- [x] Quando o squad tem membros suficientes para cobrir o mês com o limite:
  geração funciona normalmente sem erros

### Testes unitários — `schedule_service.rs` (módulo `tests`)

- [x] `test_monthly_limit_excludes_member`: candidato com `monthly_count = 2` é removido
  do pool antes da seleção; candidatos restantes são escalados normalmente
- [x] `test_monthly_limit_blocks_couple_partner`: quando membro A atinge o limite mensal,
  seu parceiro de casal B também é bloqueado automaticamente via propagação
- [x] `test_monthly_limit_enough_members`: squad com membros suficientes para cobrir todas
  as ocorrências do mês sem violar o limite — geração funciona sem erros

### Geral

- [x] `cargo test` passa sem erros (26/26 — incluindo todos os testes de TASK-032 e TASK-033)
- [x] `cargo clippy` sem warnings novos

---

## Notas Técnicas

- O filtro por `monthly_count_map` deve ocorrer **antes** da ordenação por score e antes da
  propagação de indisponibilidade de casais: inserir os membros que atingiram o limite no set
  `unavailable`, e deixar a propagação (já existente desde TASK-032) excluir seus parceiros
  automaticamente. Isso garante consistência sem código especial de casal no loop de seleção.
- O `monthly_count_map` criado em TASK-033 (resultado do `count_map` mutável de TASK-032)
  é a fonte de verdade para o contador mensal — esta task apenas adiciona a verificação de teto.
- Em `generate_schedule` (evento único): o `monthly_count_map` começa zerado a cada chamada.
  O limite não terá efeito prático num único evento, mas o código deve ser consistente e
  não precisar de desvio especial.
- Não expor o limite como parâmetro de API nesta task. Configurabilidade por evento ou
  squad pode ser endereçada em task futura.
- **Casal e limite mensal:** quando A atinge o limite mensal, ele é inserido em `unavailable`.
  A propagação de casais já existente (TASK-032) inserirá B automaticamente. Resultado:
  o par inteiro fica bloqueado naquela ocorrência — sem código atômico de casal necessário.

---

## Progresso

- [x] Declarar constante `MAX_MEMBER_OCCURRENCES_PER_MONTH` no topo do módulo
- [x] Adicionar filtro de limite no loop de candidatos (Phase 1), após filtro de `unavailable`
- [x] Ajustar mensagem de `AppError::Validation` para diferenciar "limite mensal" de "indisponível por data"
- [x] Escrever 3 testes unitários listados acima
- [x] `cargo test` verde — 26/26 passando
