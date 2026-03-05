# TASK-004 — CRUD Completo de Squad + Gerenciamento de Membros

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-002  
**Estimativa:** M (2–6h)

---

## Descrição

Implementar a pilha completa do domínio **Squad** (times) seguindo a mesma
arquitetura de camadas de TASK-003. Inclui não apenas o CRUD da entidade Squad,
mas também os commands de **associação membro ↔ squad** via tabela
`members_squads`, que é a base para o algoritmo de geração de escala.

---

## Critérios de Aceite

### Models (`models/squad.rs`)
- [ ] `Squad` struct com todos os campos da spec §5 + derives completos
- [ ] `SquadMember` struct: `{ member_id, squad_id, role, joined_at }` com `sqlx::FromRow`
- [ ] `SquadWithMembers` struct: `{ squad: Squad, members: Vec<Member> }`
- [ ] `CreateSquadDto { name: String, description: Option<String> }`
- [ ] `UpdateSquadDto { name: Option<String>, description: Option<String> }`

### Repo (`db/squad_repo.rs`)
- [ ] `list_all(pool) -> Result<Vec<Squad>>`
- [ ] `get_by_id(pool, id) -> Result<Squad>` — `AppError::NotFound` se ausente
- [ ] `create(pool, dto) -> Result<Squad>` — gera UUID v4
- [ ] `update(pool, id, dto) -> Result<Squad>`
- [ ] `delete(pool, id) -> Result<()>`
- [ ] `get_members(pool, squad_id) -> Result<Vec<Member>>` — JOIN com `members_squads`
- [ ] `add_member(pool, squad_id, member_id, role) -> Result<()>` — `AppError::Conflict` se já existe
- [ ] `remove_member(pool, squad_id, member_id) -> Result<()>` — `AppError::NotFound` se não existe

### Service (`services/squad_service.rs`)
- [ ] `list_squads(pool) -> Result<Vec<Squad>>`
- [ ] `get_squad(pool, id) -> Result<Squad>`
- [ ] `create_squad(pool, dto) -> Result<Squad>`:
  - Valida `name` não vazio → `AppError::Validation`
  - Detecta nome duplicado → `AppError::Conflict`
- [ ] `update_squad(pool, id, dto) -> Result<Squad>`
- [ ] `delete_squad(pool, id) -> Result<()>` — cascade via FK
- [ ] `get_squad_members(pool, squad_id) -> Result<Vec<Member>>`
- [ ] `add_member_to_squad(pool, squad_id, member_id, role) -> Result<()>`:
  - Verifica existência do membro → `AppError::NotFound`
  - Verifica existência do squad → `AppError::NotFound`
- [ ] `remove_member_from_squad(pool, squad_id, member_id) -> Result<()>`

### Commands (`commands/squad.rs`)
- [ ] `get_squads(state) -> Result<Vec<Squad>, AppError>`
- [ ] `get_squad(state, id: String) -> Result<Squad, AppError>`
- [ ] `create_squad(state, dto: CreateSquadDto) -> Result<Squad, AppError>`
- [ ] `update_squad(state, id: String, dto: UpdateSquadDto) -> Result<Squad, AppError>`
- [ ] `delete_squad(state, id: String) -> Result<(), AppError>`
- [ ] `get_squad_members(state, squad_id: String) -> Result<Vec<Member>, AppError>`
- [ ] `add_member_to_squad(state, squad_id: String, member_id: String, role: String) -> Result<(), AppError>`
- [ ] `remove_member_from_squad(state, squad_id: String, member_id: String) -> Result<(), AppError>`
- [ ] Todos registrados em `generate_handler![]`

### Testes
- [ ] Unitários (service):
  - `test_create_squad_validates_empty_name`
  - `test_create_squad_conflict_on_duplicate_name`
- [ ] Integração (repo, SQLite `:memory:`):
  - `test_create_and_list_squads`
  - `test_add_and_remove_member`
  - `test_add_duplicate_member_returns_conflict`
  - `test_delete_squad_cascades_members`
- [ ] Testes passando com cobertura ≥ 75%
- [ ] `cargo clippy -- -D warnings` sem warnings

---

## Notas Técnicas

### Query de Membros do Squad

