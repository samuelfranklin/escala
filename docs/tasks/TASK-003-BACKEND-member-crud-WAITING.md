# TASK-003 — CRUD Completo de Member

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-002  
**Estimativa:** M (2–6h)

---

## Descrição

Implementar a pilha completa do domínio **Member** seguindo a arquitetura em
camadas da spec §3:

```
commands/member.rs          ← interface Tauri (IPC)
services/member_service.rs  ← lógica de negócio e validação
db/member_repo.rs           ← queries SQLx
models/member.rs            ← structs + DTOs + enums
```

Inclui testes unitários (service) e de integração (repo + SQLite in-memory).

---

## Critérios de Aceite

### Models (`models/member.rs`)
- [ ] `Member` struct com todos os campos da spec §5 + `#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]`
- [ ] `MemberRank` enum: `Leader | Trainer | Member | Recruit` com `#[sqlx(type_name = "TEXT", rename_all = "lowercase")]`
- [ ] `CreateMemberDto` (campos opcionais conforme spec)
- [ ] `UpdateMemberDto` (todos os campos `Option<T>`)

### Repo (`db/member_repo.rs`)
- [ ] `list_all(pool) -> Result<Vec<Member>>`
- [ ] `get_by_id(pool, id) -> Result<Member>` — retorna `AppError::NotFound` se ausente
- [ ] `create(pool, dto) -> Result<Member>` — gera UUID v4, seta `created_at`/`updated_at`
- [ ] `update(pool, id, dto) -> Result<Member>` — atualiza apenas campos `Some(v)`, seta `updated_at`
- [ ] `delete(pool, id) -> Result<()>` — retorna `AppError::NotFound` se id não existe
- [ ] Todas as queries usam **prepared statements** SQLx (`query_as!` ou `query!`)

### Service (`services/member_service.rs`)
- [ ] `list_members(pool) -> Result<Vec<Member>>`
- [ ] `get_member(pool, id) -> Result<Member>`
- [ ] `create_member(pool, dto) -> Result<Member>`:
  - Valida `name` não vazio → `AppError::Validation`
  - Valida formato de email se presente → `AppError::Validation`
  - Detecta email duplicado → `AppError::Conflict`
- [ ] `update_member(pool, id, dto) -> Result<Member>`
- [ ] `delete_member(pool, id) -> Result<()>`

### Commands (`commands/member.rs`)
- [ ] `get_members(state) -> Result<Vec<Member>, AppError>`
- [ ] `get_member(state, id: String) -> Result<Member, AppError>`
- [ ] `create_member(state, dto: CreateMemberDto) -> Result<Member, AppError>`
- [ ] `update_member(state, id: String, dto: UpdateMemberDto) -> Result<Member, AppError>`
- [ ] `delete_member(state, id: String) -> Result<(), AppError>`
- [ ] Todos registrados em `tauri::generate_handler![]` no `lib.rs`

### Testes
- [ ] Unitários em `services/member_service.rs`:
  - `test_create_validates_empty_name`
  - `test_create_validates_email_format`
- [ ] Integração em `db/member_repo.rs` (SQLite `:memory:`):
  - `test_create_and_get_member`
  - `test_update_member`
  - `test_delete_member`
  - `test_get_nonexistent_returns_not_found`
- [ ] Testes passando com cobertura ≥ 75%
- [ ] `cargo clippy -- -D warnings` sem warnings

---

## Notas Técnicas

### Geração de ID

```rust
use uuid::Uuid;
let id = Uuid::new_v4().to_string().replace("-", "");
```

### Padrão de Command (spec §6)

```rust
#[tauri::command]
pub async fn get_members(
    state: tauri::State<'_, AppState>
) -> Result<Vec<Member>, AppError> {
    member_service::list_members(&state.db).await
}
```

### Validação de Email (simples)

```rust
fn is_valid_email(email: &str) -> bool {
    email.contains('@') && email.contains('.')
}
```

### Referências

- spec §5 — schema `members`
- spec §6 — padrão de commands
- PDR-RUST-001 — padrões Rust do projeto

---

## Progresso

- [ ] Implementar `models/member.rs` (struct + enum + DTOs)
- [ ] Implementar `db/member_repo.rs` (5 funções)
- [ ] Escrever testes de integração do repo
- [ ] Implementar `services/member_service.rs` (5 funções + validações)
- [ ] Escrever testes unitários do service
- [ ] Implementar `commands/member.rs` (5 commands)
- [ ] Registrar commands no `lib.rs`
- [ ] Verificar `cargo clippy` sem warnings
- [ ] Confirmar cobertura ≥ 75%
- [ ] Commit: `feat(members): implement full CRUD [TASK-003]`
