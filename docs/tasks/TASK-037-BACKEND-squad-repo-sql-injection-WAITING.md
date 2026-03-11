# TASK-037 — Eliminar SQL Injection em squad_repo::update()

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P0 (segurança)  
**Depende de:** nenhuma  
**Estimativa:** S (< 2h)

## Descrição

`squad_repo::update()` usa SQL dinâmico com interpolação de string para montar
o `UPDATE`. Campos `name` e `description` são inseridos via `format!()`.

## Situação Atual

```rust
// squad_repo.rs — linhas 28–34
let mut sets = vec!["updated_at = datetime('now')".to_string()];
if let Some(v) = &dto.name        { sets.push(format!("name = '{}'", v.replace('\'', "''"))) }
if let Some(v) = &dto.description { sets.push(format!("description = '{}'", v.replace('\'', "''"))) }
let sql = format!("UPDATE squads SET {} WHERE id = '{}'", sets.join(", "), id);
sqlx::query(&sql).execute(pool).await?;
```

## Solução

Mesma abordagem: carregar squad atual, montar `sqlx::query!` parametrizada com todos
os campos. Squad é o mais simples — só tem `name` e `description`.

## Critérios de Aceite

- [ ] `squad_repo::update()` não usa `format!()` nem `sqlx::query(&sql)`
- [ ] Todos os parâmetros são bind variables (`?`)
- [ ] `cargo test --lib` passa
- [ ] SQLx cache regenerado (`cargo sqlx prepare`)
