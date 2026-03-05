# TASK-001 — Scaffold do Projeto Tauri v2 + Svelte + Rust

**Domínio:** INFRA  
**Status:** WAITING  
**Prioridade:** P0 — bloqueia todas as demais tasks  
**Depende de:** nenhuma  
**Estimativa:** M (2–6h)

---

## Descrição

Inicializar do zero a estrutura completa do projeto **Escala Mídia** usando
`npm create tauri-app`, configurar o workspace Rust/Cargo, ajustar
`tauri.conf.json` com as capabilities corretas, e criar a estrutura de pastas
exata definida na spec §4.

Este scaffold é o pré-requisito absoluto de todo desenvolvimento: sem ele não
há compilação, banco, nem commands.

---

## Critérios de Aceite

- [ ] `npm create tauri-app@latest` executado com template `svelte-ts`
- [ ] `src/` segue estrutura da spec §4:
  - `lib/api/`, `lib/components/ui/`, `lib/components/layout/`,
    `lib/components/domain/`, `lib/stores/`, `lib/types/`, `lib/utils/`
  - `routes/` com arquivos stub para todas as rotas:
    `dashboard`, `members`, `squads`, `events`, `schedule`, `couples`,
    `availability`
- [ ] `src-tauri/src/` segue estrutura da spec §4:
  - `commands/mod.rs` + stubs `member.rs`, `squad.rs`, `event.rs`,
    `schedule.rs`, `couple.rs`, `availability.rs`
  - `services/mod.rs` + stubs correspondentes
  - `db/mod.rs` + `pool.rs`
  - `models/mod.rs` + stubs correspondentes
  - `errors.rs` com `AppError` (thiserror) já definido
  - `state.rs` com `AppState { db: SqlitePool }`
- [ ] `src-tauri/Cargo.toml` com todas as dependências da spec §2:
  - `tauri = "2"`, `sqlx = { version = "0.8", features = ["sqlite","runtime-tokio","macros","migrate"] }`
  - `serde`, `serde_json`, `thiserror`, `chrono`, `uuid`, `tokio`
- [ ] Plugins Tauri configurados em `Cargo.toml`:
  `tauri-plugin-sql`, `tauri-plugin-store`, `tauri-plugin-notification`,
  `tauri-plugin-dialog`, `tauri-plugin-fs`, `tauri-plugin-updater`
- [ ] `src-tauri/tauri.conf.json` configurado:
  - `identifier`: `br.com.escalamidia.app`
  - `bundle` completo conforme spec §10
  - `security.csp` conforme spec §9
- [ ] `src-tauri/capabilities/default.json` com permissões da spec §9
- [ ] `vite.config.ts`, `svelte.config.js`, `tsconfig.json` configurados
- [ ] `cargo build` sem erros
- [ ] `npm run tauri dev` abre janela com tela em branco (sem crash)
- [ ] `cargo clippy -- -D warnings` sem warnings
- [ ] Testes passando com cobertura ≥ 75%

---

## Notas Técnicas

### Comando de Criação

