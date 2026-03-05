# TASK-006 — Motor de Geração de Escala

**Domínio:** BACKEND  
**Status:** WAITING  
**Prioridade:** P0 — feature principal do produto  
**Depende de:** TASK-002, TASK-003, TASK-004, TASK-005  
**Estimativa:** XL (> 12h)

---

## Descrição

Implementar o **algoritmo de geração automática de escala** — o núcleo do
produto. O motor recebe um evento e uma lista de datas, e distribui membros
por squads respeitando cinco restrições simultâneas:

1. **Disponibilidade** — membros com `availability` registrada na data são excluídos
2. **Restrição de casais** — se um membro de um casal for selecionado, seu par
   **deve** ser escalado no mesmo evento/data (regra de negócio: casais sempre
   servem juntos ou nenhum serve)
3. **Rotatividade** — membros que serviram mais recentemente têm menor
   prioridade (equidade de distribuição)
4. **Mínimo/máximo por squad** — conforme `events_squads.min_members` /
   `max_members`
5. **Membros ativos** — apenas membros com `active = 1` são elegíveis

O resultado é persistido nas tabelas `schedules` + `schedule_members`.

---

## Critérios de Aceite

### Models (`models/schedule.rs`)
- [ ] `Schedule` struct: `{ id, event_id, date, generated_at, notes }` + derives
- [ ] `ScheduleMember` struct: `{ schedule_id, member_id, squad_id, role }`
- [ ] `ScheduleWithDetails` struct: evento + data + lista de
  `{ squad: Squad, members: Vec<Member> }`
- [ ] `GenerateScheduleDto { event_id: String, dates: Vec<String> }`

### Repo (`db/schedule_repo.rs`)
- [ ] `create_schedule(pool, event_id, date) -> Result<Schedule>`
- [ ] `add_schedule_member(pool, schedule_id, member_id, squad_id, role) -> Result<()>`
- [ ] `get_schedules_for_event(pool, event_id) -> Result<Vec<Schedule>>`
- [ ] `get_schedule_details(pool, schedule_id) -> Result<ScheduleWithDetails>`
- [ ] `get_member_service_count(pool, member_id, since_date) -> Result<i64>` — conta serviços recentes para rotatividade
- [ ] `get_last_service_date(pool, member_id) -> Result<Option<String>>`
- [ ] `delete_schedule(pool, schedule_id) -> Result<()>`

### Service (`services/schedule_service.rs`) — Algoritmo

