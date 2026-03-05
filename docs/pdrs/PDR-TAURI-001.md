# Tauri v2 — Guia Completo para Desenvolvimento Desktop

> **Contexto:** Referência técnica para construção de app desktop multiplataforma (Windows, Linux, macOS) com Tauri v2 + Svelte/SvelteKit + TypeScript + SQLite. Projeto: gestão de escala para time de mídia de igreja.

---

## 1. Visão Geral do Tauri v2

Tauri é um framework para construir binários pequenos e rápidos para desktop (e mobile) usando **tecnologias web no frontend** e **Rust no backend**. A versão 2.0 é estável, auditada por segurança e suporta Windows, Linux, macOS, Android e iOS.

### Por que Tauri em vez de Electron?

| Critério | Tauri v2 | Electron |
|---|---|---|
| Bundle mínimo | ~600 KB | ~50–200 MB |
| Motor WebView | WebView do SO (nativo) | Chromium bundled |
| Linguagem backend | Rust | Node.js |
| Segurança | Auditada; capabilities ACL | Permissões menos granulares |
| Memória | Significativamente menor | Maior consumo |
| WebViews por plataforma | Edge WebView2 (Win), WKWebView (macOS), webkitgtk (Linux) | Chromium em todas |

### Filosofia central

- **Secure by default**: capabilities system bloqueia tudo por padrão
- **Small by default**: usa WebView do sistema operacional
- **Flexible by default**: qualquer framework frontend (React, Svelte, Vue, Angular…)
- **Rust backend**: segurança de memória e performance sem GC

**Referência:** [Tauri 1.0 Blog Post](https://tauri.app/blog/tauri-1-0/) | [Audit Report v2](https://github.com/tauri-apps/tauri/blob/dev/audits/Radically_Open_Security-v2-report.pdf)

---

## 2. Arquitetura do Tauri v2

### Modelo de Processos Multi-processo

Tauri segue arquitetura multi-processo similar a navegadores modernos:

```
┌─────────────────────────────────────────┐
│           Core Process (Rust)           │
│  - Acesso total ao SO                   │
│  - Gerencia janelas, tray, notificações │
│  - Rota todas as IPC calls              │
│  - Gerencia estado global e DB          │
│  - Implementado com TAO + WRY           │
└───────────────┬─────────────────────────┘
                │  IPC (message passing)
┌───────────────▼─────────────────────────┐
│         WebView Process(es)             │
│  - Renderiza HTML/CSS/JS                │
│  - Acesso restrito via capabilities     │
│  - Seu frontend Svelte/React/Vue        │
└─────────────────────────────────────────┘
```

**Princípio do menor privilégio:** o WebView só acessa recursos que forem explicitamente autorizados nas capabilities.

### Crates Principais

| Crate | Responsabilidade |
|---|---|
| `tauri` | Crate central — runtime, macros, API |
| `tauri-runtime` | Camada de abstração entre Tauri e WebView |
| `tauri-build` | Macros em compile-time, injeta features no cargo |
| `tauri-macros` | `#[tauri::command]`, `generate_handler!`, etc. |
| `tauri-utils` | Parsing de config, detecção de plataforma, CSP |
| `tauri-bundler` | Empacotamento para distribuição (MSI, AppImage, DMG…) |
| `tauri-codegen` | Embed/compress assets, parse `tauri.conf.json` |
| `tauri-runtime-wry` | Interações de baixo nível com WRY |
| `@tauri-apps/api` | TypeScript — bindings para o frontend |

### Bibliotecas de baixo nível mantidas pelo Tauri

- **[TAO](https://github.com/tauri-apps/tao)** — Gerenciamento de janelas cross-platform (fork de winit, com menu e system tray)
- **[WRY](https://github.com/tauri-apps/wry)** — WebView rendering cross-platform (decide qual WebView usar em cada SO)

### Estrutura de Projeto

```
meu-app/
├── src/                   # Frontend (Svelte/TypeScript)
├── src-tauri/
│   ├── src/
│   │   ├── lib.rs         # Ponto de entrada Rust, commands
│   │   └── commands.rs    # Comandos organizados
│   ├── capabilities/
│   │   └── main.json      # Permissões/capabilities
│   ├── icons/             # Ícones da aplicação
│   ├── Cargo.toml
│   └── tauri.conf.json    # Configuração central
├── package.json
└── vite.config.ts
```

---

## 3. IPC — Comunicação Inter-Processo (Commands & Events)

### 3.1 Commands: Frontend → Rust

Commands são o mecanismo principal de IPC. São funções Rust expostas ao frontend via JSON-RPC.

**Rust (`src-tauri/src/lib.rs`):**
```rust
use tauri::State;
use std::sync::Mutex;

// Comando simples
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Olá, {}!", name)
}

// Comando com estado gerenciado
#[tauri::command]
fn get_members(state: State<'_, Mutex<AppState>>) -> Vec<Member> {
    let state = state.lock().unwrap();
    state.members.clone()
}

// Comando async com Result (retorna erro para o frontend)
#[tauri::command]
async fn create_member(name: String, role: String) -> Result<Member, String> {
    // lógica de criação...
    Ok(Member { id: 1, name, role })
}

// Registrar commands
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            greet,
            get_members,
            create_member,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**Frontend TypeScript (Svelte):**
```typescript
import { invoke } from '@tauri-apps/api/core';

// Invocação simples
const greeting = await invoke<string>('greet', { name: 'Samuel' });

// Com tratamento de erro
try {
  const member = await invoke<Member>('create_member', {
    name: 'João',
    role: 'Câmera',
  });
  console.log('Membro criado:', member);
} catch (error) {
  console.error('Erro:', error);
}
```

> **Importante:** nomes de parâmetros em Rust usam `snake_case`; no JS devem ser passados em `camelCase`. Ex: `invoke_message` no Rust → `{ invokeMessage: '...' }` no JS.

### 3.2 Tratamento de Erros Idiomático

```rust
// Usar thiserror para erros tipados e serializáveis
#[derive(Debug, thiserror::Error)]
enum AppError {
    #[error("Membro não encontrado: {0}")]
    MemberNotFound(i64),
    #[error(transparent)]
    Database(#[from] sqlx::Error),
}

// Implementar Serialize manualmente (obrigatório)
impl serde::Serialize for AppError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where S: serde::ser::Serializer {
        serializer.serialize_str(self.to_string().as_ref())
    }
}

#[tauri::command]
async fn get_member(id: i64) -> Result<Member, AppError> {
    find_by_id(id).ok_or(AppError::MemberNotFound(id))
}
```

### 3.3 Events: Sistema Bidirecional

Events são fire-and-forget, ideais para notificações de estado, progresso, etc.

**Emitir do Rust para o frontend:**
```rust
use tauri::{AppHandle, Emitter};
use serde::Serialize;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct ScheduleGenerated {
    event_id: i64,
    members_count: usize,
}

#[tauri::command]
async fn generate_schedule(app: AppHandle, event_id: i64) {
    // ... lógica de geração
    app.emit("schedule-generated", ScheduleGenerated {
        event_id,
        members_count: 5,
    }).unwrap();
}
```

**Escutar no frontend (Svelte):**
```typescript
import { listen } from '@tauri-apps/api/event';
import { onDestroy } from 'svelte';

let unlisten: (() => void) | undefined;

onMount(async () => {
  unlisten = await listen<{ eventId: number; membersCount: number }>(
    'schedule-generated',
    (event) => {
      console.log('Escala gerada:', event.payload);
    }
  );
});

onDestroy(() => unlisten?.());
```

### 3.4 Channels (Streaming de Alta Performance)

Para operações com grande volume de dados (ex: log em tempo real, progresso de export):
```rust
use tauri::ipc::Channel;

#[tauri::command]
async fn export_data(on_progress: Channel<u8>) {
    for percent in [10u8, 25, 50, 75, 100] {
        on_progress.send(percent).unwrap();
        tokio::time::sleep(std::time::Duration::from_millis(100)).await;
    }
}
```

---

## 4. Plugin SQL (tauri-plugin-sql + SQLite)

O plugin SQL é essencial para o projeto de escala — fornece acesso a SQLite, MySQL e PostgreSQL diretamente do frontend via Rust/sqlx.

### 4.1 Instalação

```bash
npm run tauri add sql
# No diretório src-tauri:
cargo add tauri-plugin-sql --features sqlite
```

### 4.2 Configuração com Migrations (`src-tauri/src/lib.rs`)

```rust
use tauri_plugin_sql::{Builder as SqlBuilder, Migration, MigrationKind};

pub fn run() {
    let migrations = vec![
        Migration {
            version: 1,
            description: "create_members_table",
            sql: "
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
            ",
            kind: MigrationKind::Up,
        },
        Migration {
            version: 2,
            description: "create_squads_table",
            sql: "
                CREATE TABLE IF NOT EXISTS squads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS member_squads (
                    member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
                    squad_id INTEGER REFERENCES squads(id) ON DELETE CASCADE,
                    PRIMARY KEY (member_id, squad_id)
                );
            ",
            kind: MigrationKind::Up,
        },
        Migration {
            version: 3,
            description: "create_events_and_schedule",
            sql: "
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT
                );
                CREATE TABLE IF NOT EXISTS schedule_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                    member_id INTEGER REFERENCES members(id),
                    squad_id INTEGER REFERENCES squads(id),
                    role TEXT
                );
            ",
            kind: MigrationKind::Up,
        },
    ];

    tauri::Builder::default()
        .plugin(
            SqlBuilder::default()
                .add_migrations("sqlite:escala.db", migrations)
                .build(),
        )
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**`tauri.conf.json` — preload do banco:**
```json
{
  "plugins": {
    "sql": {
      "preload": ["sqlite:escala.db"]
    }
  }
}
```

### 4.3 Uso no Frontend (Svelte/TypeScript)

```typescript
import Database from '@tauri-apps/plugin-sql';

// Carregar/conectar ao banco
const db = await Database.load('sqlite:escala.db');

// INSERT com parâmetros posicionais ($1, $2...)
const result = await db.execute(
  'INSERT INTO members (name, role, phone) VALUES ($1, $2, $3)',
  ['Maria Silva', 'Câmera', '11999990000']
);
console.log('rowsAffected:', result.rowsAffected);
console.log('lastInsertId:', result.lastInsertId);

// SELECT
const members = await db.select<Member[]>(
  'SELECT * FROM members WHERE active = $1 ORDER BY name',
  [1]
);

// UPDATE
await db.execute(
  'UPDATE members SET name = $1 WHERE id = $2',
  ['Maria Santos', 1]
);

// DELETE
await db.execute('DELETE FROM members WHERE id = $1', [1]);
```

### 4.4 Permissões necessárias (`capabilities/main.json`)

```json
{
  "permissions": [
    "sql:default",
    "sql:allow-execute"
  ]
}
```

> **Nota de segurança:** `sql:default` habilita apenas leitura (select, load, close). Para escrita (INSERT/UPDATE/DELETE), adicione explicitamente `sql:allow-execute`.

---

## 5. Sistema de Capabilities e Segurança

### 5.1 Modelo de Confiança (Trust Boundary)

```
┌──────────────────────────────────────────────┐
│  Core Rust (confiança total — acesso ao SO)  │
│  plugins, comandos customizados              │
└────────────────────┬─────────────────────────┘
                     │ IPC  (fronteira controlada)
┌────────────────────▼─────────────────────────┐
│  WebView (confiança limitada)                │
│  Acesso apenas ao que capabilities permitem  │
└──────────────────────────────────────────────┘
```

### 5.2 Estrutura de Capabilities

**`src-tauri/capabilities/main.json`:**
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Permissões para a janela principal",
  "windows": ["main"],
  "permissions": [
    "core:path:default",
    "core:event:default",
    "core:window:default",
    "core:app:default",
    "core:resources:default",
    "core:menu:default",
    "core:tray:default",
    "sql:default",
    "sql:allow-execute",
    "store:default"
  ]
}
```

**Capabilities por plataforma:**
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "desktop-only",
  "windows": ["main"],
  "platforms": ["linux", "macOS", "windows"],
  "permissions": [
    "global-shortcut:allow-register",
    "fs:default"
  ]
}
```

### 5.3 Referenciar capabilities no `tauri.conf.json`

```json
{
  "app": {
    "security": {
      "capabilities": ["main-capability", "desktop-only"]
    }
  }
}
```

### 5.4 O que o sistema de capabilities protege

✅ Minimiza impacto de comprometimento do frontend  
✅ Previne exposição acidental de dados do sistema  
✅ Previne escalação de privilégios frontend→backend  

❌ **Não protege contra:** código Rust malicioso; configuração excessivamente permissiva; 0-days no WebView do SO; supply chain attacks

### 5.5 CSP (Content Security Policy)

Tauri injeta automaticamente CSP no WebView. Para customizar:

```json
{
  "app": {
    "security": {
      "csp": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    }
  }
}
```

> Para desenvolvimento, pode ser necessário relaxar o CSP. **Nunca use `unsafe-eval` em produção.**

### 5.6 WebView e Segurança de Patches

Tauri usa o WebView do sistema operacional (não bundled), o que significa que patches de segurança chegam muito mais rápido ao usuário final — via Windows Update, macOS Update ou gerenciador de pacotes Linux — do que se o WebView estivesse bundled no app.

---

## 6. Integração com Svelte / SvelteKit + TypeScript

### 6.1 Setup com SvelteKit (recomendado)

**Criar projeto:**
```bash
npm create tauri-app@latest meu-app -- --template svelte-ts
cd meu-app
npm install
```

**Ou adicionar Tauri a SvelteKit existente:**
```bash
npm install --save-dev @sveltejs/adapter-static
npm run tauri init
```

**`svelte.config.js`:**
```javascript
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      fallback: 'index.html', // SPA mode
    }),
  },
};

export default config;
```

**`src/routes/+layout.ts`** — desabilitar SSR:
```typescript
export const ssr = false;
```

**`src-tauri/tauri.conf.json`:**
```json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../build"
  }
}
```

**`vite.config.ts`** — compatível com Tauri mobile dev:
```typescript
import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';

const host = process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [sveltekit()],
  clearScreen: false,
  server: {
    host: host || false,
    port: 5173,
    strictPort: true,
    hmr: host ? { protocol: 'ws', host, port: 5174 } : undefined,
  },
});
```

### 6.2 Componente Svelte com invoke

```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { listen } from '@tauri-apps/api/event';
  import { onMount, onDestroy } from 'svelte';

  interface Member {
    id: number;
    name: string;
    role: string;
    active: boolean;
  }

  let members: Member[] = [];
  let loading = false;
  let error = '';

  async function loadMembers() {
    loading = true;
    try {
      members = await invoke<Member[]>('list_members');
    } catch (e) {
      error = String(e);
    } finally {
      loading = false;
    }
  }

  async function deleteMember(id: number) {
    await invoke('delete_member', { id });
    await loadMembers();
  }

  onMount(loadMembers);
</script>

{#if loading}
  <p>Carregando...</p>
{:else if error}
  <p class="error">{error}</p>
{:else}
  <ul>
    {#each members as member (member.id)}
      <li>
        {member.name} — {member.role}
        <button on:click={() => deleteMember(member.id)}>Remover</button>
      </li>
    {/each}
  </ul>
{/if}
```

### 6.3 Store Svelte + Tauri

```typescript
// stores/members.ts
import { writable } from 'svelte/store';
import { invoke } from '@tauri-apps/api/core';

export const members = writable<Member[]>([]);

export async function refreshMembers() {
  const data = await invoke<Member[]>('list_members');
  members.set(data);
}
```

---

## 7. Gerenciamento de Estado no Rust

```rust
use std::sync::Mutex;
use tauri::{Builder, Manager, State};

// Estado da aplicação
#[derive(Default)]
struct AppState {
    db_path: String,
}

// Registrar
Builder::default()
    .setup(|app| {
        app.manage(Mutex::new(AppState::default()));
        Ok(())
    })

// Acessar em commands
#[tauri::command]
fn update_setting(
    state: State<'_, Mutex<AppState>>,
    key: String,
    value: String,
) {
    let mut s = state.lock().unwrap();
    // usar s...
}
```

---

## 8. Plugin Store (configurações persistentes)

Para configurações simples da app (sem SQL):

```bash
npm run tauri add store
```

```typescript
import { load } from '@tauri-apps/plugin-store';

const store = await load('settings.json', { autoSave: true });

// Salvar configuração
await store.set('theme', 'dark');
await store.set('church-name', 'Igreja Exemplo');

// Ler configuração
const theme = await store.get<string>('theme');
const churchName = await store.get<string>('church-name');
```

**Capabilities:**
```json
{ "permissions": ["store:default"] }
```

---

## 9. Auto-Updater

### 9.1 Configuração

```bash
npm run tauri add updater
# Gerar par de chaves
npm run tauri signer generate -- -w ~/.tauri/escala.key
```

**`tauri.conf.json`:**
```json
{
  "bundle": {
    "createUpdaterArtifacts": true
  },
  "plugins": {
    "updater": {
      "pubkey": "CONTEÚDO_DA_CHAVE_PUBLICA",
      "endpoints": [
        "https://releases.meu-app.com/{{target}}/{{arch}}/{{current_version}}"
      ]
    }
  }
}
```

### 9.2 JSON estático para GitHub Releases

```json
{
  "version": "1.2.0",
  "notes": "Correções e melhorias na geração de escala",
  "pub_date": "2024-01-15T10:00:00Z",
  "platforms": {
    "linux-x86_64": {
      "signature": "CONTEÚDO DO .sig",
      "url": "https://github.com/user/repo/releases/download/v1.2.0/app_1.2.0_amd64.AppImage"
    },
    "windows-x86_64": {
      "signature": "CONTEÚDO DO .sig",
      "url": "https://github.com/user/repo/releases/download/v1.2.0/app_1.2.0_x64-setup.exe"
    },
    "darwin-x86_64": {
      "signature": "CONTEÚDO DO .sig",
      "url": "https://github.com/user/repo/releases/download/v1.2.0/app_1.2.0_x64.dmg"
    },
    "darwin-aarch64": {
      "signature": "CONTEÚDO DO .sig",
      "url": "https://github.com/user/repo/releases/download/v1.2.0/app_1.2.0_aarch64.dmg"
    }
  }
}
```

### 9.3 Verificar updates no frontend

```typescript
import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

async function checkUpdate() {
  const update = await check();
  if (update?.available) {
    console.log(`Nova versão: ${update.version}`);
    await update.downloadAndInstall();
    await relaunch();
  }
}
```

> ⚠️ A chave privada **NUNCA deve ser commitada**. Use variáveis de ambiente no CI: `TAURI_SIGNING_PRIVATE_KEY`.

---

## 10. Build e Distribuição Multiplataforma

### 10.1 Build local

```bash
npm run tauri build
```

Gera automaticamente os bundles para a plataforma atual:
- **Windows:** `.msi` (NSIS) e `.exe`
- **Linux:** `.deb`, `.AppImage`, `.rpm`
- **macOS:** `.dmg`, `.app`

### 10.2 Configurar versão

**`src-tauri/tauri.conf.json`:**
```json
{
  "version": "1.0.0",
  "bundle": {
    "identifier": "br.com.suaigreja.escala",
    "productName": "Escala Mídia",
    "createUpdaterArtifacts": true
  }
}
```

### 10.3 GitHub Actions — CI/CD Multiplataforma

```yaml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    strategy:
      fail-fast: false
      matrix:
        platform: [ubuntu-22.04, windows-latest, macos-latest]
    runs-on: ${{ matrix.platform }}

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies (Ubuntu)
        if: matrix.platform == 'ubuntu-22.04'
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libappindicator3-dev \
            librsvg2-dev patchelf

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install frontend dependencies
        run: npm ci

      - name: Build and release
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
        with:
          tagName: v__VERSION__
          releaseName: 'Escala Mídia v__VERSION__'
          releaseBody: 'Veja os assets para baixar esta versão.'
          releaseDraft: true
```

### 10.4 Otimização de tamanho (`src-tauri/Cargo.toml`)

```toml
[profile.release]
codegen-units = 1
lto = true
opt-level = "s"
panic = "abort"
strip = true
```

### 10.5 Remover commands não utilizados

```json
{
  "build": {
    "removeUnusedCommands": true
  }
}
```

---

## 11. Testing no Tauri

### 11.1 Testes Unitários Rust (mock runtime)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_schedule_generation() {
        let members = vec![
            Member { id: 1, name: "João".into(), role: "Camera".into() },
            Member { id: 2, name: "Maria".into(), role: "Audio".into() },
        ];
        let schedule = generate_schedule_logic(&members, &[]);
        assert!(!schedule.is_empty());
    }
}
```

### 11.2 Mock de IPC no Frontend (Vitest)

```typescript
// tests/members.test.ts
import { beforeAll, expect, test, vi } from 'vitest';
import { randomFillSync } from 'crypto';
import { mockIPC } from '@tauri-apps/api/mocks';
import { invoke } from '@tauri-apps/api/core';

beforeAll(() => {
  // jsdom não tem WebCrypto
  Object.defineProperty(window, 'crypto', {
    value: { getRandomValues: (buf: any) => randomFillSync(buf) },
  });
});

test('lista membros', async () => {
  mockIPC((cmd, args) => {
    if (cmd === 'list_members') {
      return [{ id: 1, name: 'João', role: 'Camera', active: true }];
    }
  });

  const spy = vi.spyOn(window.__TAURI_INTERNALS__, 'invoke');
  const members = await invoke('list_members');

  expect(spy).toHaveBeenCalled();
  expect(members).toHaveLength(1);
  expect(members[0].name).toBe('João');
});
```

### 11.3 Mock de Windows

```typescript
import { mockWindows } from '@tauri-apps/api/mocks';

test('múltiplas janelas', async () => {
  mockWindows('main', 'settings', 'about');
  const { getAll } = await import('@tauri-apps/api/webviewWindow');
  expect(getAll().map(w => w.label)).toEqual(['main', 'settings', 'about']);
});
```

### 11.4 End-to-End com WebDriver

Tauri suporta protocolo WebDriver para E2E em desktop. Ferramentas compatíveis: WebdriverIO, Selenium. macOS não suporta cliente WebDriver desktop por limitações do SO.

---

## 12. Plugins Oficiais Relevantes

| Plugin | Uso | Plataformas |
|---|---|---|
| `tauri-plugin-sql` | SQLite/MySQL/PostgreSQL | Win/Lin/Mac/Android/iOS |
| `tauri-plugin-store` | Config key-value persistente | Todas |
| `tauri-plugin-updater` | Auto-update in-app | Win/Lin/Mac |
| `tauri-plugin-fs` | Filesystem access | Todas |
| `tauri-plugin-dialog` | Open/Save dialogs | Todas |
| `tauri-plugin-shell` | Shell/processos externos | Desktop |
| `tauri-plugin-os` | Info do SO | Todas |
| `tauri-plugin-process` | Acesso ao processo atual | Todas |
| `tauri-plugin-log` | Logging configurável | Todas |
| `tauri-plugin-single-instance` | Uma instância por vez | Desktop |
| `tauri-plugin-deep-linking` | URL handlers | Win/Mac |
| `tauri-plugin-notification` | Notificações nativas | Todas |
| `tauri-plugin-http` | HTTP client em Rust | Todas |

---

## 13. Problemas Comuns e Soluções

### 13.1 WebView diferente por plataforma

**Problema:** Comportamento de CSS/JS inconsistente entre Windows (Edge WebView2), macOS (WKWebView) e Linux (webkitgtk).

**Solução:**
- Testar em todas as plataformas no CI
- Usar `@tauri-apps/api/os` para detectar SO e ajustar comportamento
- Evitar features CSS muito novas; checar [Can I use](https://caniuse.com) para webkitgtk

### 13.2 `invoke` retorna undefined/null

**Problema:** Command Rust retorna `()` (unit type) → JS recebe `null`.

**Solução:** Retorne um tipo explícito ou trate `null` no frontend.

### 13.3 Erro de capability não configurada

**Problema:** `Command X not allowed` mesmo com o command registrado.

**Solução:** Verificar se o command está nas capabilities do arquivo JSON correto e se a capability está referenciada no `tauri.conf.json`.

### 13.4 CSP bloqueando recursos externos

**Problema:** Fontes, imagens ou scripts externos bloqueados pelo CSP padrão.

**Solução:**
```json
{
  "app": {
    "security": {
      "csp": "default-src 'self'; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com"
    }
  }
}
```

### 13.5 Primeira build muito lenta

**Problema:** `cargo` baixa e compila todas as dependências Rust (~10–20 min na primeira vez).

**Solução:** Builds subsequentes são muito mais rápidas pois o cache do Cargo persiste. Em CI, usar `actions/cache` para o diretório `~/.cargo`.

### 13.6 `tauri dev` não recarrega após mudança Rust

**Problema:** Hot-reload funciona para o frontend, mas o processo Rust precisa recompilar e reiniciar.

**Solução:** Normal e esperado. Para otimizar, use builds incrementais no `Cargo.toml`:
```toml
[profile.dev]
incremental = true
```

### 13.7 `sqlite:escala.db` — caminho do banco

**Problema:** Onde fica o arquivo `.db` em produção?

**Solução:** Por padrão, o plugin SQL resolve o caminho relativo ao `BaseDirectory::AppConfig` do sistema:
- Windows: `%APPDATA%\com.suaigreja.escala\`
- Linux: `~/.config/com.suaigreja.escala/`
- macOS: `~/Library/Application Support/com.suaigreja.escala/`

### 13.8 Linux — webkitgtk não instalado

**Problema:** Build falha no Linux com erro de dependência.

**Solução:**
```bash
sudo apt-get install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev
```

### 13.9 `ssr = false` obrigatório com SvelteKit

**Problema:** APIs do Tauri (`invoke`, `listen`) não estão disponíveis durante SSR/prerendering.

**Solução:** Adicionar `export const ssr = false` no `+layout.ts` root ou usar o adaptador estático em modo SPA.

### 13.10 Tauri IPC — tipos não-serializáveis

**Problema:** Tipos Rust que não implementam `serde::Serialize` causam erro em tempo de compilação.

**Solução:** Derivar `#[derive(Serialize, Deserialize)]` em todos os tipos retornados/recebidos por commands, ou usar `map_err(|e| e.to_string())` para simplificar.

---

## 14. Configuração Completa do `tauri.conf.json` (Exemplo)

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "Escala Mídia",
  "version": "1.0.0",
  "identifier": "br.com.suaigreja.escala",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../build",
    "removeUnusedCommands": true
  },
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "Escala Mídia",
        "width": 1200,
        "height": 800,
        "minWidth": 900,
        "minHeight": 600,
        "resizable": true,
        "decorations": true
      }
    ],
    "security": {
      "capabilities": ["main-capability"]
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/icon.icns", "icons/icon.ico"],
    "createUpdaterArtifacts": true
  },
  "plugins": {
    "sql": {
      "preload": ["sqlite:escala.db"]
    },
    "updater": {
      "pubkey": "SUA_CHAVE_PUBLICA_AQUI",
      "endpoints": [
        "https://github.com/user/escala/releases/latest/download/latest.json"
      ]
    }
  }
}
```

---

## 15. Padrão de Arquitetura para o Projeto Escala

```
src-tauri/src/
├── lib.rs                  # Builder + registro de commands + plugins
├── commands/
│   ├── mod.rs
│   ├── members.rs          # CRUD de membros
│   ├── squads.rs           # CRUD de squads
│   ├── events.rs           # CRUD de eventos
│   └── schedule.rs         # Geração automática de escala
└── models/
    ├── mod.rs
    ├── member.rs           # #[derive(Serialize, Deserialize, Clone)]
    ├── squad.rs
    └── event.rs

src/ (Svelte frontend)
├── routes/
│   ├── +layout.ts          # ssr = false
│   ├── +layout.svelte      # Shell com sidebar
│   ├── members/
│   ├── squads/
│   ├── events/
│   └── schedule/
├── lib/
│   ├── db.ts               # Database instance singleton
│   ├── stores/             # Svelte stores
│   └── types.ts            # Interfaces TypeScript
```

---

## 16. Desenvolvimento Local — Comandos Essenciais

```bash
# Instalar dependências e scaffoldar
npm create tauri-app@latest escala -- --template svelte-ts

# Desenvolvimento com hot-reload
npm run tauri dev

# Build para produção
npm run tauri build

# Adicionar plugin
npm run tauri add sql
npm run tauri add store
npm run tauri add updater

# Gerar chaves de assinatura
npm run tauri signer generate -- -w ~/.tauri/escala.key

# Build sem bundle (só o binário)
npm run tauri build -- --no-bundle

# Build bundle específico
npm run tauri bundle -- --bundles deb,appimage
```

---

## 17. Referências e Links

| Recurso | URL |
|---|---|
| Documentação oficial v2 | https://v2.tauri.app |
| Guia de início | https://v2.tauri.app/start/ |
| Arquitetura | https://v2.tauri.app/concept/architecture/ |
| IPC / Commands | https://v2.tauri.app/develop/calling-rust/ |
| Events / Frontend←Rust | https://v2.tauri.app/develop/calling-frontend/ |
| Capabilities & Segurança | https://v2.tauri.app/security/capabilities/ |
| Plugin SQL | https://v2.tauri.app/plugin/sql/ |
| Plugin Store | https://v2.tauri.app/plugin/store/ |
| Plugin Updater | https://v2.tauri.app/plugin/updater/ |
| Todos os plugins | https://v2.tauri.app/plugin/ |
| SvelteKit integration | https://v2.tauri.app/start/frontend/sveltekit/ |
| Estado (State Management) | https://v2.tauri.app/develop/state-management/ |
| Testing / Mocking | https://v2.tauri.app/develop/tests/mocking/ |
| Distribuição | https://v2.tauri.app/distribute/ |
| App Size Optimization | https://v2.tauri.app/concept/size/ |
| Modelo de processos | https://v2.tauri.app/concept/process-model/ |
| Tauri GitHub | https://github.com/tauri-apps/tauri |
| plugins-workspace | https://github.com/tauri-apps/plugins-workspace |
| tauri-action (GitHub Actions) | https://github.com/tauri-apps/tauri-action |
| awesome-tauri | https://github.com/tauri-apps/awesome-tauri |
| Audit report v2 | https://github.com/tauri-apps/tauri/blob/dev/audits/Radically_Open_Security-v2-report.pdf |
| TauRPC (tipagem IPC avançada) | https://github.com/MatsDK/TauRPC |
| create-tauri-app | https://github.com/tauri-apps/create-tauri-app |

---

*Documento compilado a partir da documentação oficial Tauri v2 (v2.tauri.app), março 2025. Todas as APIs referenciadas são estáveis no Tauri 2.x.*