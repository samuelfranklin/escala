# TASK-041 — Refatorar squad_service: validators + adicionar testes

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P2 (qualidade)  
**Depende de:** TASK-037 (SQL injection fix), TASK-038 (módulo validators)  
**Estimativa:** S (< 2h)

## Descrição

Aplicar Clean Architecture no `squad_service`:
1. Substituir validação inline de nome pela função do `validators.rs`
2. Adicionar testes unitários (atualmente zero)

O service é simples (20 linhas, 8 funções thin wrapper) — não precisa virar
diretório. Mas precisa compartilhar a validação e ter cobertura mínima.

## Situação Atual

```rust
// squad_service.rs — 20 linhas
pub async fn create_squad(...) {
    if dto.name.trim().is_empty() { ... }  // DRY repetido
    squad_repo::create(pool, dto).await
}

pub async fn update_squad(...) {
    if let Some(ref name) = dto.name {
        if name.trim().is_empty() { ... }  // DRY repetido
    }
    squad_repo::update(pool, id, dto).await
}
// ... zero testes
```

## Situação Alvo

```rust
use super::validators;

pub async fn create_squad(...) {
    validators::require_non_empty("Name", &dto.name)?;
    squad_repo::create(pool, dto).await
}

pub async fn update_squad(...) {
    validators::require_non_empty_opt("Name", dto.name.as_deref())?;
    squad_repo::update(pool, id, dto).await
}

#[cfg(test)]
mod tests {
    // Testes de validação + CRUD integração
}
```

## Critérios de Aceite

- [ ] `squad_service.rs` usa `validators::require_non_empty` / `_opt`
- [ ] ≥ 4 testes: create com nome vazio, update com nome vazio, create ok, update ok
- [ ] `cargo test --lib services::squad_service` passa

## Notas Técnicas

- Service é simples o suficiente para ficar como arquivo único (não precisa diretório)
- Testes de integração precisam de `SqlitePool::connect(":memory:")` + migrations
