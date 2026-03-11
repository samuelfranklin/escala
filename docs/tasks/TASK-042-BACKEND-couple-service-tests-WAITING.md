# TASK-042 — couple_service: adicionar testes

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P2 (qualidade)  
**Depende de:** —  
**Estimativa:** S (< 1h)

## Descrição

O `couple_service` possui apenas 1 validação (`a != b`) e zero testes.
Adicionar testes unitários para garantir cobertura.

## Situação Atual

```rust
// couple_service.rs — 11 linhas
pub async fn create_couple(...) {
    if dto.member_a_id == dto.member_b_id {
        return Err("Os membros de um casal devem ser diferentes.".into());
    }
    couple_repo::create(pool, dto).await
}
// ... zero testes
```

## Situação Alvo

```rust
// couple_service.rs
pub async fn create_couple(...) {
    if dto.member_a_id == dto.member_b_id {
        return Err("Os membros de um casal devem ser diferentes.".into());
    }
    couple_repo::create(pool, dto).await
}

#[cfg(test)]
mod tests {
    // Testes: self-couple rejeitado, create/delete ok
}
```

## Critérios de Aceite

- [ ] ≥ 3 testes: auto-casal rejeitado, create ok, delete ok
- [ ] `cargo test --lib services::couple_service` passa

## Notas Técnicas

- Service é extremamente simples — não precisa de refatoração estrutural
- Validação `a != b` é específica demais para extrair para validators.rs
- Testes precisam de `SqlitePool::connect(":memory:")` + migrations
