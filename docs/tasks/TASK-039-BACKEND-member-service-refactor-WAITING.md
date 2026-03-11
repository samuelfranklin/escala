# TASK-039 — Refatorar member_service: validators + separar testes

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P1 (arquitetura)  
**Depende de:** TASK-035 (SQL injection fix), TASK-038 (módulo validators)  
**Estimativa:** S (< 2h)

## Descrição

Aplicar Clean Architecture no `member_service`:
1. Substituir validações inline pelas funções do `validators.rs`
2. Converter `member_service.rs` em diretório (`member_service/mod.rs` + `tests.rs`)
3. Remover `validate_email()` privada (agora vive no módulo compartilhado)

## Situação Atual

```rust
// member_service.rs — validação duplicada e inline
fn validate_email(email: &str) -> bool { ... } // privada, não reutilizável

pub async fn create_member(...) {
    if dto.name.trim().is_empty() { ... }     // DRY: repetido em 3 services
    if !validate_email(email) { ... }          // acoplado ao service
}

pub async fn update_member(...) {
    if name.trim().is_empty() { ... }          // DRY duplicado do create
    if !validate_email(email) { ... }          // DRY duplicado do create
}
```

## Situação Alvo

```rust
// member_service/mod.rs — limpo, composição com validators
use super::validators;

pub async fn create_member(...) {
    validators::require_non_empty("Name", &dto.name)?;
    if let Some(ref email) = dto.email { validators::validate_email(email)?; }
    member_repo::create(pool, dto).await
}
```

## Critérios de Aceite

- [ ] `member_service/mod.rs` usa funções de `validators` (sem validação inline)
- [ ] `member_service/tests.rs` contém os 4 testes existentes (adaptados)
- [ ] `fn validate_email()` removida do member_service (vive em validators)
- [ ] Zero `#[cfg(test)]` no `mod.rs`
- [ ] `cargo test --lib services::member_service` passa
