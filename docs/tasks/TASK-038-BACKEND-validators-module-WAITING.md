# TASK-038 — Criar módulo validators.rs com funções puras DRY

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P1 (arquitetura)  
**Depende de:** nenhuma  
**Estimativa:** S (< 2h)

## Descrição

Validações idênticas estão espalhadas em 3 serviços (member, event, squad).
O padrão `name.trim().is_empty()` aparece **6 vezes** no código de produção.
A validação de email está presa dentro do `member_service` como função privada.

Criar um módulo `services/validators.rs` com funções puras e testáveis que
centralizam toda lógica de validação.

## Violações DRY Identificadas

| Padrão duplicado | Onde aparece | Ocorrências |
|-----------------|-------------|-------------|
| `name.trim().is_empty()` → "Name cannot be empty" | member, event, squad (create + update) | 6× |
| `validate_email()` | member_service (privada) | 2× |
| Validação de campo vazio genérico | availability (date), couple (ids) | 2× |

## Entregáveis

### `services/validators.rs`

```rust
use crate::errors::AppError;

/// Valida que um campo obrigatório não está vazio (após trim).
pub fn require_non_empty(field_name: &str, value: &str) -> Result<(), AppError> {
    if value.trim().is_empty() {
        return Err(AppError::Validation(format!("{} cannot be empty", field_name)));
    }
    Ok(())
}

/// Valida campo obrigatório em update (Option) — só valida se presente.
pub fn require_non_empty_opt(field_name: &str, value: Option<&str>) -> Result<(), AppError> {
    if let Some(v) = value {
        require_non_empty(field_name, v)?;
    }
    Ok(())
}

/// Valida formato de email (se não vazio).
pub fn validate_email(email: &str) -> Result<(), AppError> {
    if email.is_empty() { return Ok(()); }
    let parts: Vec<&str> = email.split('@').collect();
    if parts.len() != 2 || !parts[1].contains('.') {
        return Err(AppError::Validation("Invalid email format".into()));
    }
    Ok(())
}

/// Valida formato de data YYYY-MM-DD.
pub fn validate_date_format(value: &str) -> Result<(), AppError> {
    chrono::NaiveDate::parse_from_str(value, "%Y-%m-%d")
        .map_err(|_| AppError::Validation("Invalid date format (expected YYYY-MM-DD)".into()))?;
    Ok(())
}
```

## Critérios de Aceite

- [ ] `services/validators.rs` existe com funções puras (sem I/O, sem async)
- [ ] Testes unitários para cada função (≥ 8 testes: happy + edge cases)
- [ ] `services/mod.rs` exporta `pub mod validators;`
- [ ] `cargo test --lib services::validators` passa
- [ ] Nenhum serviço alterado ainda — isso é só a fundação (TASK-039/040/041 consomem)

## Notas Técnicas

- Funções retornam `Result<(), AppError>` (padronizado com o resto)
- Sem dependências externas além de `chrono` (já no projeto) e `AppError`
- API funcional: composição via `?` operator
