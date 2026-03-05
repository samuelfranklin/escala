# TASK-002 — Migrations SQLite com SQLx + Seed de Desenvolvimento

**Domínio:** INFRA  
**Status:** WAITING  
**Prioridade:** P0 — bloqueia todos os CRUDs e o gerador  
**Depende de:** TASK-001  
**Estimativa:** M (2–6h)

---

## Descrição

Criar as migrations SQLite versionadas usando `sqlx-cli` com o schema completo
definido na spec §5. Configurar o `pool.rs` com inicialização do banco e
execução automática de migrations no startup. Criar seed de dados realistas
para desenvolvimento e testes.

---

## Critérios de Aceite

- [ ] `sqlx-cli` instalado e documentado no `README`
  (`cargo install sqlx-cli --no-default-features --features sqlite`)
- [ ] Diretório `src-tauri/migrations/` com as migrations na ordem correta:
  - `20240101_001_members.sql` — tabela `members`
  - `20240101_002_squads.sql` — tabelas `squads` e `members_squads`
  - `20240101_003_events.sql` — tabelas `events` e `events_squads`
  - `20240101_004_couples.sql` — tabela `couples`
  - `20240101_005_availability.sql` — tabela `availability`
  - `20240101_006_schedules.sql` — tabelas `schedules` e `schedule_members`
- [ ] Cada migration contém os `CHECK`, `REFERENCES … ON DELETE CASCADE` e
  `DEFAULT` exatos da spec §5
- [ ] `db/pool.rs` implementado:
  - `create_pool(app_handle)` resolve o path do DB por plataforma
    via `app_handle.path().app_data_dir()`
  - Executa `sqlx::migrate!("./migrations").run(&pool)` no startup
  - Configura `PRAGMA foreign_keys = ON`
  - Configura `PRAGMA journal_mode = WAL`
- [ ] `lib.rs` registra `AppState { db: pool }` via `.manage()`
- [ ] `src-tauri/migrations/seed_dev.sql` com dados de desenvolvimento:
  - ≥ 8 membros com ranks variados (leader, trainer, member, recruit)
  - ≥ 3 squads (ex.: Câmera, Áudio, Transmissão)
  - Associações `members_squads` realistas
  - ≥ 2 eventos (fixed + seasonal)
  - ≥ 1 casal
  - ≥ 2 registros de availability
- [ ] `cargo test` passa nos testes de migration (pool in-memory)
- [ ] Testes passando com cobertura ≥ 75%
- [ ] `cargo clippy -- -D warnings` sem warnings

---

## Notas Técnicas

### Estrutura de Migrations

Cada arquivo de migration contém apenas `CREATE TABLE` + índices relevantes
para leitura frequente. Nunca alterar migrations já commitadas — criar nova
migration para mudanças futuras.

