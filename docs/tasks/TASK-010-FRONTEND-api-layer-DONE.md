# TASK-010 — Camada de API Tipada (invoke wrappers)

**Domínio:** FRONTEND  
**Status:** DONE  
**Prioridade:** P0  
**Depende de:** TASK-001 (scaffold Tauri + Svelte)  
**Estimativa:** M

---

## Descrição

Implementar a camada de API frontend que encapsula todas as chamadas `invoke()` ao backend Rust, com tipos TypeScript que espelham exatamente as structs Rust, tratamento de erros padronizado e utilitários de resultado. Esta task **bloqueia todas as pages** (TASK-011 a 015).

Toda comunicação frontend → backend deve passar exclusivamente por esta camada — nenhuma página ou store deve chamar `invoke()` diretamente.

---

## Escopo

### 1. Tipos TypeScript — `src/lib/types/index.ts`

Espelhar exatamente as structs Rust (spec §5):

```typescript
// ─── Enums ────────────────────────────────────────────────────────────────────

export type MemberRank = 'leader' | 'trainer' | 'member' | 'recruit';
export type EventType  = 'fixed' | 'seasonal' | 'special';
export type Weekday    = 'sunday' | 'monday' | 'tuesday' | 'wednesday'
                       | 'thursday' | 'friday' | 'saturday';

// ─── Entidades ────────────────────────────────────────────────────────────────

export interface Member {
  id:         string;
  name:       string;
  email:      string | null;
  phone:      string | null;
  instagram:  string | null;
  rank:       MemberRank;
  active:     boolean;
  created_at: string;   // ISO datetime string
  updated_at: string;
}

export interface Squad {
  id:          string;
  name:        string;
  description: string | null;
  created_at:  string;
}

export interface MemberSquad {
  member_id: string;
  squad_id:  string;
  role:      string;
  joined_at: string;
}

export interface Event {
  id:          string;
  name:        string;
  event_type:  EventType;
  weekday:     Weekday | null;
  date:        string | null;  // ISO date (YYYY-MM-DD)
  time:        string | null;  // HH:MM
  description: string | null;
  active:      boolean;
  created_at:  string;
}

export interface EventSquad {
  event_id:    string;
  squad_id:    string;
  min_members: number;
  max_members: number;
}

export interface Couple {
  id:           string;
  member_a_id:  string;
  member_b_id:  string;
  created_at:   string;
}

export interface Availability {
  id:         string;
  member_id:  string;
  start_date: string;  // ISO date
  end_date:   string;  // ISO date
  reason:     string | null;
  created_at: string;
}

export interface Schedule {
  id:           string;
  event_id:     string;
  date:         string;
  generated_at: string;
  notes:        string | null;
}

export interface ScheduleMember {
  schedule_id: string;
  member_id:   string;
  squad_id:    string;
  role:        string;
}

// ─── DTOs (enviados ao backend) ───────────────────────────────────────────────

export interface CreateMemberDto {
  name:      string;
  email?:    string;
  phone?:    string;
  instagram?: string;
  rank?:     MemberRank;
}

export type UpdateMemberDto = Partial<CreateMemberDto> & { active?: boolean };

export interface CreateSquadDto {
  name:        string;
  description?: string;
}

export type UpdateSquadDto = Partial<CreateSquadDto>;

export interface CreateEventDto {
  name:        string;
  event_type:  EventType;
  weekday?:    Weekday;
  date?:       string;
  time?:       string;
  description?: string;
}

export type UpdateEventDto = Partial<CreateEventDto> & { active?: boolean };

export interface SetEventSquadDto {
  event_id:    string;
  squad_id:    string;
  min_members: number;
  max_members: number;
}

export interface CreateCoupleDto {
  member_a_id: string;
  member_b_id: string;
}

export interface CreateAvailabilityDto {
  member_id:  string;
  start_date: string;
  end_date:   string;
  reason?:    string;
}

export interface GenerateScheduleDto {
  event_id: string;
  dates:    string[];  // ISO dates
}

// ─── Tipos de resultado ───────────────────────────────────────────────────────

export interface ScheduleResult {
  schedule:  Schedule;
  members:   ScheduleMember[];
}

/** Visão enriquecida para exibição na tabela de escala */
export interface ScheduleView {
  date:    string;
  squads:  Array<{
    squad:   Squad;
    members: Member[];
  }>;
}
```

---

### 2. Tratamento de Erros — `src/lib/api/errors.ts`

```typescript
/** Espelha o enum AppError do Rust (serializado como JSON pelo Tauri) */
export type AppErrorKind =
  | 'NotFound'
  | 'Validation'
  | 'Database'
  | 'Conflict';

export interface AppError {
  kind:    AppErrorKind;
  message: string;
}

/**
 * Tipo de resultado padronizado para todas as chamadas de API.
 * Evita try/catch espalhados pelas stores e componentes.
 */
export type ApiResult<T> =
  | { ok: true;  data: T }
  | { ok: false; error: AppError };

/**
 * Converte qualquer erro capturado do invoke() em AppError normalizado.
 * O Tauri serializa erros Rust como strings JSON: '{"Validation":"mensagem"}'
 */
export function parseError(raw: unknown): AppError {
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw) as Record<string, string>;
      const kind = Object.keys(parsed)[0] as AppErrorKind;
      return { kind, message: parsed[kind] ?? raw };
    } catch {
      return { kind: 'Database', message: raw };
    }
  }
  if (raw instanceof Error) {
    return { kind: 'Database', message: raw.message };
  }
  return { kind: 'Database', message: String(raw) };
}

/**
 * Wrapper que executa uma Promise e retorna ApiResult<T>
 * sem propagar exceções.
 */
export async function safeInvoke<T>(
  fn: () => Promise<T>,
): Promise<ApiResult<T>> {
  try {
    const data = await fn();
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: parseError(err) };
  }
}
```

---

### 3. API de Membros — `src/lib/api/members.ts`

```typescript
import { invoke } from '@tauri-apps/api/core';
import { safeInvoke } from './errors';
import type { Member, CreateMemberDto, UpdateMemberDto } from '$lib/types';

export const membersApi = {
  /** Lista todos os membros */
  getAll: () =>
    safeInvoke(() => invoke<Member[]>('get_members')),

  /** Busca membro por ID */
  getById: (id: string) =>
    safeInvoke(() => invoke<Member>('get_member', { id })),

  /** Cria novo membro */
  create: (dto: CreateMemberDto) =>
    safeInvoke(() => invoke<Member>('create_member', { dto })),

  /** Atualiza membro existente */
  update: (id: string, dto: UpdateMemberDto) =>
    safeInvoke(() => invoke<Member>('update_member', { id, dto })),

  /** Remove membro (soft delete via active=false ou hard delete) */
  delete: (id: string) =>
    safeInvoke(() => invoke<void>('delete_member', { id })),
} as const;
```

---

### 4. API de Times — `src/lib/api/squads.ts`

```typescript
export const squadsApi = {
  getAll:           () => safeInvoke(() => invoke<Squad[]>('get_squads')),
  getById:          (id: string) => safeInvoke(() => invoke<Squad>('get_squad', { id })),
  create:           (dto: CreateSquadDto) => safeInvoke(() => invoke<Squad>('create_squad', { dto })),
  update:           (id: string, dto: UpdateSquadDto) => safeInvoke(() => invoke<Squad>('update_squad', { id, dto })),
  delete:           (id: string) => safeInvoke(() => invoke<void>('delete_squad', { id })),
  getMembers:       (squadId: string) => safeInvoke(() => invoke<Member[]>('get_squad_members', { squadId })),
  addMember:        (squadId: string, memberId: string) => safeInvoke(() => invoke<void>('add_member_to_squad', { squadId, memberId })),
  removeMember:     (squadId: string, memberId: string) => safeInvoke(() => invoke<void>('remove_member_from_squad', { squadId, memberId })),
} as const;
```

---

### 5. API de Eventos — `src/lib/api/events.ts`

```typescript
export const eventsApi = {
  getAll:        () => safeInvoke(() => invoke<Event[]>('get_events')),
  getById:       (id: string) => safeInvoke(() => invoke<Event>('get_event', { id })),
  create:        (dto: CreateEventDto) => safeInvoke(() => invoke<Event>('create_event', { dto })),
  update:        (id: string, dto: UpdateEventDto) => safeInvoke(() => invoke<Event>('update_event', { id, dto })),
  delete:        (id: string) => safeInvoke(() => invoke<void>('delete_event', { id })),
  getSquads:     (eventId: string) => safeInvoke(() => invoke<EventSquad[]>('get_event_squads', { eventId })),
  setSquad:      (dto: SetEventSquadDto) => safeInvoke(() => invoke<EventSquad>('set_event_squad', { dto })),
  removeSquad:   (eventId: string, squadId: string) => safeInvoke(() => invoke<void>('remove_event_squad', { eventId, squadId })),
} as const;
```

---

### 6. API de Escala — `src/lib/api/schedule.ts`

```typescript
export const scheduleApi = {
  generate: (dto: GenerateScheduleDto) =>
    safeInvoke(() => invoke<ScheduleResult[]>('generate_schedule', { dto })),

  getByEvent: (eventId: string) =>
    safeInvoke(() => invoke<ScheduleView[]>('get_schedules_by_event', { eventId })),

  exportCsv: (scheduleId: string) =>
    safeInvoke(() => invoke<string>('export_schedule_csv', { scheduleId })),

  exportPdf: (scheduleId: string) =>
    safeInvoke(() => invoke<void>('export_schedule_pdf', { scheduleId })),
} as const;
```

---

### 7. API de Casais — `src/lib/api/couples.ts`

```typescript
export const couplesApi = {
  getAll:  () => safeInvoke(() => invoke<Couple[]>('get_couples')),
  create:  (dto: CreateCoupleDto) => safeInvoke(() => invoke<Couple>('create_couple', { dto })),
  delete:  (id: string) => safeInvoke(() => invoke<void>('delete_couple', { id })),
} as const;
```

---

### 8. API de Disponibilidade — `src/lib/api/availability.ts`

```typescript
export const availabilityApi = {
  getAll:       () => safeInvoke(() => invoke<Availability[]>('get_availability')),
  getByMember:  (memberId: string) =>
    safeInvoke(() => invoke<Availability[]>('get_member_availability', { memberId })),
  create:       (dto: CreateAvailabilityDto) =>
    safeInvoke(() => invoke<Availability>('create_availability', { dto })),
  delete:       (id: string) =>
    safeInvoke(() => invoke<void>('delete_availability', { id })),
} as const;
```

---

### 9. Barrel Export — `src/lib/api/index.ts`

```typescript
export { membersApi }      from './members';
export { squadsApi }       from './squads';
export { eventsApi }       from './events';
export { scheduleApi }     from './schedule';
export { couplesApi }      from './couples';
export { availabilityApi } from './availability';
export type { ApiResult, AppError, AppErrorKind } from './errors';
export { safeInvoke, parseError }                 from './errors';
```

---

## Critérios de Aceite

- [ ] Todos os tipos TypeScript de `src/lib/types/index.ts` espelham exatamente as structs Rust da spec §5 (campos, tipos, opcionais)
- [ ] `ApiResult<T>` distingue sucesso/erro em tempo de compilação (discriminated union)
- [ ] `parseError()` converte corretamente strings JSON do Tauri em `AppError` com `kind` + `message`
- [ ] `safeInvoke()` nunca propaga exceção — sempre retorna `ApiResult<T>`
- [ ] Todos os 6 módulos de API (`members`, `squads`, `events`, `schedule`, `couples`, `availability`) implementados
- [ ] Cada método de API cobre exatamente os commands Rust registrados na spec §6
- [ ] Barrel `api/index.ts` exporta tudo
- [ ] Testes unitários para `parseError()` e `safeInvoke()` com casos: sucesso, `NotFound`, `Validation`, `Conflict`, `Database`, erro genérico
- [ ] Testes de cada módulo de API mockando `invoke()` (happy path + error path)
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Zero chamadas `invoke()` fora de `src/lib/api/`

---

## Notas Técnicas

- **Mocking Tauri**: criar `src/__mocks__/@tauri-apps/api/core.ts` com `vi.fn()` para `invoke`; configurar em `vitest.config.ts`
- **Nomes de commands**: usar exatamente os nomes registrados no `tauri::generate_handler![]` do Rust — qualquer divergência causa erro em runtime; validar com o time de backend
- **`safeInvoke` vs try/catch**: stores e componentes devem sempre usar `safeInvoke` e verificar `result.ok` antes de acessar `result.data`
- **Sem transformações**: a API layer não transforma dados — recebe e entrega exatamente o que o backend retorna; transformações para exibição ficam nos componentes/utils
- **DTOs opcionais**: campos marcados como `?` nos DTOs TypeScript devem ser omitidos (não enviados como `undefined`) — usar `Object.fromEntries(Object.entries(dto).filter(([,v]) => v !== undefined))` se necessário
- **`ScheduleView`**: tipo construído pelo frontend para facilitar renderização — não existe no backend; montar a partir dos arrays `Schedule` + `ScheduleMember` + `Squad` + `Member`
- **`exportCsv`**: retorna o conteúdo do CSV como string; a escrita no disco é feita pelo componente via `tauri-plugin-dialog` + `tauri-plugin-fs`

---

## Arquivos a Criar

```
src/lib/
├── types/
│   └── index.ts                  ← todos os tipos/interfaces/enums
└── api/
    ├── index.ts                  ← barrel export
    ├── errors.ts                 ← AppError, ApiResult, safeInvoke, parseError
    ├── errors.test.ts
    ├── members.ts
    ├── members.test.ts
    ├── squads.ts
    ├── squads.test.ts
    ├── events.ts
    ├── events.test.ts
    ├── schedule.ts
    ├── schedule.test.ts
    ├── couples.ts
    ├── couples.test.ts
    ├── availability.ts
    └── availability.test.ts

src/__mocks__/
└── @tauri-apps/
    └── api/
        └── core.ts               ← mock do invoke para testes
```

---

## Progresso

- [ ] `types/index.ts` — todos os tipos e DTOs
- [ ] `api/errors.ts` — `AppError`, `ApiResult`, `safeInvoke`, `parseError`
- [ ] `api/errors.test.ts` — testes unitários completos
- [ ] `api/members.ts` + testes
- [ ] `api/squads.ts` + testes
- [ ] `api/events.ts` + testes
- [ ] `api/schedule.ts` + testes
- [ ] `api/couples.ts` + testes
- [ ] `api/availability.ts` + testes
- [ ] `api/index.ts` — barrel completo
- [ ] Mock `@tauri-apps/api/core` configurado no Vitest
- [ ] `tsc --noEmit` sem erros
- [ ] `vitest --coverage` ≥ 75%
