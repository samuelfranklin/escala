# Project Guidelines


## 🚀 CRITICAL READING BEFORE STARTING ANY FEATURE OR BUG FIX

**⚠️ MANDATORY:** Before implementing ANY feature or bug fix, read these documents in order:

1. **[AGENTS.md - Code Quality Standards](#code-quality-standards-mandatory---read-before-coding)** (this file, section below)
   - SOLID principles and patterns
   - Organizing code in helpers/ vs schemas/
   - Anti-patterns to avoid

**Expected Outcome After Reading:**
- ✅ You understand RED-FAILING → FIX → GREEN-PASSING workflow
- ✅ You know where to place tests and code
- ✅ You can write tests that demonstrate problems (RED) and solutions (GREEN)
- ✅ You're aware of 100% coverage requirement
___
## Code Style
- Projeto em Python 3 com UI Tkinter; mantenha estilo simples e legível, sem dependências desnecessárias.
- Use tipagem quando já houver padrão no módulo (ex.: `gui/main_window.py`, `services/member_service.py`), sem forçar refatoração ampla.
- Respeite a nomenclatura mista já existente: domínio da UI em PT-BR (`Membros`, `Escala`) e entidades ORM em EN (`Member`, `Event`, `Squad`).
- Em telas Tkinter, siga a organização por métodos privados (`_build_*`, `_on_*`) como em `gui/main_window.py` e `gui/membros.py`.

## Architecture
- Entrada principal: `app.py` (cria `tk.Tk()`, registra frames e chama `app.sincronizar()`).
- Shell da GUI: `gui/main_window.py` (sidebar, `register_frame`, navegação com `tkraise`, sincronização por `atualizar_lista`).
- Camada de dados: `infra/database.py` (modelos SQLAlchemy, `engine`, `session_scope`, `create_tables`).
- Camada de serviço: `services/member_service.py` (operações de membro usando `session_scope`).
- Há coexistência de padrões: parte da GUI usa SQL direto via `db.conectar()` (ex.: `gui/membros.py`, `gui/squads.py`, `gui/eventos.py`). Preserve o padrão local do arquivo que você editar.

## Build and Test
- Ambiente: use a venv local em `.venv` quando disponível.
- Executar app: `python app.py`
- Desenvolvimento com auto-reload: `python watcher.py` (reinicia `app.py` ao alterar `.py`).
- Não há suíte de testes/configuração de build detectável (`pytest`, `pyproject.toml`, `requirements*.txt` não encontrados).

## Project Conventions
- Contrato de atualização de telas: frames que implementam `atualizar_lista` são atualizados por `SistemaEscalaApp.sincronizar()`.
- Para novas telas, registre via `app.register_frame("Nome", Frame(...))` em `app.py`.
- Mudanças em banco devem respeitar `session_scope` e relacionamentos/cascatas já definidos em `infra/database.py`.
- Evite “arrumar tudo” em uma tarefa: existem inconsistências legadas (ex.: pasta `sevices/`, imports antigos, partes comentadas) e alterações devem ser cirúrgicas.

## Integration Points
- Configuração de banco vem de `DATABASE_URL` (env) com fallback para leitura de `.ENV`/`.env` em `infra/database.py`.
- Default local é SQLite (`sqlite:///escala.db`) com `PRAGMA foreign_keys = ON` habilitado para cascata.
- A GUI integra módulos por referência a `app.frames[...]` (ex.: fluxo entre geração e visualização de escala).

## Security
- Trate como sensíveis os dados de membros (telefone, email, instagram) e evite expor em logs/prints.
- Não vaze conteúdo de `.ENV` (especialmente `DATABASE_URL`) em commits, issues ou respostas do agente.
- Evite versionar/duplicar artefatos locais de dados (`*.db`, backups `backup_*.db`, `escala_debug.log`) salvo solicitação explícita.


## Code Quality Standards (MANDATORY - Read Before Coding)
All code in this repository MUST adhere to these principles:

#### **SOLID Principles**
- **Single Responsibility**: Each function/module has ONE reason to change
  - Example: `calculateDownPaymentAmount()` only calculates, does not persist
  - Example: `validateOrderCreation()` only validates, does not mutate
  - Schema hooks call utility functions rather than implementing logic directly
  
- **Open/Closed**: Open for extension, closed for modification
  - Add new validation rules without changing existing ones
  - Create new utility functions in helpers/ rather than modifying hooks
  - Example: New order status handler added to `workOrder.helpers.ts` without touching Order schema
  
- **Liskov Substitution**: Derived types must be substitutable
  - All context parameters follow same interface pattern
  - Hooks preserve contract: input → process → output
  
- **Interface Segregation**: Clients depend only on interfaces they use
  - Each helper exports only necessary functions
  - Example: `order.helpers.ts` exports focused validation/calculation functions
  
- **Dependency Inversion**: Depend on abstractions, not concretions
  - Hooks call async utilities, not hardcoded database queries
  - Example: `getDownPaymentPercentage()` abstracts PricingConfig fetch

#### **Functional Programming**
- **Pure Functions**: No side-effects where possible
  - `calculateDeliveryDate(eventDate)` → Date | null (always same output for same input)
  - `calculateDownPaymentAmount(totalPrice, percentage)` → string (deterministic)
  - `signalPaidJustMarked(prev, new)` → boolean (comparison function)
  - Use pure functions in utilities before calling async/DB operations in hooks
  
- **Composition Over Inheritance**: Combine small functions
  - Order hook composition: resolveInput → validateInput → afterOperation (each layer calls utilities)
  - Example: WorkOrder hook calls `updateOrderStatusFromWorkOrder()` utility
  
- **Immutability**: Avoid modifying input parameters
  - Create new Date objects rather than mutating existing ones
  - Example: `const delivery = new Date(event); // not modifying event`
  - Return new objects from utilities, let hooks persist them
  
- **Higher-Order Functions**: Where applicable
  - Status transition logic encapsulated in testable functions
  - Example: `allWorkOrdersReady()` takes orderId and context, returns boolean

#### **Reutilizabilidade (Reusability)**
- **Utilities are shareable across hooks and schemas**
  - Functions in `helpers/` should be isolated and single-purpose
  - Example: `calculateDeliveryDate()` used by Order.resolveInput AND by any future system that needs delivery date logic
  - Example: `allWorkOrdersReady()` can be called from Order updates, notifications, reporting, etc.
  
- **Generic signatures over specific ones**
  - Avoid parameter types tied to specific contexts
  - Good: `calculateDownPaymentAmount(totalPrice: number | string, percentage: number): string`
  - Bad: `calculateDownPaymentAmount(order: Order): Decimal` (only works with Order, tightly coupled)
  
- **Export focused, narrow functions**
  - Each exported function should solve ONE problem reusably
  - Example: `validateOrderHasItems(items)` is generic, works with any item array
  - Example: `getDownPaymentPercentage(context)` is reusable anywhere percentage is needed
  - Do NOT export fat utility objects with dozens of methods
  
- **Zero coupling to Business Logic Flow**
  - Utilities don't know about hooks or schemas
  - Example: `calculateDeliveryDate()` doesn't care if it's called from Order creation or WorkOrder update
  - Example: `validateOrderCreation()` doesn't trigger side-effects; caller decides what to do with result
  
- **Copy-paste test**: If you need to use a function in a different context and can't easily change the call site, the function needs refactoring
  - Bad: Function has hardcoded assumptions about hook types
  - Good: Function works the same way in Order, WorkOrder, or even frontend contexts
  
- **Import patterns across workspaces**
  - Core utilities in `apps/backend/helpers/` can be imported by all backend modules
  - Shared logic in `packages/shared/` available to frontend and backend
  - Example: `packages/shared/date-utils.helper.ts` used by both apps

#### **Reutilizabilidade em Testes**
- **Test utilities in isolation first**
  - Pure functions tested without context/DB (fast, reusable test patterns)
  - Utilities tested once, hooks tested for orchestration only
  
- **Test fixtures shareable across suites**
  - Create test factories in `__tests__/fixtures/` for common data setup
  - Example: `createMockOrder()`, `createMockWorkOrder()` used by multiple test files
  
- **Avoid test duplication**
  - If same assertions appear in Order and WorkOrder tests, move to shared utility test
  - Example: Both test files call `validateOrderCreation()` → test utility once, reference in both

#### **Clean Code**
- **Naming**: Be explicit and descriptive
  - Functions: `calculateDownPaymentAmount` not `calc`, `validateOrderHasItems` not `check`
  - Variables: `totalPrice`, `downPaymentPercentage`, `orderId` (clear intent)
  - Avoid: `temp`, `data`, `value`, `result` (unless context is obvious)
  
- **Code Organization**:
  - Utilities in `apps/backend/helpers/` (one concern per file):
    - `order.helpers.ts` - Order logic only
    - `workOrder.helpers.ts` - WorkOrder logic only
    - `pricing.helpers.ts` - Pricing calculations only
  - Schema definitions in `apps/backend/schemas/` (Keystone list config)
  - Tests in `apps/backend/__tests__/` (mirror helper structure)
  
- **Function Size**: 
  - Pure utility functions: < 30 lines (easy to test, understand, reuse)
  - Hooks: < 100 lines (call utilities for logic, minimal orchestration)
  - Example: `calculateDeliveryDate()` is 8 lines, testable, focused
  
- **Comments**: Document WHY, not WHAT
  - Good: `// Only update if all work orders are ready (prevents premature status change)`
  - Bad: `// Update order`
  - Use JSDoc comments for exported functions (see `order.helpers.ts` examples)
  
- **Error Handling**: Explicit, don't swallow errors
  - Log errors: `console.error('Error calculating downPayment:', error)`
  - Return safe defaults: `return 10; // fallback percentage`
  - Throw errors in validation hooks to prevent invalid operations


#### **When Writing Code**
1. **First**: Write pure utility function in helpers/ → easy to test, reuse
2. **Second**: Call utility from hook → hooks stay thin, orchestration only
3. **Third**: Write tests for utilities first (pure functions are simplest to test)
4. **Fourth**: Write integration tests for hooks (harder, need DB/context)

#### **Anti-Patterns to AVOID**
- ❌ Logic inside schema hooks (put in helpers instead)
- ❌ Direct database calls without Prisma/context wrapper
- ❌ Async operations in pure functions (separate concerns)
- ❌ Side-effects in utility functions (testability suffers)
- ❌ Comments explaining WHAT the code does (it should be obvious from naming)
- ❌ Functions doing multiple things (calculate AND validate AND persist)
- ❌ Magic numbers/strings (use named constants or config)
- ❌ Silent failures (log errors, or throw explicitly)
- ❌ Tightly-coupled utilities (functions tied to specific schemas, can't be reused)
- ❌ Duplicated helper logic across multiple files (violates DRY)
- ❌ Utilities inside `__tests__/` that should be in `helpers/` (misses reuse opportunity)


---

## Conversation Operators (mandatory)

Use these operators to control interaction mode.

| Operator | Mode | Agent behavior |
| --- | --- | --- |
| `??` | Direct question mode | Do **not** execute tools, do **not** edit files, do **not** run commands. Only answer the user question clearly and directly. |
| `!?` | Collaborative reasoning mode | Do **not** execute tools, do **not** edit files, do **not** run commands. Discuss the problem collaboratively with the user until a solution direction is agreed. |
| `>>` | Continuation / sequential chaining mode | If `>>` appears at the **end** of the message, do **not** execute anything: only interpret, respond with understanding, and wait for the next part. If `>>` appears **between requests** in the same message, execute tasks **in sequence** (first request to completion, then continue to the next automatically), sending a short progress note when moving from one request to the next. |

Interpretation rules:
- Operator must be recognized when it appears at the **start** of the user message.
- `>>` can be recognized at the **end** of the message (continuation pending) or **between clauses/requests** (sequential execution chain).
- Multiple `>>` separators in the same message must be processed left-to-right as a sequential chain.
- If no operator is present, default behavior remains normal task execution flow.

---

## Ambiguity Handling (mandatory)

Agents must **never** decide by themselves when requirements are ambiguous or incomplete.

Required behavior:
1. Explicitly state that the task is ambiguous before asking questions.
2. Ask focused clarifying questions until all critical ambiguities are resolved.
3. Include an ambiguity counter in messages, e.g.:
  - `Ambiguities found: 2`
4. Update the counter as ambiguities are resolved.
5. Only proceed with execution after ambiguity count reaches zero or user explicitly chooses assumptions.

---