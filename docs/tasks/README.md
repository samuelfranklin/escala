# docs/tasks — Fluxo de Tasks

Este diretório contém todas as tasks de desenvolvimento do projeto **Escala Mídia**.

---

## Nomenclatura dos Arquivos

```
TASK-[NNN]-[DOMÍNIO]-[SLUG]-[STATUS].md
```

| Parte | Descrição | Exemplo |
|---|---|---|
| `NNN` | Número sequencial com zero-padding | `001`, `012` |
| `DOMÍNIO` | Área da task | `BACKEND`, `FRONTEND`, `INFRA`, `UX`, `TEST` |
| `SLUG` | Descrição curta em kebab-case | `member-crud`, `schedule-generator` |
| `STATUS` | Estado atual da task | `WAITING`, `DOING`, `DONE`, `BLOCKED` |

**Exemplo:** `TASK-003-BACKEND-member-crud-DOING.md`

---

## Status das Tasks

| Status | Significado |
|---|---|
| `WAITING` | Aguardando pré-requisito ou priorização |
| `DOING` | Em andamento (uma task por domínio por vez) |
| `DONE` | Concluída, testada e mergeada |
| `BLOCKED` | Impedida — motivo documentado dentro do arquivo |

---

## Estrutura de uma Task

Cada arquivo de task segue este template:

```markdown
# TASK-NNN — Título da Task

**Domínio:** BACKEND | FRONTEND | INFRA | UX | TEST  
**Status:** WAITING | DOING | DONE | BLOCKED  
**Prioridade:** P0 (bloqueante) | P1 (alta) | P2 (normal) | P3 (baixa)  
**Depende de:** TASK-NNN (ou "nenhuma")  
**Estimativa:** S (< 2h) | M (2–6h) | L (6–12h) | XL (> 12h)

## Descrição

O que precisa ser feito e por quê.

## Critérios de Aceite

- [ ] Critério 1
- [ ] Critério 2
- [ ] Testes passando com cobertura ≥ 75%

## Notas Técnicas

Referências, decisões de design, riscos conhecidos.

## Progresso

- [ ] Sub-tarefa 1
- [ ] Sub-tarefa 2
```

---

## Fluxo de Trabalho

```
WAITING ──► DOING ──► DONE
              │
              ▼
           BLOCKED ──► DOING (após resolução)
```

1. **Ao iniciar uma task:** renomear o arquivo (WAITING → DOING) e criar um commit `chore: start TASK-NNN`
2. **Durante a task:** atualizar o campo Progresso dentro do arquivo
3. **Ao concluir:** renomear (DOING → DONE), fazer o commit final referenciando a task
4. **Se bloqueada:** renomear (DOING → BLOCKED) e documentar o motivo + o que precisa ser resolvido

---

## Convenção de Commits

Commits relacionados a tasks devem referenciar o número:

```
feat(members): implement CRUD commands [TASK-003]
test(members): add unit tests for MemberService [TASK-003]
```

---

## Tasks por Domínio

| Domínio | Descrição |
|---|---|
| `BACKEND` | Rust: commands, services, models, migrations |
| `FRONTEND` | Svelte: pages, components, stores, API layer |
| `INFRA` | Tauri config, CI/CD, bundling, deploy |
| `TEST` | Suites de teste cross-layer (E2E, regressão) |
| `UX` | Design system, wireframes, acessibilidade |
| `DOCS` | Documentação técnica e de produto |
