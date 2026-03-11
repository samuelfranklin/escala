# TASK-043 — availability_service: validação de data + testes

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P2 (qualidade)  
**Depende de:** TASK-038 (módulo validators)  
**Estimativa:** S (< 1h)

## Descrição

O `availability_service` valida apenas que a data não é vazia. Precisa:
1. Usar validators compartilhado para validação de string não-vazia
2. Adicionar validação de formato de data (`YYYY-MM-DD`)
3. Adicionar testes unitários (atualmente zero)

## Situação Atual

```rust
// availability_service.rs — 11 linhas
pub async fn create_availability(...) {
    if dto.unavailable_date.trim().is_empty() {
        return Err("A data de indisponibilidade é obrigatória.".into());
    }
    availability_repo::create(pool, dto).await
}
// ... zero testes
```

## Situação Alvo

```rust
use super::validators;

pub async fn create_availability(...) {
    validators::require_valid_date("Data de indisponibilidade", &dto.unavailable_date)?;
    availability_repo::create(pool, dto).await
}

#[cfg(test)]
mod tests {
    // Testes: data vazia, data formato inválido, create/delete ok
}
```

## Critérios de Aceite

- [ ] `availability_service.rs` usa `validators::require_valid_date`
- [ ] ≥ 4 testes: data vazia, formato inválido (ex: "31/12/2024"), create ok, delete ok
- [ ] `cargo test --lib services::availability_service` passa

## Notas Técnicas

- `require_valid_date` pode usar `chrono::NaiveDate::parse_from_str(s, "%Y-%m-%d")`
- Service é simples — arquivo único, sem necessidade de diretório
