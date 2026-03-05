# TASK-016 — Configurar GitHub Actions (CI/CD Pipelines)

**Domínio:** INFRA  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-001 (scaffold do projeto existe com `src-tauri/` e `src/` estruturados)  
**Estimativa:** L

---

## Descrição

Criar os três workflows GitHub Actions que cobrem todo o ciclo de vida do projeto:

1. **`test.yml`** — Roda em todo push e PR: testes unitários Rust + testes unitários/CFI frontend + cobertura com gate mínimo de 75%.
2. **`e2e.yml`** — Disparado após `test.yml` concluir com sucesso: executa a suite Playwright + Tauri WebDriver no runner Linux com display virtual (`xvfb`).
3. **`release.yml`** — Disparado em tags `v*.*.*`: build multiplataforma via `tauri-apps/tauri-action`, assina (macOS Developer ID + notarização + Windows Code Signing), cria GitHub Release com todos os assets.

A pipeline deve ser **fail-fast** (nenhum merge chega a `main` sem todos os gates passando) e **incremental** (E2E só roda se unit tests passaram; release é build-only, mas exige que os testes estejam passando na branch de origem).

---

## Critérios de Aceite

- [ ] `test.yml` dispara em `push` e `pull_request` para todas as branches
- [ ] Job `rust-tests`: executa `cargo test`, `cargo clippy -- -D warnings` e `cargo tarpaulin` com `--min-average-coverage 75`
- [ ] Job `frontend-tests`: executa `npm ci`, `svelte-check` (type-check) e `vitest run --coverage` com `thresholds.lines=75` e `thresholds.branches=70`
- [ ] Ambos os jobs fazem upload dos relatórios de cobertura (HTML + LCOV) como artifacts com `retention-days: 14`
- [ ] `e2e.yml` usa `workflow_run` aguardando o workflow `Tests` concluir com `success`
- [ ] `e2e.yml` instala todas as dependências de sistema Ubuntu: `libwebkit2gtk-4.1-dev`, `libgtk-3-dev`, `libayatana-appindicator3-dev`, `librsvg2-dev`, `webkit2gtk-driver`, `xvfb`
- [ ] `e2e.yml` executa Playwright dentro de `xvfb-run --auto-servernum`
- [ ] `e2e.yml` faz upload do relatório HTML Playwright (`if: always()`) e screenshots (`if: failure()`)
- [ ] `release.yml` dispara apenas em tags que casem com `v[0-9]+.[0-9]+.[0-9]+`
- [ ] `release.yml` usa matrix com 4 targets: Linux x64, Linux ARM64, Windows x64, macOS Apple Silicon
- [ ] `release.yml` usa `tauri-apps/tauri-action@v0` com todos os secrets de assinatura injetados via `env`
- [ ] GitHub Release criada como **draft** com `.dmg`, `.msi`, `.exe` (NSIS), `.AppImage`, `.deb`, `.rpm`
- [ ] `prerelease: true` automático para tags contendo `-alpha`, `-beta` ou `-rc`
- [ ] Rust cache via `Swatinem/rust-cache@v2` em todos os jobs Rust (`workspaces: src-tauri`)
- [ ] Node cache via `actions/setup-node` com `cache: 'npm'` em todos os jobs Node
- [ ] Branch `main` com branch protection exigindo `test / rust-tests` e `test / frontend-tests` como status checks obrigatórios
- [ ] `docs/ops/secrets.md` criado com tabela de todos os secrets (sem valores reais)

---

## Notas Técnicas

### Estrutura de Arquivos a Criar

