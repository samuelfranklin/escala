# TASK-019 — Configuração de Squads por Evento (event_squads)

**Domínio:** FULLSTACK (Backend Rust + Frontend Svelte)  
**Status:** DONE  
**Prioridade:** P0 (bloqueante — sem isso a geração de escala nunca funciona)  
**Depende de:** TASK-013 (events page), TASK-012 (squads page)  
**Estimativa:** M (2–6h)

---

## Descrição

A tabela `event_squads` existe no banco e é consultada pelo algoritmo de geração de escala, mas **nunca é populada** porque não há command Tauri nem UI para gerenciá-la. Isso faz com que `generate_schedule` retorne sempre o erro `"Event has no squads configured"`.

É necessário implementar a cadeia completa: repo → service → command Tauri → API wrapper → UI na tela de Eventos.

---

## Contexto Técnico

```
schema                    backend                    frontend
─────────────────────     ───────────────────────    ─────────────────────
event_squads              event_repo (faltando)      src/lib/api/events.ts
  event_id  TEXT          event_service (faltando)   src/routes/events/+page.svelte
  squad_id  TEXT          commands/event.rs
  min_members INT                                    (tudo faltando)
  max_members INT
```

---

## Critérios de Aceite

### Backend

- [ ] `event_repo.rs` — adicionar:
  - `get_event_squads(pool, event_id) -> Result<Vec<EventSquad>, AppError>`
  - `set_event_squads(pool, event_id, items: Vec<EventSquadDto>) -> Result<(), AppError>`
    - Implementar como DELETE + INSERT em transação (upsert simples)

- [ ] `models/event.rs` — adicionar structs:
  ```rust
  #[derive(Debug, Clone, Serialize, Deserialize)]
  pub struct EventSquad {
      pub squad_id: String,
      pub squad_name: String,   // JOIN com squads para retornar o nome
      pub min_members: i64,
      pub max_members: i64,
  }

  #[derive(Debug, Deserialize)]
  pub struct EventSquadDto {
      pub squad_id: String,
      pub min_members: i64,
      pub max_members: i64,
  }
  ```

- [ ] `event_service.rs` — adicionar:
  ```rust
  pub async fn get_event_squads(pool, event_id) -> Result<Vec<EventSquad>, AppError>
  pub async fn set_event_squads(pool, event_id, items: Vec<EventSquadDto>) -> Result<Vec<EventSquad>, AppError>
  ```

- [ ] `commands/event.rs` — adicionar dois commands:
  ```rust
  #[tauri::command]
  pub async fn get_event_squads(state, event_id: String) -> Result<Vec<EventSquad>, AppError>

  #[tauri::command]
  pub async fn set_event_squads(state, event_id: String, squads: Vec<EventSquadDto>) -> Result<Vec<EventSquad>, AppError>
  ```

- [ ] Registrar os novos commands no `tauri::generate_handler![]` em `lib.rs`

- [ ] Testes unitários em `event_service.rs` (SQLite `:memory:`):
  - `test_set_and_get_event_squads_roundtrip`
  - `test_set_event_squads_replaces_previous`
  - `test_set_event_squads_empty_clears_all`

### Frontend

- [ ] `src/lib/types/index.ts` — adicionar tipos:
  ```typescript
  export interface EventSquad {
    squad_id: string;
    squad_name: string;
    min_members: number;
    max_members: number;
  }
  export interface EventSquadDto {
    squad_id: string;
    min_members: number;
    max_members: number;
  }
  ```

- [ ] `src/lib/api/events.ts` — adicionar:
  ```typescript
  export const getEventSquads = (eventId: string) =>
    invoke<EventSquad[]>('get_event_squads', { eventId });

  export const setEventSquads = (eventId: string, squads: EventSquadDto[]) =>
    invoke<EventSquad[]>('set_event_squads', { eventId, squads });
  ```

- [ ] `src/routes/events/+page.svelte` — adicionar fluxo de configuração:
  1. Ao clicar em um evento na lista, abrir painel lateral (ou modal) "Configurar Times"
  2. Listar todos os squads cadastrados com checkbox
  3. Para cada squad marcado, permitir definir `min_members` (default 1) e `max_members` (default 3)
  4. Botão "Salvar Configuração" chama `setEventSquads`
  5. Badge no card do evento mostrando quantos squads estão configurados (ex: "3 times")
  6. Indicador visual: evento sem squads → badge vermelho "Sem times", evento com squads → badge verde "N times"

### UI — Wireframe

```
┌─ Eventos ─────────────────────────────────────── [+ Novo Evento] ─┐
│ ┌──────────────────────────────┐  ┌──────────────────────────────┐ │
│ │ ► Culto Domingo  2026-03-08  │  │  Configurar Times             │ │
│ │   [● 3 times]               │  │  Culto Domingo                │ │
│ │   Culto Quarta   2026-03-11  │  │  ──────────────────────────  │ │
│ │   [✗ Sem times]             │  │  ☑ Câmera      min[1] max[3] │ │
│ └─────────────────────────────┘  │  ☑ Transmissão min[1] max[2] │ │
│                                   │  ☐ Áudio                     │ │
│                                   │  ☐ Iluminação                │ │
│                                   │  ──────────────────────────  │ │
│                                   │  [Salvar Configuração]        │ │
│                                   └──────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

- [ ] Testes Vitest (CFI): `set_event_squads` é chamado com payload correto ao salvar

---

## Notas Técnicas

- O `set_event_squads` deve rodar em transação: `DELETE FROM event_squads WHERE event_id = ?` seguido de múltiplos `INSERT`. Isso evita lógica de diff e garante consistência.
- Validar no service: `min_members >= 1`, `max_members >= min_members`, `max_members <= 10`.
- O campo `squad_name` em `EventSquad` exige JOIN com a tabela `squads` na query de leitura — não armazenar o nome, só buscar na leitura.
- No frontend, carregar a lista de `EventSquad` ao selecionar o evento para pré-popular os checkboxes.
