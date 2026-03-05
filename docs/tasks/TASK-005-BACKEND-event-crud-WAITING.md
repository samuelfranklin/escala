# TASK-005 — CRUD Completo de Event + Configuração de Squads por Evento

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-002  
**Estimativa:** M (2–6h)

---

## Descrição

Implementar a pilha completa do domínio **Event** (eventos/cultos), incluindo
o CRUD da entidade e o gerenciamento da tabela `events_squads` — que define
**quais squads** participam de cada evento e **quantos membros** são necessários
(min/max). Esta configuração é consumida diretamente pelo algoritmo de geração
de escala (TASK-006).

---

## Critérios de Aceite

### Models (`models/event.rs`)
- [ ] `Event` struct com todos os campos da spec §5 + derives completos
- [ ] `EventType` enum: `Fixed | Seasonal | Special` com
  `#[sqlx(type_name = "TEXT", rename_all = "lowercase")]`
- [ ] `EventSquadConfig` struct:
  `{ event_id, squad_id, min_members: i32, max_members: i32 }`
- [ ] `EventWithConfig` struct: `{ event: Event, squad_configs: Vec<EventSquadConfig> }`
- [ ] `CreateEventDto { name, event_type, weekday, date, time, description }`
- [ ] `UpdateEventDto` (todos `Option<T>`)
- [ ] `SetEventSquadConfigDto { squad_id, min_members, max_members }`

### Repo (`db/event_repo.rs`)
- [ ] `list_all(pool) -> Result<Vec<Event>>`
- [ ] `list_active(pool) -> Result<Vec<Event>>` — WHERE `active = 1`
- [ ] `get_by_id(pool, id) -> Result<Event>`
- [ ] `create(pool, dto) -> Result<Event>`
- [ ] `update(pool, id, dto) -> Result<Event>`
- [ ] `delete(pool, id) -> Result<()>`
- [ ] `get_squad_configs(pool, event_id) -> Result<Vec<EventSquadConfig>>`
- [ ] `set_squad_config(pool, event_id, dto) -> Result<EventSquadConfig>` — upsert
- [ ] `remove_squad_config(pool, event_id, squad_id) -> Result<()>`

### Service (`services/event_service.rs`)
- [ ] `list_events(pool) -> Result<Vec<Event>>`
- [ ] `get_event(pool, id) -> Result<Event>`
- [ ] `create_event(pool, dto) -> Result<Event>`:
  - Valida `name` não vazio
  - Se `event_type = Fixed`: valida que `weekday` é informado e válido
    (`sunday` | `monday` | ... | `saturday`)
  - Se `event_type = Seasonal | Special`: valida que `date` é informada (ISO format)
- [ ] `update_event(pool, id, dto) -> Result<Event>`
- [ ] `delete_event(pool, id) -> Result<()>`
- [ ] `get_event_with_config(pool, id) -> Result<EventWithConfig>`
- [ ] `set_squad_config(pool, event_id, dto) -> Result<EventSquadConfig>`:
  - Valida `min_members >= 1` e `max_members >= min_members`
  - Verifica existência do squad → `AppError::NotFound`
- [ ] `remove_squad_config(pool, event_id, squad_id) -> Result<()>`

### Commands (`commands/event.rs`)
- [ ] `get_events(state) -> Result<Vec<Event>, AppError>`
- [ ] `get_event(state, id: String) -> Result<Event, AppError>`
- [ ] `create_event(state, dto: CreateEventDto) -> Result<Event, AppError>`
- [ ] `update_event(state, id: String, dto: UpdateEventDto) -> Result<Event, AppError>`
- [ ] `delete_event(state, id: String) -> Result<(), AppError>`
- [ ] `get_event_with_config(state, id: String) -> Result<EventWithConfig, AppError>`
- [ ] `set_event_squad_config(state, event_id: String, dto: SetEventSquadConfigDto) -> Result<EventSquadConfig, AppError>`
- [ ] `remove_event_squad_config(state, event_id: String, squad_id: String) -> Result<(), AppError>`
- [ ] Todos registrados em `generate_handler![]`

### Testes
- [ ] Unitários (service):
  - `test_create_fixed_event_requires_weekday`
  - `test_create_seasonal_event_requires_date`
  - `test_set_config_validates_min_max`
- [ ] Integração (repo, SQLite `:memory:`):
  - `test_create_and_list_events`
  - `test_set_and_get_squad_config`
  - `test_upsert_squad_config`
  - `test_delete_event_cascades_config`
- [ ] Testes passando com cobertura ≥ 75%
- [ ] `cargo clippy -- -D warnings` sem warnings

---

## Notas Técnicas

### Upsert de events_squads

