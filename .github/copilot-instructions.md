# Copilot Instructions

## Build & Run

```bash
# Activate venv first
source .venv/bin/activate

# Run the app
python app.py

# Dev mode with auto-reload on file change
python watcher.py

# Run all working tests
pytest tests/

# Run tests for a specific layer
pytest tests/helpers/
pytest tests/services/
pytest tests/integration/

# Run a single test file
pytest tests/helpers/test_escala_generator.py

# Run a single test by name
pytest tests/helpers/test_escala_generator.py::TestIsValidMonth::test_valid_month_january

# Run E2E tests (requires X display — on Wayland, unset WAYLAND_DISPLAY first)
env -u WAYLAND_DISPLAY pytest tests/e2e/
```

> **Note:** Some tests in `tests/` have known import errors (e.g., `test_squads_service.py`, `test_popup_centering.py`). These are pre-existing failures unrelated to your change.

---

## Architecture Overview

This is a Python/Tkinter desktop app for managing church media team schedules ("escala"). Three distinct layers:

```
app.py                  ← Entry point: wires Tk root, creates frames, calls sincronizar()
gui/                    ← Tkinter frames (one per screen)
  main_window.py        ← App shell: sidebar, register_frame(), sincronizar()
  membros.py            ← Individual screen frames
  gerar_escala.py
  ...
services/               ← Business logic, orchestrates helpers + DB
  membros_service.py
  escala_service.py
  ...
helpers/                ← Pure functions (no DB, no side-effects, 100% testable)
  escala_generator.py
  membros.py
  ...
infra/
  database.py           ← SQLAlchemy models, engine, session_scope(), create_tables()
tests/
  helpers/              ← Unit tests for pure helper functions
  services/             ← Tests for service layer
  integration/          ← Tests that hit the real ORM (use test DB)
conftest.py             ← Shared fixtures: test_db (in-memory SQLite), members_fixture
```

### Key runtime contracts

- **`register_frame(name, frame)`** in `app.py` adds a frame to the sidebar. Navigation uses `tkraise()`.
- **`sincronizar()`** on `SistemaEscalaApp` calls `atualizar_lista()` on every registered frame that implements it. All frames that display live data must implement `atualizar_lista()`.
- **`session_scope()`** in `infra/database.py` is the only way to access the DB in services. It commits on success and rolls back on exception.
- Database URL resolution order: `DATABASE_URL` env var → `.ENV`/`.env` file → `sqlite:///escala.db`.

---

## Key Conventions

### Layering rule
- **`helpers/`** = pure functions only. No DB access, no logging, no side effects. These are the unit-testable core.
- **`services/`** = orchestration: call helpers for logic, call `session_scope()` for persistence.
- **`gui/`** = Tkinter frames only. They instantiate services, never call helpers or DB directly.

### GUI file structure
All screen frames follow `_build_*` / `_on_*` private method naming, e.g.:
```python
def _build_ui(self) -> None: ...
def _on_save(self) -> None: ...
```

### Dual DB-access patterns (legacy coexistence)
Some GUI files (`gui/squads.py`, old `gui/eventos.py`) use raw `db.conectar()` SQLite calls while newer ones use SQLAlchemy via `services/`. **Preserve the pattern already in the file you're editing.** Do not migrate unless that's the task.

### Naming convention
- UI labels and domain strings are **PT-BR**: `Membros`, `Escala`, `Times`, `Patente`
- ORM models and service methods are **English**: `Member`, `Squad`, `Event`, `MemberSquad`

### ORM models (infra/database.py)
All PKs are UUID strings (`gen_uuid()`). All FK relationships define `cascade="all, delete-orphan"`. The SQLite engine always sets `PRAGMA foreign_keys = ON`.

Key models: `Member`, `Squad`, `Event`, `MemberSquad` (M:N), `EventSquad` (M:N with level/quantity), `FamilyCouple`, `MemberRestrictions`.

### Test fixtures
`conftest.py` provides:
- `test_db` — in-memory SQLite engine, patches `infra.database.SessionLocal` for the test duration
- `members_fixture` — inserts 6 test members (Alice, Bob, Charlie, Dave, Eve, Frank) and returns `{name: id}` dict

### Do not commit
`.db` files, `backup_*.db`, `escala_debug.log`, `.ENV` contents.
