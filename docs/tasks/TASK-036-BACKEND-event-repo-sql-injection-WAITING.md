# TASK-036 — Eliminar SQL Injection em event_repo::update()

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P0 (segurança)  
**Depende de:** nenhuma  
**Estimativa:** S (< 2h)

## Descrição

`event_repo::update()` usa SQL dinâmico com interpolação de string para montar
o `UPDATE`. Campos como `name`, `event_date`, `event_type`, `recurrence` e `notes`
são inseridos diretamente no SQL via `format!()`.

Problema adicional: o campo `event_date` **não faz nem o escape mínimo** de aspas —
é interpolado cru (`format!("event_date = '{}'", v)`).

## Situação Atual

```rust
// event_repo.rs — linhas 30–38
let mut sets = vec!["updated_at = datetime('now')".to_string()];
if let Some(v) = &dto.name       { sets.push(format!("name = '{}'", v.replace('\'', "''"))) }
if let Some(v) = &dto.event_date { sets.push(format!("event_date = '{}'", v)) }  // ❌ sem escape
if let Some(v) = &dto.event_type { sets.push(format!("event_type = '{}'", v)) }  // ❌ sem escape
if let Some(v) = dto.day_of_week { sets.push(format!("day_of_week = {}", v)) }
if let Some(v) = &dto.recurrence { sets.push(format!("recurrence = '{}'", v)) }  // ❌ sem escape
if let Some(v) = &dto.notes      { sets.push(format!("notes = '{}'", v.replace('\'', "''"))) }
let sql = format!("UPDATE events SET {} WHERE id = '{}'", sets.join(", "), id);
```

## Solução

Mesma abordagem da TASK-035: carregar evento atual com `get_by_id()`, montar
query parametrizada com todos os campos (fallback para valor atual).

## Critérios de Aceite

- [ ] `event_repo::update()` não usa `format!()` nem `sqlx::query(&sql)`
- [ ] Todos os parâmetros são bind variables (`?`)
- [ ] `cargo test --lib` passa (incluindo testes do event_service)
- [ ] SQLx cache regenerado (`cargo sqlx prepare`)

## Notas Técnicas

- `day_of_week` é `Option<i64>` — testar o case `None` (deve manter valor atual).
- Events têm 6 campos opcionais no UpdateDto — garantir que atualização parcial funciona.
