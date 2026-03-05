# AGENTS.md — Fonte da Verdade para Agentes de IA

> Este arquivo é a **primeira leitura obrigatória** para qualquer agente de IA que atue neste repositório.
> Leia-o integralmente antes de executar qualquer tarefa.

---

## 1. Sobre o Projeto

**Escala Mídia** é um app desktop multiplataforma para gestão de escalas do time de mídia de igrejas.
Construído integralmente com **AI Pair-Coding** (GitHub Copilot CLI + subagentes especializados).

- **Branch principal de desenvolvimento:** `feat/tauri-migration`
- **Spec técnica completa:** [`docs/specs/app.spec.md`](docs/specs/app.spec.md)
- **PDR Tauri:** [`docs/pdrs/PDR-TAURI-001.md`](docs/pdrs/PDR-TAURI-001.md)
- **PDR Rust:** [`docs/pdrs/PDR-RUST-001.md`](docs/pdrs/PDR-RUST-001.md)
- **Tasks:** [`docs/tasks/`](docs/tasks/) — leia o [`docs/tasks/README.md`](docs/tasks/README.md)

---

## 2. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| **Framework desktop** | Tauri v2 |
| **Backend** | Rust (stable) + SQLx + SQLite |
| **Frontend** | Svelte 5 + TypeScript + Vite |
| **Testes unitários** | Vitest (frontend) · `cargo test` (backend) |
| **Testes E2E** | Playwright + Tauri WebDriver |
| **CI/CD** | GitHub Actions |
| **Deploy** | `tauri-apps/tauri-action` → Windows MSI, Linux AppImage/deb, macOS DMG |

---

## 3. Arquitetura (resumo)

```
src/                    ← Frontend Svelte/TS
  lib/api/              ← Wrappers invoke() tipados
  lib/components/       ← ui/ · layout/ · domain/
  lib/stores/           ← Estado global
  routes/               ← Páginas (members, squads, events, schedule…)

src-tauri/src/
  commands/             ← Handlers Tauri (#[tauri::command])
  services/             ← Lógica de negócio pura (sem Tauri)
  models/               ← Structs de domínio + Serde
  db/                   ← SQLx queries + migrations
  errors/               ← thiserror types

docs/
  pdrs/                 ← Documentos de pesquisa (Tauri, Rust)
  specs/                ← Especificação técnica do produto
  tasks/                ← Tasks de desenvolvimento
```

Toda comunicação frontend ↔ backend passa por `invoke()` (IPC Tauri). Sem acesso direto ao filesystem ou banco pelo frontend — apenas via Tauri commands.

---

## 4. Domínio

| Entidade | Descrição |
|---|---|
| `Member` | Membro do time de mídia (nome, telefone, email, instagram) |
| `Squad` | Time/departamento (ex.: câmera, som, transmissão) |
| `Event` | Culto/evento com data, tipo e config de escala |
| `Schedule` | Escala gerada — lista de alocações Member × Squad × Event |
| `Couple` | Restrição: dois membros que não devem ser escalados juntos |
| `Availability` | Indisponibilidade de membro em data específica |

---

## 5. Convenções de Código

### Rust (backend)
- Erros sempre via `thiserror` — nunca `.unwrap()` em produção
- Funções puras em `services/` → chamadas por `commands/` (thin handlers)
- SQLx com macros `query!`/`query_as!` (verificação em compile-time)
- Structs de domínio derivam `Serialize, Deserialize, Debug, Clone`
- IDs: `String` (UUID v4)

### Svelte/TypeScript (frontend)
- TypeScript estrito (`"strict": true`)
- Types em `src/lib/types/index.ts` — espelham exatamente as structs Rust
- Toda chamada ao backend usa wrappers em `src/lib/api/` — nunca `invoke()` direto nos componentes
- Stores Svelte para estado global; props para estado local

### Geral
- Commits: Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`)
- Sempre incluir trailer: `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`
- Nomenclatura: domínio de UI em PT-BR, entidades de código em EN

---

## 6. Processo de Desenvolvimento (TDD)

```
RED   → Escrever teste que falha (descreve o comportamento desejado)
GREEN → Implementar o mínimo para o teste passar
REFACTOR → Melhorar o código sem quebrar testes
```

**Cobertura mínima:**
- `>= 75%` durante desenvolvimento
- `>= 90%` em Release Candidate
- `100%` em v1.0

**Tipos de teste (todos obrigatórios):**
1. **Unitário** — funções puras em `services/` e helpers frontend
2. **Integração** — commands Tauri com banco real (SQLite in-memory)
3. **E2E** — fluxos completos via Playwright + Tauri WebDriver
4. **CFI (Component)** — componentes Svelte isolados com Vitest
5. **Regressão** — suite de smoke tests executada a cada PR

---

## 7. Tasks e Fluxo de Trabalho

As tasks de desenvolvimento estão em [`docs/tasks/`](docs/tasks/).

**Status das tasks:**
- `WAITING` — aguardando pré-requisito ou priorização
- `DOING` — em andamento
- `DONE` — concluída e mergeada
- `BLOCKED` — impedida (motivo descrito no arquivo)

Antes de iniciar qualquer task, leia o arquivo correspondente em `docs/tasks/` para entender escopo, critérios de aceite e dependências.

---

## 8. Segurança

- **Capabilities Tauri:** least-privilege — apenas o necessário habilitado por feature
- **CSP:** `default-src 'self'` — sem CDNs externos em produção
- **Dados sensíveis** (telefone, email, instagram): nunca em logs, commits ou outputs de agentes
- **`.ENV` local:** nunca versionar; usar apenas para `DATABASE_URL` de dev

---

## 9. Referências Rápidas

| Recurso | Caminho |
|---|---|
| Spec técnica completa | `docs/specs/app.spec.md` |
| Pesquisa Tauri v2 | `docs/pdrs/PDR-TAURI-001.md` |
| Pesquisa Rust | `docs/pdrs/PDR-RUST-001.md` |
| Tasks de desenvolvimento | `docs/tasks/` |
| Fluxo de tasks | `docs/tasks/README.md` |
