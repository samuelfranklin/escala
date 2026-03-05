# Escala Mídia — Especificação Técnica

> **Versão:** 1.0.0  
> **Status:** Draft  
> **Branch:** `feat/tauri-migration`  
> **Referências:** [PDR-TAURI-001](../pdrs/PDR-TAURI-001.md) · [PDR-RUST-001](../pdrs/PDR-RUST-001.md)

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Arquitetura](#3-arquitetura)
4. [Estrutura de Arquivos](#4-estrutura-de-arquivos)
5. [Domínio e Modelos de Dados](#5-domínio-e-modelos-de-dados)
6. [Backend — Rust / Tauri Commands](#6-backend--rust--tauri-commands)
7. [Frontend — Svelte / TypeScript](#7-frontend--svelte--typescript)
8. [UI/UX](#8-uiux)
9. [Segurança](#9-segurança)
10. [Deploy e Distribuição](#10-deploy-e-distribuição)
11. [Processo de Desenvolvimento (TDD)](#11-processo-de-desenvolvimento-tdd)
12. [Estratégia de Testes](#12-estratégia-de-testes)
13. [CI/CD](#13-cicd)
14. [Decisões de Design (ADRs)](#14-decisões-de-design-adrs)

---

## 1. Visão Geral

**Produto:** App desktop multiplataforma para gestão de escala por time de uma instituição

**Problema resolvido:** Coordenadores gerenciam manualmente em planilhas quem serve em cada evento — processo propenso a conflitos, faltas e retrabalho.

**Solução:** App offline-first que centraliza cadastro de membros, times, eventos e gera escalas automaticamente respeitando disponibilidade e restrições (casais, folgas, rotatividade).

### Personas

| Persona | Ações Principais |
|---|---|
| **Coordenador de Mídia** | Cadastrar membros/times/eventos; configurar evento; gerar escala; exportar |
| **Líder de Time** | Visualizar escala do time; registrar indisponibilidade |

### Plataformas-alvo

- Windows 10/11 (x64)
- Linux (Ubuntu 22.04+, Debian 11+) — x64 e ARM64
- macOS 12+ (Intel e Apple Silicon)

---

## 2. Stack Tecnológico

### Frontend

| Tecnologia | Versão | Finalidade |
|---|---|---|
| [Svelte](https://svelte.dev) | 5.x | Framework UI reativo |
| TypeScript | 5.x | Tipagem estática |
| Vite | 6.x | Build tool / dev server |
| [lucide-svelte](https://lucide.dev) | latest | Biblioteca de ícones |
| [svelte-query](https://tanstack.com/query) (TanStack) | 5.x | Cache e estado assíncrono |
| Vitest | 2.x | Testes unitários frontend |
| Playwright | 1.x | Testes E2E |

### Backend

| Tecnologia | Versão | Finalidade |
|---|---|---|
| Rust | 1.78+ (stable) | Linguagem principal do backend |
| [Tauri](https://tauri.app) | 2.x | Framework desktop (IPC + bundling) |
| [SQLx](https://github.com/launchbadge/sqlx) | 0.8.x | ORM async / SQLite |
| SQLite | 3.x | Banco de dados local |
| [Tokio](https://tokio.rs) | 1.x | Runtime async (via Tauri) |
| [Serde](https://serde.rs) | 1.x | Serialização JSON ↔ Rust |
| [thiserror](https://docs.rs/thiserror) | 1.x | Error types ergonômicos |
| [chrono](https://docs.rs/chrono) | 0.4.x | Datas e horários |
| [uuid](https://docs.rs/uuid) | 1.x | Geração de IDs |

### Plugins Tauri

| Plugin | Finalidade |
|---|---|
| `tauri-plugin-sql` | SQLite direto do frontend (queries simples) |
| `tauri-plugin-store` | Persistência de preferências (tema, janela) |
| `tauri-plugin-notification` | Notificações do sistema |
| `tauri-plugin-updater` | Auto-update OTA |
| `tauri-plugin-dialog` | Diálogos nativos (save/open file) |
| `tauri-plugin-fs` | Acesso ao filesystem (exportar escala) |

---

## 3. Arquitetura

### Visão Macro

```
┌─────────────────────────────────────────────────────────────┐
│                        PROCESSO TAURI                        │
│                                                             │
│  ┌───────────────────────────────┐  ┌────────────────────┐ │
│  │      FRONTEND (WebView)       │  │   BACKEND (Rust)   │ │
│  │                               │  │                    │ │
│  │  Svelte + TypeScript          │◄─►│  Tauri Commands    │ │
│  │  ├─ Pages (rotas)             │  │  ├─ member_cmd     │ │
│  │  ├─ Components                │  │  ├─ squad_cmd      │ │
│  │  ├─ Stores (estado)           │  │  ├─ event_cmd      │ │
│  │  └─ API layer (invoke)        │  │  ├─ schedule_cmd   │ │
│  │                               │  │  └─ export_cmd     │ │
│  └───────────────────────────────┘  │                    │ │
│               IPC (invoke/event)    │  ┌──────────────┐  │ │
│                                     │  │  SQLx/SQLite │  │ │
│                                     │  │  (local DB)  │  │ │
│                                     │  └──────────────┘  │ │
│                                     └────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Camadas

```
frontend/
  ├── presentation  (Svelte components, pages)
  ├── application   (stores, use-cases, query hooks)
  └── api           (invoke wrappers tipados)

src-tauri/
  ├── commands      (handlers expostos ao frontend)
  ├── services      (lógica de negócio pura)
  ├── models        (structs de domínio + Serde)
  ├── db            (queries SQLx, migrations)
  └── errors        (thiserror types)
```

### Comunicação IPC

Todo dado flui via `invoke()` (frontend → backend) ou `emit()`/`listen()` (eventos assíncronos):

```typescript
// Frontend: invoke tipado
import { invoke } from '@tauri-apps/api/core';
const members = await invoke<Member[]>('get_members');

// Backend: command handler
#[tauri::command]
async fn get_members(state: State<'_, AppState>) -> Result<Vec<Member>, AppError> {
    state.db.get_members().await.map_err(AppError::from)
}
```

---

## 4. Estrutura de Arquivos

```
escala-midia/
├── src/                        # Frontend Svelte
│   ├── lib/
│   │   ├── api/                # Wrappers invoke() tipados
│   │   │   ├── members.ts
│   │   │   ├── squads.ts
│   │   │   ├── events.ts
│   │   │   ├── schedule.ts
│   │   │   └── index.ts
│   │   ├── components/         # Componentes reutilizáveis
│   │   │   ├── ui/             # Primitivos (Button, Input, Modal, Badge)
│   │   │   ├── layout/         # Shell, Sidebar, Header
│   │   │   └── domain/         # MemberCard, ScheduleTable, EventBadge
│   │   ├── stores/             # Estado global Svelte
│   │   │   ├── members.ts
│   │   │   ├── squads.ts
│   │   │   └── ui.ts           # tema, sidebar state
│   │   ├── types/              # TypeScript types (espelham Rust structs)
│   │   │   └── index.ts
│   │   └── utils/              # Helpers puros (datas, formatação)
│   ├── routes/                 # Páginas (SvelteKit-style routing)
│   │   ├── +layout.svelte
│   │   ├── dashboard/+page.svelte
│   │   ├── members/+page.svelte
│   │   ├── squads/+page.svelte
│   │   ├── events/+page.svelte
│   │   ├── schedule/+page.svelte
│   │   ├── couples/+page.svelte
│   │   └── availability/+page.svelte
│   ├── app.css                 # Design tokens CSS (custom properties)
│   └── app.html
│
├── src-tauri/                  # Backend Rust
│   ├── src/
│   │   ├── main.rs             # Entry point (Desktop)
│   │   ├── lib.rs              # Entry point (Mobile / tests)
│   │   ├── commands/           # Tauri commands (interface pública)
│   │   │   ├── mod.rs
│   │   │   ├── member.rs
│   │   │   ├── squad.rs
│   │   │   ├── event.rs
│   │   │   ├── schedule.rs
│   │   │   ├── couple.rs
│   │   │   └── availability.rs
│   │   ├── services/           # Lógica de negócio (pura, sem Tauri)
│   │   │   ├── mod.rs
│   │   │   ├── member_service.rs
│   │   │   ├── squad_service.rs
│   │   │   ├── event_service.rs
│   │   │   ├── schedule_service.rs  # Algoritmo de geração
│   │   │   └── export_service.rs
│   │   ├── db/                 # Camada de dados
│   │   │   ├── mod.rs
│   │   │   ├── pool.rs         # ConnectionPool setup
│   │   │   ├── member_repo.rs
│   │   │   ├── squad_repo.rs
│   │   │   ├── event_repo.rs
│   │   │   └── schedule_repo.rs
│   │   ├── models/             # Structs de domínio
│   │   │   ├── mod.rs
│   │   │   ├── member.rs
│   │   │   ├── squad.rs
│   │   │   ├── event.rs
│   │   │   ├── schedule.rs
│   │   │   └── availability.rs
│   │   ├── errors.rs           # AppError (thiserror)
│   │   └── state.rs            # AppState (pool compartilhado)
│   ├── migrations/             # SQLx migrations (versionadas)
│   │   ├── 20240101_001_initial.sql
│   │   ├── 20240101_002_schedules.sql
│   │   └── ...
│   ├── Cargo.toml
│   ├── tauri.conf.json         # Configuração Tauri (capabilities, bundle)
│   └── capabilities/          # Arquivo de capabilities por contexto
│       └── default.json
│
├── tests/                      # Testes E2E (Playwright)
│   ├── e2e/
│   │   ├── fixtures/
│   │   ├── members.spec.ts
│   │   ├── squads.spec.ts
│   │   ├── events.spec.ts
│   │   └── schedule.spec.ts
│   └── playwright.config.ts
│
├── docs/
│   ├── pdrs/
│   │   ├── PDR-TAURI-001.md
│   │   └── PDR-RUST-001.md
│   └── specs/
│       └── app.spec.md         # este arquivo
│
├── .github/
│   └── workflows/
│       ├── test.yml            # CI: unit + integration
│       ├── e2e.yml             # CI: E2E com Playwright
│       └── release.yml         # CD: build + sign + publish
│
├── package.json
├── vite.config.ts
├── svelte.config.js
├── tsconfig.json
├── vitest.config.ts
└── playwright.config.ts
```

---

## 5. Domínio e Modelos de Dados

### Schema SQLite

```sql
-- Membros
CREATE TABLE members (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  name        TEXT NOT NULL,
  email       TEXT UNIQUE,
  phone       TEXT,
  instagram   TEXT,
  rank        TEXT NOT NULL DEFAULT 'member'  -- 'leader'|'trainer'|'member'|'recruit'
              CHECK(rank IN ('leader','trainer','member','recruit')),
  active      INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Times / Squads
CREATE TABLE squads (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  name        TEXT NOT NULL UNIQUE,
  description TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Associação Membro ↔ Time
CREATE TABLE members_squads (
  member_id   TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  squad_id    TEXT NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
  role        TEXT NOT NULL DEFAULT 'member',
  joined_at   TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (member_id, squad_id)
);

-- Eventos
CREATE TABLE events (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  name        TEXT NOT NULL,
  event_type  TEXT NOT NULL CHECK(event_type IN ('fixed','seasonal','special')),
  weekday     TEXT,           -- para type='fixed': 'sunday','wednesday', etc.
  date        TEXT,           -- para type='seasonal'|'special': ISO date
  time        TEXT,           -- HH:MM
  description TEXT,
  active      INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Configuração Evento ↔ Time (quantas pessoas por time por evento)
CREATE TABLE events_squads (
  event_id    TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  squad_id    TEXT NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
  min_members INTEGER NOT NULL DEFAULT 1,
  max_members INTEGER NOT NULL DEFAULT 3,
  PRIMARY KEY (event_id, squad_id)
);

-- Casais (restrição de não escalá-los juntos)
CREATE TABLE couples (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  member_a_id TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  member_b_id TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(member_a_id, member_b_id)
);

-- Disponibilidade (períodos de indisponibilidade)
CREATE TABLE availability (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  member_id   TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  start_date  TEXT NOT NULL,
  end_date    TEXT NOT NULL,
  reason      TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Escalas geradas
CREATE TABLE schedules (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  event_id    TEXT NOT NULL REFERENCES events(id),
  date        TEXT NOT NULL,
  generated_at TEXT NOT NULL DEFAULT (datetime('now')),
  notes       TEXT
);

-- Itens da escala (quem serve em quê)
CREATE TABLE schedule_members (
  schedule_id TEXT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
  member_id   TEXT NOT NULL REFERENCES members(id),
  squad_id    TEXT NOT NULL REFERENCES squads(id),
  role        TEXT NOT NULL DEFAULT 'operator',
  PRIMARY KEY (schedule_id, member_id, squad_id)
);
```

### Structs Rust (espelhadas em TypeScript)

```rust
// src-tauri/src/models/member.rs
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Member {
    pub id: String,
    pub name: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub instagram: Option<String>,
    pub rank: MemberRank,
    pub active: bool,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT", rename_all = "lowercase")]
pub enum MemberRank { Leader, Trainer, Member, Recruit }

#[derive(Debug, Deserialize)]
pub struct CreateMemberDto {
    pub name: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub instagram: Option<String>,
    pub rank: Option<MemberRank>,
}
```

---

## 6. Backend — Rust / Tauri Commands

### AppState

```rust
// src-tauri/src/state.rs
pub struct AppState {
    pub db: SqlitePool,
}
```

Registrado em `lib.rs`:
```rust
tauri::Builder::default()
    .manage(AppState { db: pool })
    .invoke_handler(tauri::generate_handler![
        member::get_members,
        member::create_member,
        member::update_member,
        member::delete_member,
        // ...
    ])
```

### Padrão de Command

```rust
// src-tauri/src/commands/member.rs
#[tauri::command]
pub async fn get_members(state: State<'_, AppState>) -> Result<Vec<Member>, AppError> {
    member_service::list_members(&state.db).await
}

#[tauri::command]
pub async fn create_member(
    state: State<'_, AppState>,
    dto: CreateMemberDto,
) -> Result<Member, AppError> {
    member_service::create_member(&state.db, dto).await
}
```

### Tratamento de Erros

```rust
// src-tauri/src/errors.rs
#[derive(Debug, thiserror::Error, Serialize)]
pub enum AppError {
    #[error("Not found: {0}")]
    NotFound(String),
    #[error("Validation error: {0}")]
    Validation(String),
    #[error("Database error: {0}")]
    Database(String),
    #[error("Conflict: {0}")]
    Conflict(String),
}

impl From<sqlx::Error> for AppError {
    fn from(e: sqlx::Error) -> Self {
        match e {
            sqlx::Error::RowNotFound => AppError::NotFound("Record not found".into()),
            _ => AppError::Database(e.to_string()),
        }
    }
}
```

### Algoritmo de Geração de Escala

```
ScheduleService::generate(event_id, dates[]) -> Vec<Schedule>

Para cada data:
1. Buscar configuração event_squads (quais times e quantas pessoas)
2. Para cada squad configurado:
   a. Filtrar membros ativos desse squad
   b. Remover membros indisponíveis na data
   c. Remover membros que serviram recentemente (rotatividade)
   d. Remover conflito de casais (sempre escalar par junto)
   e. Ordenar por menor frequência de serviço (equidade)
   f. Selecionar N membros (entre min_members e max_members)
3. Persistir e retornar
```

---

## 7. Frontend — Svelte / TypeScript

### API Layer (invoke wrappers)

```typescript
// src/lib/api/members.ts
import { invoke } from '@tauri-apps/api/core';
import type { Member, CreateMemberDto } from '$lib/types';

export const membersApi = {
  getAll: () => invoke<Member[]>('get_members'),
  getById: (id: string) => invoke<Member>('get_member', { id }),
  create: (dto: CreateMemberDto) => invoke<Member>('create_member', { dto }),
  update: (id: string, dto: Partial<CreateMemberDto>) =>
    invoke<Member>('update_member', { id, dto }),
  delete: (id: string) => invoke<void>('delete_member', { id }),
};
```

### Stores Svelte

```typescript
// src/lib/stores/members.ts
import { writable, derived } from 'svelte/store';
import { membersApi } from '$lib/api/members';

function createMembersStore() {
  const { subscribe, set, update } = writable<Member[]>([]);
  return {
    subscribe,
    load: async () => set(await membersApi.getAll()),
    create: async (dto: CreateMemberDto) => {
      const member = await membersApi.create(dto);
      update(ms => [...ms, member]);
      return member;
    },
    // ...
  };
}
export const membersStore = createMembersStore();
```

### Roteamento

Sem SvelteKit (app Tauri não tem servidor). Usar `svelte-spa-router` ou roteamento manual com stores:

```typescript
// src/lib/stores/router.ts
import { writable } from 'svelte/store';

export type Route = 'dashboard' | 'members' | 'squads' | 'events' | 
                   'schedule' | 'couples' | 'availability';
export const currentRoute = writable<Route>('dashboard');
```

---

## 8. UI/UX

### Design System

#### Paleta de Cores

```css
/* src/app.css */
:root {
  /* Primária — azul */
  --color-primary-50:  #eef2ff;
  --color-primary-100: #e0e7ff;
  --color-primary-400: #818cf8;
  --color-primary-500: #4f7ef8;   /* brand principal */
  --color-primary-600: #3b6ef0;
  --color-primary-900: #1e2a5e;

  /* Superfícies (light) */
  --surface-bg:        #0f1117;
  --surface-sidebar:   #1a1f2e;
  --surface-card:      #1e2438;
  --surface-elevated:  #252b40;
  --surface-border:    #2d3552;

  /* Textos */
  --text-primary:   #e8eaf6;
  --text-secondary: #8892b0;
  --text-muted:     #4a5568;

  /* Feedback */
  --color-success: #4ade80;
  --color-warning: #fbbf24;
  --color-error:   #f87171;
  --color-info:    #60a5fa;

  /* Patentes/Ranks */
  --rank-leader:   #fbbf24;
  --rank-trainer:  #818cf8;
  --rank-member:   #4ade80;
  --rank-recruit:  #9ca3af;
}

[data-theme="light"] {
  --surface-bg:       #f8fafc;
  --surface-sidebar:  #1a1f2e;  /* sidebar sempre escura */
  --surface-card:     #ffffff;
  --surface-elevated: #f1f5f9;
  --surface-border:   #e2e8f0;
  --text-primary:     #0f172a;
  --text-secondary:   #475569;
  --text-muted:       #94a3b8;
}
```

#### Tipografia

| Token | Fonte | Tamanho | Peso | Uso |
|---|---|---|---|---|
| `--text-xs` | Inter | 11px | 400 | Labels, captions |
| `--text-sm` | Inter | 13px | 400 | Body secundário |
| `--text-base` | Inter | 15px | 400 | Body principal |
| `--text-lg` | Inter | 17px | 500 | Sub-títulos |
| `--text-xl` | Inter | 20px | 600 | Títulos de tela |
| `--text-2xl` | Inter | 24px | 700 | KPIs, destaques |
| `--text-3xl` | Inter | 30px | 700 | Número grande |

#### Componentes-chave

| Componente | Variantes |
|---|---|
| `Button` | primary, secondary, ghost, danger, icon-only |
| `Input` | default, error, disabled, with-icon |
| `Select` | default, searchable, multi |
| `RankBadge` | leader, trainer, member, recruit |
| `EventTypeBadge` | fixed, seasonal, special |
| `Modal` | sm (400px), md (600px), lg (800px) |
| `Toast` | success, warning, error, info |
| `Table` | sortable, selectable, paginated |
| `EmptyState` | com ícone + CTA |
| `Card` | KPI card (número + label + trend) |

#### Ícones

Biblioteca: `lucide-svelte` (árvore abalável, TypeScript-friendly).

| Ação | Ícone |
|---|---|
| Adicionar | `Plus` |
| Editar | `Pencil` |
| Remover | `Trash2` |
| Salvar | `Save` |
| Buscar | `Search` |
| Membros | `Users` |
| Times | `Layers` |
| Eventos | `Calendar` |
| Escala | `ClipboardList` |
| Casais | `Heart` |
| Disponibilidade | `Clock` |
| Config | `Settings` |
| Gerar | `Zap` |
| Exportar | `Download` |

### Estrutura de Navegação

```
Sidebar (220px, sempre escura)
├── [Logo + nome do app]
├── ── Visão Geral ──
│   └── 📊 Dashboard          (Ctrl+1)
├── ── Cadastros ──
│   ├── 👥 Membros            (Ctrl+2)
│   ├── 🗂️  Times              (Ctrl+3)
│   └── 📅 Eventos            (Ctrl+4)
├── ── Escala ──
│   ├── ⚡ Gerar Escala       (Ctrl+5)
│   └── 👫 Casais             (Ctrl+6)
└── ── Configurações ──
    ├── 🕐 Disponibilidade    (Ctrl+7)
    └── ⚙️  Preferências
```

### Wireframes Principais

#### Shell Geral
```
┌──────────────────────────────────────────────────────────────┐
│ ┌────────────┐ ┌────────────────────────────────────────────┐ │
│ │  SIDEBAR   │ │              CONTENT AREA                  │ │
│ │  220px     │ │                                            │ │
│ │            │ │  ┌──────────────────────────────────────┐  │ │
│ │  🎬 ESCALA │ │  │  [Título da Tela]    [+ Adicionar]   │  │ │
│ │  MÍDIA     │ │  │  [Busca / Filtros]                    │  │ │
│ │            │ │  └──────────────────────────────────────┘  │ │
│ │  ▶ Dash    │ │                                            │ │
│ │  • Membros │ │  ┌──────────────────────────────────────┐  │ │
│ │  • Times   │ │  │         CONTEÚDO PRINCIPAL            │  │ │
│ │  • Eventos │ │  │         (tabela / cards / form)       │  │ │
│ │  • Escala  │ │  │                                       │  │ │
│ │  • Casais  │ │  └──────────────────────────────────────┘  │ │
│ │            │ │                                            │ │
│ │  ──────── │ │                                            │ │
│ │  ⚙ Config │ │                                            │ │
│ └────────────┘ └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

#### Tela Membros (painel duplo)
```
┌─ Membros ─────────────────────────── [🔍 Buscar] [+ Membro] ─┐
│ ┌─────────────────────────────────┐ ┌───────────────────────┐ │
│ │ Nome          Patente   Times   │ │ João Silva            │ │
│ │ ─────────────────────────────  │ │ ● Leader              │ │
│ │ ► João Silva  👑 Líder   2      │ │                       │ │
│ │   Ana Lima    🎓 Trainer  1     │ │ 📞 (11) 99999-9999    │ │
│ │   Pedro Costa ✓ Membro  3      │ │ ✉  joao@email.com     │ │
│ │   ...                          │ │ 📷 @joaosilva         │ │
│ │                                │ │                       │ │
│ │                                │ │ Times:                │ │
│ │                                │ │ [🎬 Câmera] [🎛 Audio] │ │
│ │                                │ │                       │ │
│ │                                │ │ [✏ Editar] [🗑 Remover]│ │
│ └─────────────────────────────── ┘ └───────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

#### Gerar Escala
```
┌─ Gerar Escala ───────────────────────────────────────────────┐
│  Evento: [Culto Dominical          ▼]  Período: [março 2024] │
│  Datas:  ☑ 03/03  ☑ 10/03  ☑ 17/03  ☑ 24/03  ☑ 31/03      │
│  [⚡ Gerar Escala]                                            │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ Data    │ Câmera          │ Áudio       │ Transmissão  │   │
│ │ 03/03   │ João · Ana      │ Pedro       │ Maria · Luiz │   │
│ │ 10/03   │ Carlos · Rita   │ João        │ Ana · Pedro  │   │
│ │ ...                                                     │   │
│ └────────────────────────────────────────────────────────┘   │
│  [📋 Copiar] [📤 Exportar CSV] [📤 Exportar PDF]              │
└──────────────────────────────────────────────────────────────┘
```

### Acessibilidade

- **Contraste mínimo:** WCAG 2.1 AA (4.5:1 para texto, 3:1 para UI)
- **Navegação por teclado:** Toda interação acessível via Tab/Enter/Escape/Arrows
- **Focus trap:** Modais e drawers travam o foco (usando `inert` attribute)
- **ARIA:** `role`, `aria-label`, `aria-live` em regiões dinâmicas
- **Reduced motion:** `@media (prefers-reduced-motion: reduce)` aplicado
- **Targets mínimos de clique:** 36×36px (preferencialmente 44×44px)

### Dark Mode

- Padrão do app: **dark** (sidebar sempre escura)
- Toggle: botão ⊙/☽ no rodapé da sidebar
- Persistência: `tauri-plugin-store` → `preferences.json`
- Implementação: CSS `[data-theme]` attribute no `<html>` — sem FOUC

---

## 9. Segurança

### Tauri Capabilities

Cada capability define exatamente o que o frontend pode fazer:

```json
// src-tauri/capabilities/default.json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Permissões padrão do app",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "sql:default",
    "store:default",
    "fs:allow-read-text-file",
    "fs:allow-write-text-file",
    "dialog:allow-save",
    "notification:default",
    "updater:default"
  ]
}
```

### CSP (Content Security Policy)

```json
// tauri.conf.json
"security": {
  "csp": "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"
}
```

### Princípios

| Princípio | Implementação |
|---|---|
| Least Privilege | Apenas capabilities necessárias declaradas |
| No Dangling Perms | `allowlist` explícita — tudo bloqueado por padrão |
| Input Validation | Validação no backend Rust (antes de tocar o DB) |
| SQL Injection | SQLx usa prepared statements parametrizados |
| Local Data Only | App offline-first — sem dados saindo do dispositivo |
| Sensitive Fields | Telefone/email/instagram não logados/impressos |

---

## 10. Deploy e Distribuição

### Targets de Build

| Plataforma | Formato | Assinatura |
|---|---|---|
| Windows | `.msi` + `.exe` (NSIS) | Code signing (cert EV) |
| macOS | `.dmg` + `.app` | Apple Developer ID + Notarização |
| Linux | `.AppImage` + `.deb` + `.rpm` | GPG |

### Configuração de Bundle

```json
// src-tauri/tauri.conf.json (bundle section)
{
  "bundle": {
    "identifier": "br.com.escalamidia.app",
    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/icon.icns", "icons/icon.ico"],
    "publisher": "Escala Mídia",
    "copyright": "MIT",
    "shortDescription": "Gestão de escala para time de mídia",
    "longDescription": "App desktop para coordenação de voluntários do time de mídia de igrejas.",
    "windows": {
      "wix": { "language": "pt-BR" },
      "nsis": { "language": 1046 }
    },
    "macOS": { "minimumSystemVersion": "12.0" },
    "linux": { "depends": ["libwebkit2gtk-4.1-0"] }
  }
}
```

### Auto-Update

```rust
// No startup do app
tauri::Builder::default()
  .plugin(tauri_plugin_updater::Builder::new().build())
  .setup(|app| {
      let handle = app.handle().clone();
      tauri::async_runtime::spawn(async move {
          if let Ok(Some(update)) = handle.updater()?.check().await {
              // Notificar usuário e aplicar update
          }
      });
      Ok(())
  })
```

Endpoint de update: GitHub Releases com `latest.json` por plataforma.

### Banco de Dados em Produção

- Localização: `$APPDATA/escala-midia/data.db` (Windows), `~/.local/share/escala-midia/data.db` (Linux), `~/Library/Application Support/escala-midia/data.db` (macOS)
- Acesso via `tauri::api::path::app_data_dir()`
- Migrations executadas automaticamente no startup via `sqlx::migrate!()`

---

## 11. Processo de Desenvolvimento (TDD)

### Workflow Red-Green-Refactor

```
1. RED    → Escrever teste que falha (descreve comportamento esperado)
2. GREEN  → Implementar o mínimo para o teste passar
3. REFACTOR → Melhorar código sem quebrar testes
```

### Fluxo por Feature

```
GitHub Issue (comportamento) 
  → Testes unitários (Vitest / Rust #[test]) — RED
  → Implementação mínima — GREEN  
  → Testes de integração — RED → GREEN
  → Refactoring
  → PR com coverage report
  → Code review
  → E2E test — RED → GREEN
  → Merge
```

### Cobertura de Testes

| Fase | Cobertura Mínima |
|---|---|
| Durante desenvolvimento | **75%** linhas + **70%** branches |
| Release candidate | **90%** linhas + **85%** branches |
| Versão final (1.0) | **100%** linhas + **100%** branches |

Gates de CI bloqueiam merge se cobertura cair abaixo do mínimo da fase atual.

---

## 12. Estratégia de Testes

### Pirâmide de Testes

```
         /\
        /E2E\          ← Playwright (5-10 fluxos críticos)
       /──────\
      / Integr.\       ← Vitest + Tauri mock / Rust #[tokio::test]
     /──────────\
    /   Unit     \     ← Vitest (frontend) + #[test] (Rust)
   ──────────────────
```

### 1. Testes Unitários (Frontend — Vitest)

**O que testar:**
- Funções puras em `$lib/utils/`
- Lógica de stores isolada (mockando `invoke`)
- Componentes: renderização, eventos, props edge cases

```typescript
// src/lib/utils/schedule.test.ts
import { describe, it, expect } from 'vitest';
import { filterAvailableMembers } from './schedule';

describe('filterAvailableMembers', () => {
  it('removes unavailable members', () => {
    const members = [{ id: '1', name: 'João' }, { id: '2', name: 'Ana' }];
    const unavailable = ['1'];
    expect(filterAvailableMembers(members, unavailable, '2024-03-03'))
      .toEqual([{ id: '2', name: 'Ana' }]);
  });
});
```

**Cobertura alvo:** 100% das funções em `utils/` e `stores/`

### 2. Testes Unitários (Backend — Rust)

```rust
// src-tauri/src/services/schedule_service.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_filter_unavailable_members() {
        let members = vec![
            Member { id: "1".into(), name: "João".into(), ..Default::default() },
            Member { id: "2".into(), name: "Ana".into(), ..Default::default() },
        ];
        let unavailable = vec!["1".to_string()];
        let result = filter_available(&members, &unavailable);
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].id, "2");
    }
}
```

**Cobertura alvo:** 100% de `services/` e `models/`

### 3. Testes de Integração (Rust + SQLite em memória)

```rust
// src-tauri/src/db/member_repo.rs
#[cfg(test)]
mod integration {
    use sqlx::SqlitePool;
    
    #[tokio::test]
    async fn test_create_and_get_member() {
        let pool = SqlitePool::connect(":memory:").await.unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();
        
        let member = member_repo::create(&pool, CreateMemberDto {
            name: "Test User".into(),
            ..Default::default()
        }).await.unwrap();
        
        let found = member_repo::get_by_id(&pool, &member.id).await.unwrap();
        assert_eq!(found.name, "Test User");
    }
}
```

**Cobertura alvo:** Todos os repos — happy path + erros principais

### 4. Testes E2E (Playwright + Tauri WebDriver)

Usando [`@tauri-apps/api/mocks`](https://github.com/tauri-apps/tauri/tree/dev/tooling/api) e o driver oficial do Tauri para Playwright:

```typescript
// tests/e2e/members.spec.ts
import { test, expect } from '@playwright/test';
import { setup, teardown } from './fixtures/tauri';

test.beforeAll(async () => { await setup(); });
test.afterAll(async () => { await teardown(); });

test('criar membro e verificar na lista', async ({ page }) => {
  await page.click('[data-testid="nav-members"]');
  await page.click('[data-testid="btn-add-member"]');
  
  await page.fill('[data-testid="input-name"]', 'João Silva');
  await page.fill('[data-testid="input-email"]', 'joao@test.com');
  await page.selectOption('[data-testid="select-rank"]', 'member');
  await page.click('[data-testid="btn-save"]');
  
  await expect(page.locator('[data-testid="members-table"]'))
    .toContainText('João Silva');
});
```

**Fluxos E2E obrigatórios:**
1. Criar membro → aparece na lista
2. Criar time → associar membros → verificar associação
3. Criar evento → configurar times → verificar configuração
4. Fluxo completo: membros + times + evento → gerar escala → verificar resultado
5. Registrar indisponibilidade → gerar escala → confirmar membro ausente
6. Cadastrar casal → gerar escala → confirmar que não são escalados juntos

### 5. Testes de Regressão

- Executados a cada PR e em tag releases
- Cobrem todos os E2E + snapshot tests de componentes críticos (ScheduleTable)
- `playwright --reporter=html` para relatório visual

### 6. Testes CFI (Component Functional Integration)

Testa componente Svelte + store + mock de invoke juntos:

```typescript
// src/lib/components/domain/MembersList.test.ts
import { render, fireEvent } from '@testing-library/svelte';
import { vi } from 'vitest';
import * as tauriApi from '@tauri-apps/api/core';
import MembersList from './MembersList.svelte';

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn().mockResolvedValue([
    { id: '1', name: 'João', rank: 'member' }
  ])
}));

test('exibe membros e abre modal ao clicar em adicionar', async () => {
  const { getByText, getByTestId } = render(MembersList);
  await screen.findByText('João');
  
  fireEvent.click(getByTestId('btn-add-member'));
  expect(getByTestId('modal-create-member')).toBeVisible();
});
```

### Ferramentas de Cobertura

| Camada | Ferramenta | Relatório |
|---|---|---|
| Frontend (JS/TS) | `@vitest/coverage-v8` | HTML + LCOV |
| Backend (Rust) | `cargo-tarpaulin` (Linux) / `cargo-llvm-cov` | HTML + LCOV |
| E2E | Playwright built-in | HTML |
| Consolidado | `codecov.io` | Badge + PR comment |

---

## 13. CI/CD

### Workflows GitHub Actions

#### `test.yml` — Executado em todo PR

```yaml
name: Tests
on: [push, pull_request]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:coverage
      - name: Check coverage threshold
        run: npx vitest run --coverage --coverage.thresholds.lines=75

  rust-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - run: cargo test --manifest-path src-tauri/Cargo.toml
      - run: cargo install cargo-tarpaulin && cargo tarpaulin --min-average-coverage 75

  e2e-tests:
    needs: [frontend-tests, rust-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install system deps (WebKit)
        run: sudo apt-get install -y libwebkit2gtk-4.1-dev libgtk-3-dev
      - run: npm ci && npx playwright install
      - run: npm run test:e2e
```

#### `release.yml` — Tag `v*.*.*`

```yaml
name: Release
on:
  push:
    tags: ['v*.*.*']

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-22.04
            target: x86_64-unknown-linux-gnu
          - os: windows-latest
            target: x86_64-pc-windows-msvc
          - os: macos-latest
            target: aarch64-apple-darwin
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: tauri-apps/tauri-action@v0
        env:
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_PRIVATE_KEY }}
          APPLE_CERTIFICATE: ${{ secrets.APPLE_CERTIFICATE }}
          APPLE_ID: ${{ secrets.APPLE_ID }}
        with:
          tagName: ${{ github.ref_name }}
          releaseName: 'Escala Mídia ${{ github.ref_name }}'
```

---

## 14. Decisões de Design (ADRs)

### ADR-001: Tauri v2 em vez de Electron

**Decisão:** Usar Tauri v2.  
**Motivação:** Bundle 10–20x menor (~4MB vs ~80MB), sem Node.js runtime empacotado, WebView nativa do SO, backend em Rust (segurança de memória), licença MIT.  
**Trade-off:** Ecosistema menor que Electron; Rust tem curva de aprendizado maior.

### ADR-002: Svelte em vez de React/Vue

**Decisão:** Svelte 5 + TypeScript.  
**Motivação:** Sem virtual DOM (ideal para app desktop), sintaxe simples, bundle menor, runes (Svelte 5) para reatividade granular. Time pode aprender mais facilmente vindo de Python/Tkinter.  
**Trade-off:** Menos recursos de aprendizado que React; TanStack Query tem suporte Svelte experimental.

### ADR-003: SQLx em vez de Diesel

**Decisão:** SQLx com SQL puro + verificação em compile-time.  
**Motivação:** Macros que validam SQL contra o schema na compilação, suporte async nativo, flexibilidade para queries complexas (algoritmo de escala).  
**Trade-off:** Não gera código automaticamente; requer escrever SQL manualmente.

### ADR-004: Offline-first sem sync

**Decisão:** Dados 100% locais, sem backend remoto.  
**Motivação:** Simplicidade máxima para o contexto de uso (church media team), sem custo de infra, privacidade.  
**Trade-off:** Sem sincronização entre dispositivos; backup manual via exportação.

### ADR-005: UUIDs como chave primária

**Decisão:** `TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16))))` no SQLite.  
**Motivação:** Portabilidade (exportar/importar dados), sem auto-increment race conditions, IDs seguros para expor no frontend.  
**Trade-off:** Levemente mais lento que INTEGER PK para lookups.

---

*Documento gerado em: 2026-03-05*  
*Próxima revisão: antes do início da implementação*
