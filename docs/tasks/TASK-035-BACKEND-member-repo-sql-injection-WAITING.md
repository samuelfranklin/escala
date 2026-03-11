# TASK-035 — Eliminar SQL Injection em member_repo::update()

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P0 (segurança)  
**Depende de:** nenhuma  
**Estimativa:** S (< 2h)

## Descrição

`member_repo::update()` usa SQL dinâmico com interpolação de string para montar
o `UPDATE`. Valores de campos como `name`, `email`, `phone`, `instagram` e `rank`
são inseridos diretamente no SQL via `format!()`, criando vulnerabilidade de injeção.

O escape manual (`v.replace('\'', "''")`) é insuficiente — não cobre outros vetores
de ataque (ex.: valores com caractere nulo, unicode malicioso).

## Situação Atual

```rust
// member_repo.rs — linhas 51–62
let mut sets = vec!["updated_at = datetime('now')".to_string()];
if let Some(v) = &dto.name { sets.push(format!("name = '{}'", v.replace('\'', "''"))) }
// ... mais campos ...
let sql = format!("UPDATE members SET {} WHERE id = '{}'", sets.join(", "), id);
sqlx::query(&sql).execute(pool).await?;
```

## Solução

Substituir por query parametrizada com `sqlx::query!`. Abordagem: carregar o membro
atual com `get_by_id()` e usar `COALESCE`-style no Rust (fallback para valor atual
quando o campo não foi fornecido no DTO).

```rust
let current = get_by_id(pool, id).await?;
sqlx::query!(
    "UPDATE members SET name = ?, email = ?, phone = ?, instagram = ?,
     rank = ?, active = ?, updated_at = datetime('now') WHERE id = ?",
    dto.name.as_deref().unwrap_or(&current.name),
    // ... etc
    id
).execute(pool).await?;
```

## Critérios de Aceite

- [ ] `member_repo::update()` não usa `format!()` nem `sqlx::query(&sql)`
- [ ] Todos os parâmetros são bind variables (`?`)
- [ ] `cargo test --lib` passa (incluindo testes do member_service)
- [ ] SQLx cache regenerado (`cargo sqlx prepare`)

## Notas Técnicas

- O campo `active` é `bool` no DTO mas `i32` no SQLite — converter na borda.
- Testar com payload contendo `'; DROP TABLE members; --` para confirmar proteção.
