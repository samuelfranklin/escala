# TASK-040 — Refatorar event_service: validators + separar testes + limpar helpers

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P1 (arquitetura)  
**Depende de:** TASK-036 (SQL injection fix), TASK-038 (módulo validators)  
**Estimativa:** M (2–6h)

## Descrição

Aplicar Clean Architecture no `event_service`:
1. Substituir validações inline pelas funções do `validators.rs`
2. Converter `event_service.rs` em diretório (`event_service/mod.rs` + `tests.rs`)
3. Limpar test helper `create_test_squad()` para usar `squad_repo::create()`
4. Extrair validação de `EventSquadDto` para método ou para `validators.rs`

## Situação Atual

```rust
// event_service.rs — validação complexa inline
pub async fn create_event(...) {
    if dto.name.trim().is_empty() { ... }           // DRY repetido
    if event_type == "regular" {
        if dto.day_of_week.is_none() { ... }        // lógica de domínio inline
        if dto.recurrence.is_none()  { ... }
    } else if dto.event_date...is_empty() { ... }
}

pub async fn set_event_squads(...) {
    for item in &items {
        if item.min_members < 1 { ... }              // validação de DTO inline
        if item.max_members < item.min_members { ... }
        if item.max_members > 10 { ... }
    }
}
```

Test helper com query direta:
```rust
async fn create_test_squad(pool: &SqlitePool, name: &str) -> String {
    sqlx::query("INSERT INTO squads (id, name) VALUES (?, ?)")  // ❌ fura camada
        .bind(&id).bind(name).execute(pool).await.unwrap();
}
```

## Situação Alvo

```rust
// event_service/mod.rs
use super::validators;

pub async fn create_event(...) {
    validators::require_non_empty("Name", &dto.name)?;
    validate_event_type_fields(&dto)?;  // fn privada focada
    event_repo::create(pool, dto).await
}
```

```rust
// tests.rs — helper limpo
async fn create_test_squad(pool: &SqlitePool, name: &str) -> String {
    squad_repo::create(pool, CreateSquadDto { name: name.into(), description: None })
        .await.unwrap().id
}
```

## Critérios de Aceite

- [ ] `event_service/mod.rs` usa `validators` para nome
- [ ] Validação de regras de event_type extraída em função dedicada
- [ ] Validação de `EventSquadDto` extraída (método no DTO ou fn em validators)
- [ ] `event_service/tests.rs` com todos os testes existentes
- [ ] Test helper usa `squad_repo::create()` — zero `sqlx::query` nos testes
- [ ] `cargo test --lib services::event_service` passa

## Notas Técnicas

- Validação de event_type é específica do domínio de eventos — pode ficar como
  `fn validate_event_type_fields()` privada no `mod.rs` (não precisa ir para validators)
- Validação de `EventSquadDto` pode virar `impl EventSquadDto { fn validate(&self) -> Result<()> }`
