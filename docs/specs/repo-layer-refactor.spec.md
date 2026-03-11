# Spec — Refatoração Clean Architecture de todos os serviços

## Contexto

O `schedule_service` foi refatorado com sucesso aplicando Clean Architecture, SOLID e DRY:
- Módulos focados (scoring, recurrence, constraints, allocation)
- Queries movidas para o repo
- Service como orquestrador puro
- Testes isolados por módulo

Este spec documenta a aplicação dos mesmos princípios para **todos** os demais serviços.

---

## Referência: O que fizemos no schedule_service

| Princípio | Aplicação |
|-----------|-----------|
| **SRP** | Cada módulo tem uma responsabilidade (scoring, recurrence, constraints, allocation) |
| **OCP** | Novos critérios de score = novo módulo, sem alterar orquestrador |
| **DIP** | Service depende de abstrações (funções do repo), não de queries concretas |
| **DRY** | Lógica duplicada (couple propagation, monthly limit) extraída em funções reutilizáveis |
| **Separação de camadas** | Service = orquestração, Repo = dados, Módulos = lógica pura |

---

## Diagnóstico Completo — Todos os Serviços

### 1. member_service + member_repo

| Aspecto | Estado | Problema |
|---------|--------|----------|
| Separação service/repo | ✅ | Queries no repo |
| SQL injection | ❌ **CRÍTICO** | `member_repo::update()` usa `format!()` com interpolação |
| SRP | ⚠️ | Validação inline no service (misturada com orquestração) |
| DRY | ⚠️ | `validate_email()` é privada — não reutilizável por outros serviços |
| DRY | ⚠️ | `name.trim().is_empty()` duplicado em `create` e `update` |
| Testes | ⚠️ | 4 testes inline no service (deveriam estar em arquivo separado) |

**Ações:**
- Extrair `validation.rs` com funções puras: `validate_required_name()`, `validate_email()`
- Corrigir SQL injection no repo (query parametrizada)
- Separar testes em `tests.rs`

### 2. event_service + event_repo

| Aspecto | Estado | Problema |
|---------|--------|----------|
| Separação service/repo | ✅ | Queries no repo |
| SQL injection | ❌ **CRÍTICO** | `event_repo::update()` usa `format!()` — `event_date` e `event_type` **sem escape nenhum** |
| SRP | ⚠️ | Validação complexa de tipo de evento inline no `create_event()` |
| DRY | ⚠️ | Validação de nome duplicada (igual ao member e squad) |
| DRY | ⚠️ | Validação de `EventSquadDto` (min/max) poderia ser método no DTO |
| Testes | ⚠️ | 5+ testes inline + helper `create_test_squad()` com query direta |

**Ações:**
- Extrair validação de evento em módulo `validation.rs` (regras por event_type)
- Mover validação de `EventSquadDto` para método `validate()` no DTO ou módulo de validação
- Corrigir SQL injection no repo
- Limpar test helper → usar `squad_repo::create()`
- Separar testes em `tests.rs`

### 3. squad_service + squad_repo

| Aspecto | Estado | Problema |
|---------|--------|----------|
| Separação service/repo | ✅ | Queries no repo |
| SQL injection | ❌ **CRÍTICO** | `squad_repo::update()` usa `format!()` |
| SRP | ✅ | Service simples — só validação de nome + delegação |
| DRY | ⚠️ | Validação de nome é a mesma de member e event |
| Testes | ❌ | Zero testes |

**Ações:**
- Corrigir SQL injection no repo
- Compartilhar validação de nome via módulo common
- Adicionar testes unitários mínimos

### 4. couple_service + couple_repo

| Aspecto | Estado | Problema |
|---------|--------|----------|
| Separação service/repo | ✅ | |
| Segurança | ✅ | Queries parametrizadas |
| SRP | ✅ | Validação mínima e adequada (`a != b`) |
| Testes | ❌ | Zero testes |

**Ações:**
- Adicionar testes unitários (validação de self-couple, integração CRUD)

### 5. availability_service + availability_repo

| Aspecto | Estado | Problema |
|---------|--------|----------|
| Separação service/repo | ✅ | |
| Segurança | ✅ | Queries parametrizadas |
| SRP | ✅ | Validação mínima e adequada (date not empty) |
| DRY | ⚠️ | Validação de data vazia é genérica — poderia reutilizar helper |
| Testes | ❌ | Zero testes |

**Ações:**
- Validar formato da data (YYYY-MM-DD) — hoje aceita qualquer string
- Adicionar testes unitários

### 6. schedule_service ✅ (já refatorado)

| Aspecto | Estado |
|---------|--------|
| Separação service/repo | ✅ Queries no repo |
| Módulos focados | ✅ scoring, recurrence, constraints, allocation |
| Testes | ✅ 32 testes em 5 módulos |
| DRY | ✅ Lógica reutilizável extraída |

---

## Violações DRY Transversais

Padrões repetidos em múltiplos serviços que devem ser consolidados:

### 1. Validação de nome obrigatório (3 serviços)

```rust
// Repetido em: member_service, squad_service, event_service
// Tanto no create quanto no update (6 ocorrências no total)
if name.trim().is_empty() {
    return Err(AppError::Validation("Name cannot be empty".into()));
}
```

**Solução:** Módulo `validators` com:
```rust
pub fn require_non_empty(field: &str, value: &str) -> Result<(), AppError> { ... }
pub fn require_non_empty_opt(field: &str, value: Option<&str>) -> Result<(), AppError> { ... }
```

### 2. Padrão de update dinâmico inseguro (3 repos)

```rust
// Repetido em: member_repo, event_repo, squad_repo
let mut sets = vec!["updated_at = datetime('now')".to_string()];
if let Some(v) = &dto.field { sets.push(format!("field = '{}'", v.replace(...))) }
let sql = format!("UPDATE table SET {} WHERE id = '{}'", sets.join(", "), id);
```

**Solução:** Query parametrizada com fallback para valor atual (load-then-update).

### 3. Validação de email (isolada no member_service)

```rust
fn validate_email(email: &str) -> bool {
    let parts: Vec<&str> = email.split('@').collect();
    parts.len() == 2 && parts[1].contains('.')
}
```

**Solução:** Mover para `validators` — potencialmente reutilizável se eventos
ou squads ganharem campo de email no futuro.

---

## Arquitetura Alvo

```
src-tauri/src/
  commands/          ← Thin handlers (já ✅ — zero lógica)
  services/
    validators.rs    ← Funções puras de validação (DRY, testáveis)
    member_service/
      mod.rs         ← Orquestração (validação + repo)
      tests.rs       ← Testes isolados
    event_service/
      mod.rs
      tests.rs
    squad_service.rs ← Simples o bastante para ficar em 1 arquivo
    couple_service.rs
    availability_service.rs
    schedule_service/
      mod.rs         ← ✅ já refatorado
      scoring.rs
      recurrence.rs
      constraints.rs
      allocation.rs
      tests.rs
  db/
    member_repo.rs   ← Queries parametrizadas (sem format!)
    event_repo.rs
    squad_repo.rs
    couple_repo.rs   ← ✅ já seguro
    availability_repo.rs ← ✅ já seguro
    schedule_repo.rs ← ✅ já refatorado
```

---

## Tasks

| # | Prioridade | Escopo | Descrição |
|---|------------|--------|-----------|
| TASK-035 | P0 | `member_repo` | Eliminar SQL injection no `update()` |
| TASK-036 | P0 | `event_repo` | Eliminar SQL injection no `update()` |
| TASK-037 | P0 | `squad_repo` | Eliminar SQL injection no `update()` |
| TASK-038 | P1 | `services/` | Criar `validators.rs` — funções puras DRY |
| TASK-039 | P1 | `member_service` | Refatorar: usar validators + separar testes |
| TASK-040 | P1 | `event_service` | Refatorar: usar validators + limpar test helper + separar testes |
| TASK-041 | P2 | `squad_service` | Usar validators + adicionar testes |
| TASK-042 | P2 | `couple_service` | Adicionar testes unitários |
| TASK-043 | P2 | `availability_service` | Validar formato data + adicionar testes |

### Ordem de execução recomendada

```
TASK-035 → TASK-036 → TASK-037  (P0 — segurança, parallelizável)
    ↓
TASK-038                         (P1 — cria o módulo validators)
    ↓
TASK-039 → TASK-040              (P1 — refatora services que usam validators)
    ↓
TASK-041 → TASK-042 → TASK-043  (P2 — testes e ajustes menores)
```
