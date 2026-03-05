# TASK-007 — Commands de Couple e Availability

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-002  
**Estimativa:** S (< 2h)

---

## Descrição

Implementar as pilhas completas dos domínios **Couple** (restrição de par —
dois membros que sempre servem juntos ou nenhum serve) e **Availability**
(período de indisponibilidade de um membro por data).

Ambos os domínios são relativamente simples em termos de CRUD, mas são
**dados críticos** consumidos pelo algoritmo de geração de escala (TASK-006).
Entregá-los com boa cobertura de testes garante que o motor funcione
corretamente em todos os cenários.

---

## Critérios de Aceite

### COUPLE

#### Models (`models/` — adicionar em `availability.rs` ou arquivo próprio)
- [ ] `Couple` struct: `{ id, member_a_id, member_b_id, created_at }` + derives
- [ ] `CoupleWithMembers` struct: `{ couple: Couple, member_a: Member, member_b: Member }`
- [ ] `CreateCoupleDto { member_a_id: String, member_b_id: String }`

#### Repo (`db/couple_repo.rs`)
- [ ] `list_all(pool) -> Result<Vec<Couple>>`
- [ ] `list_with_members(pool) -> Result<Vec<CoupleWithMembers>>` — JOIN com `members`
- [ ] `create(pool, dto) -> Result<Couple>`:
  - Normalizar: gravar sempre `member_a_id < member_b_id` (ordem alfabética)
    para evitar duplicatas invertidas
- [ ] `delete(pool, id) -> Result<()>`
- [ ] `get_couple_partner(pool, member_id) -> Result<Option<String>>` — retorna o ID do par se existir

#### Service (`services/couple_service.rs`)
- [ ] `list_couples(pool) -> Result<Vec<CoupleWithMembers>>`
- [ ] `create_couple(pool, dto) -> Result<Couple>`:
  - Verifica existência de ambos os membros → `AppError::NotFound`
  - Verifica que `member_a_id != member_b_id` → `AppError::Validation`
  - Verifica que par não existe já (em qualquer ordem) → `AppError::Conflict`
- [ ] `delete_couple(pool, id) -> Result<()>`

#### Commands (`commands/couple.rs`)
- [ ] `get_couples(state) -> Result<Vec<CoupleWithMembers>, AppError>`
- [ ] `create_couple(state, dto: CreateCoupleDto) -> Result<Couple, AppError>`
- [ ] `delete_couple(state, id: String) -> Result<(), AppError>`

---

### AVAILABILITY

#### Models (`models/availability.rs`)
- [ ] `Availability` struct:
  `{ id, member_id, start_date, end_date, reason, created_at }` + derives
- [ ] `CreateAvailabilityDto { member_id, start_date, end_date, reason }`
- [ ] `UpdateAvailabilityDto { start_date, end_date, reason }` (todos `Option<T>`)

#### Repo (`db/availability_repo.rs`)
- [ ] `list_for_member(pool, member_id) -> Result<Vec<Availability>>`
- [ ] `list_all(pool) -> Result<Vec<Availability>>`
- [ ] `create(pool, dto) -> Result<Availability>`
- [ ] `update(pool, id, dto) -> Result<Availability>`
- [ ] `delete(pool, id) -> Result<()>`
- [ ] `get_unavailable_member_ids(pool, date: &str) -> Result<Vec<String>>`:
  — retorna IDs de membros onde `start_date <= date <= end_date`
  — **esta é a função mais crítica: usada diretamente pelo schedule_service**

#### Service (`services/availability_service.rs`)
- [ ] `list_availability_for_member(pool, member_id) -> Result<Vec<Availability>>`
- [ ] `create_availability(pool, dto) -> Result<Availability>`:
  - Verifica existência do membro → `AppError::NotFound`
  - Valida `start_date <= end_date` → `AppError::Validation`
  - Valida formato ISO de datas (`YYYY-MM-DD`) → `AppError::Validation`
- [ ] `update_availability(pool, id, dto) -> Result<Availability>`
- [ ] `delete_availability(pool, id) -> Result<()>`
- [ ] `get_unavailable_on_date(pool, date) -> Result<Vec<String>>`

#### Commands (`commands/availability.rs`)
- [ ] `get_member_availability(state, member_id: String) -> Result<Vec<Availability>, AppError>`
- [ ] `create_availability(state, dto: CreateAvailabilityDto) -> Result<Availability, AppError>`
- [ ] `update_availability(state, id: String, dto: UpdateAvailabilityDto) -> Result<Availability, AppError>`
- [ ] `delete_availability(state, id: String) -> Result<(), AppError>`

---

### Testes (Couple)
- [ ] Unitários (service):
  - `test_create_couple_same_member_returns_validation`
  - `test_create_couple_conflict_on_duplicate`
- [ ] Integração (repo):
  - `test_create_and_list_couples`
  - `test_couple_normalizes_member_order`
  - `test_get_partner_returns_correct_id`
  - `test_delete_couple_removes_pair`

### Testes (Availability)
- [ ] Unitários (service):
  - `test_create_availability_validates_date_order`
  - `test_create_availability_validates_iso_format`
- [ ] Integração (repo):
  - `test_create_and_list_availability`
  - `test_get_unavailable_member_ids_on_date` — caso coberto pela data
  - `test_get_unavailable_member_ids_outside_range` — fora do range não retorna
  - `test_get_unavailable_member_ids_boundary_dates` — testa start_date e end_date exatos

### Qualidade
- [ ] Todos os commands registrados em `generate_handler![]`
- [ ] Testes passando com cobertura ≥ 75%
- [ ] `cargo clippy -- -D warnings` sem warnings

---

## Notas Técnicas

### Query Crítica — `get_unavailable_member_ids`

