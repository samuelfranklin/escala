# Rust para Backend Tauri v2 — Guia Completo para Devs Python

> **Contexto:** App desktop Tauri v2 para gestão de escala de mídia. Backend em Rust + SQLite. Time com background principal em Python.

---

## Sumário

1. [Por que Rust no Backend Tauri?](#por-que-rust)
2. [Ownership, Borrowing e Lifetimes](#ownership)
3. [Tipos, Structs e Enums](#tipos)
4. [Tratamento de Erros com `thiserror`](#erros)
5. [Serde: Serialização JSON](#serde)
6. [Async Rust com Tokio](#async)
7. [SQLx: Setup, Pool, Migrations e Queries](#sqlx)
8. [Estrutura do Projeto Tauri](#estrutura)
9. [Commands Tauri](#commands)
10. [Testes em Rust](#testes)
11. [Tabela Python → Rust](#python-rust)
12. [Padrões Recomendados](#padroes)
13. [Referências](#referencias)

---

## 1. Por que Rust no Backend Tauri? {#por-que-rust}

Tauri v2 usa Rust como runtime do processo nativo da aplicação desktop. Todo o acesso ao sistema operacional, ao banco de dados, ao sistema de arquivos e às funcionalidades nativas passa pelo código Rust. O frontend (HTML/JS/TS) se comunica com o backend Rust via **IPC (Inter-Process Communication)** usando o sistema de `commands`.

**Vantagens para este projeto:**
- **Segurança de memória sem GC** — sem vazamentos acidentais, sem crashes por null pointer
- **Performance** — operações de banco de dados e geração de escala sem overhead de interpretador
- **SQLx com compile-time checks** — queries SQL validadas em tempo de compilação
- **Integração nativa com Tauri** — o framework foi projetado em torno do Rust

---

## 2. Ownership, Borrowing e Lifetimes {#ownership}

Este é o conceito mais diferente para devs Python. Em Python, o Garbage Collector gerencia memória automaticamente. Em Rust, o compilador garante segurança de memória em **tempo de compilação** através de três regras:

### 2.1 Regras de Ownership

```
1. Cada valor tem exatamente UM dono (owner)
2. Só pode haver um dono por vez
3. Quando o dono sai de escopo, o valor é destruído (drop)
```

**Comparação Python → Rust:**

```python
# Python: garbage collector cuida da memória
nome = "João"
outro = nome  # ambos apontam para o mesmo objeto
print(nome)   # funciona normalmente
```

```rust
// Rust: String é movida (moved), não copiada
let nome = String::from("João");
let outro = nome;  // 'nome' foi MOVIDO para 'outro'
// println!("{}", nome); // ERRO DE COMPILAÇÃO: 'nome' foi movido
println!("{}", outro); // OK
```

**Tipos primitivos são copiados automaticamente** (`i32`, `f64`, `bool`, `char`):

```rust
let x = 5;
let y = x; // cópia, não move
println!("{} {}", x, y); // ambos válidos — i32 implementa Copy
```

### 2.2 Borrowing (Referências)

Para usar um valor sem transferir ownership, usa-se **referências**:

```rust
fn calcular_tamanho(s: &String) -> usize {  // & = referência (borrow)
    s.len()
} // s sai de escopo mas NÃO dropa o valor (ela só emprestava)

fn main() {
    let s = String::from("escala");
    let tamanho = calcular_tamanho(&s); // passa referência
    println!("'{}' tem {} letras", s, tamanho); // s ainda válido
}
```

**Referências mutáveis:**

```rust
fn adicionar_servico(s: &mut String) {
    s.push_str(" - Mídia");
}

let mut nome = String::from("Squad A");
adicionar_servico(&mut nome);
// Regra: só UMA referência mutável por vez no mesmo escopo
```

**Por que essa regra?** Previne **data races** — dois ponteiros tentando modificar o mesmo dado simultaneamente, problema comum em código Python com threads.

### 2.3 Lifetimes

Lifetimes garantem que referências não sobrevivam ao dado que referenciam. Na maioria dos casos o compilador infere automaticamente (lifetime elision). Você raramente precisará anotá-las explicitamente no código Tauri/backend:

```rust
// Compilador infere o lifetime aqui automaticamente
fn primeiro_nome(nome_completo: &str) -> &str {
    nome_completo.split(' ').next().unwrap()
}
```

Quando necessário explicitamente (raro no código de aplicação):
```rust
fn mais_longo<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

---

## 3. Tipos, Structs e Enums {#tipos}

### 3.1 Structs — O "dataclass" do Rust

```python
# Python com dataclass
from dataclasses import dataclass
from typing import Optional

@dataclass
class Member:
    id: int
    name: str
    phone: Optional[str] = None
    active: bool = True
```

```rust
// Rust equivalente
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Member {
    pub id: i64,
    pub name: String,
    pub phone: Option<String>,  // Option<T> = None | Some(T)
    pub active: bool,
}

// Para criação (sem id ainda)
#[derive(Debug, Deserialize)]
pub struct CreateMemberRequest {
    pub name: String,
    pub phone: Option<String>,
}
```

### 3.2 Enums — Muito mais poderosos que em Python

```rust
// Enum simples para status
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT", rename_all = "snake_case")]
pub enum MemberStatus {
    Active,
    Inactive,
    OnLeave,
}

// Enum com dados associados (tipo sum type / union)
#[derive(Debug)]
pub enum ScheduleEntry {
    Assigned { member_id: i64, role: String },
    Vacant { role: String },
    Holiday { reason: String },
}
```

### 3.3 Domínio Completo do Projeto

```rust
// src-tauri/src/models.rs

use serde::{Deserialize, Serialize};
use sqlx::FromRow;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Member {
    pub id: i64,
    pub name: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub instagram: Option<String>,
    pub active: bool,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Squad {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Event {
    pub id: i64,
    pub name: String,
    pub date: String,
    pub squad_id: Option<i64>,
    pub notes: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct SquadMember {
    pub squad_id: i64,
    pub member_id: i64,
    pub role: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Schedule {
    pub id: i64,
    pub event_id: i64,
    pub member_id: i64,
    pub role: String,
}

// DTOs para criação/atualização
#[derive(Debug, Deserialize)]
pub struct CreateMemberRequest {
    pub name: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub instagram: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateMemberRequest {
    pub name: Option<String>,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub instagram: Option<String>,
    pub active: Option<bool>,
}
```

---

## 4. Tratamento de Erros com `thiserror` {#erros}

Python usa exceções (`try/except`). Rust usa **tipos de retorno** — erros são valores, não exceções:

```python
# Python
def buscar_membro(id: int) -> Member:
    try:
        return db.query(id)
    except Exception as e:
        raise ValueError(f"Membro não encontrado: {e}")
```

```rust
// Rust: o erro É o retorno, não uma exceção
async fn buscar_membro(pool: &SqlitePool, id: i64) -> Result<Member, AppError> {
    let member = sqlx::query_as!(Member, "SELECT * FROM members WHERE id = ?", id)
        .fetch_one(pool)
        .await?;  // ? propaga o erro se houver
    Ok(member)
}
```

### 4.1 Definindo Erros com `thiserror`

```toml
# Cargo.toml
[dependencies]
thiserror = "2"
```

```rust
// src-tauri/src/error.rs
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("Erro de banco de dados: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Membro não encontrado: id={0}")]
    MemberNotFound(i64),

    #[error("Squad não encontrado: id={0}")]
    SquadNotFound(i64),

    #[error("Evento não encontrado: id={0}")]
    EventNotFound(i64),

    #[error("Dados inválidos: {0}")]
    Validation(String),

    #[error("Erro de IO: {0}")]
    Io(#[from] std::io::Error),
}

// Necessário para usar em Tauri commands (erros precisam ser serializáveis)
impl serde::Serialize for AppError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::ser::Serializer,
    {
        serializer.serialize_str(self.to_string().as_ref())
    }
}

// Alias de conveniência
pub type Result<T> = std::result::Result<T, AppError>;
```

### 4.2 `thiserror` vs `anyhow`

| | `thiserror` | `anyhow` |
|---|---|---|
| **Uso ideal** | Bibliotecas, APIs públicas | Código de aplicação rápido |
| **Erros tipados** | ✅ Sim | ❌ Um tipo genérico |
| **Mensagens** | `#[error("...")]` | `.context("...")` |
| **Tauri commands** | ✅ Recomendado | Precisa de wrapper |
| **Diagnóstico** | Explícito por variante | Stack trace em runtime |

**Para este projeto use `thiserror`** — os commands Tauri precisam serializar os erros para o frontend, e ter tipos explícitos facilita o mapeamento TypeScript ↔ Rust.

---

## 5. Serde: Serialização JSON {#serde}

Serde é a biblioteca de serialização/deserialização do ecossistema Rust. Tauri usa Serde internamente para a comunicação entre frontend e backend.

```toml
# Cargo.toml
[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

```python
# Python equivalente
import json
from dataclasses import asdict

member = Member(id=1, name="João")
json_str = json.dumps(asdict(member))
```

```rust
// Rust: apenas adicione os derives
#[derive(Serialize, Deserialize)]
pub struct Member {
    pub id: i64,
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]  // omite null no JSON
    pub email: Option<String>,
    #[serde(rename = "createdAt")]  // camelCase para o frontend JS
    pub created_at: String,
}

// Serializar manualmente (raramente necessário — Tauri faz isso)
let json = serde_json::to_string(&member)?;
// Deserializar
let member: Member = serde_json::from_str(&json)?;
```

### 5.1 Atributos Úteis do Serde

```rust
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]  // todos os campos em camelCase automaticamente
pub struct EventResponse {
    pub event_id: i64,       // serializa como "eventId"
    pub squad_name: String,  // serializa como "squadName"
    pub event_date: String,  // serializa como "eventDate"
}

// Enum como string no JSON
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Role {
    Presenter,
    SoundTech,
    VideoTech,
    Vocalist,
}
// Serializa como: "presenter", "sound_tech", etc.

// Enum com tag (útil para erros tipados)
#[derive(Serialize)]
#[serde(tag = "type", content = "data")]
pub enum ApiResponse<T> {
    Success(T),
    Error { message: String, code: u16 },
}
```

---

## 6. Async Rust com Tokio {#async}

Tauri v2 usa Tokio internamente como runtime assíncrono. Tokio é o runtime async mais utilizado em Rust, fornecendo execução concorrente multi-thread sem necessidade de threads por tarefa.

### 6.1 Conceito: Futures

```python
# Python async: coroutines com asyncio
import asyncio

async def buscar_dado():
    await asyncio.sleep(1)
    return "dado"

asyncio.run(buscar_dado())
```

```rust
// Rust async: Futures com Tokio
use tokio::time::{sleep, Duration};

async fn buscar_dado() -> String {
    sleep(Duration::from_secs(1)).await;
    "dado".to_string()
}

#[tokio::main]
async fn main() {
    let resultado = buscar_dado().await;
    println!("{}", resultado);
}
```

**Diferença chave:** Em Python, `async/await` é single-threaded por padrão (event loop). Em Rust com Tokio, as tasks podem rodar em múltiplas threads (work-stealing scheduler). Uma `Future` em Rust é uma **state machine** — o compilador transforma o código async em um enum de estados que não bloqueia o thread.

### 6.2 Tokio no Contexto Tauri

Em Tauri v2, você **não** precisa criar o runtime Tokio manualmente — ele já existe. Commands `async` no Tauri são executados no runtime Tokio do próprio Tauri:

```rust
// Command assíncrono — Tauri usa o runtime Tokio interno
#[tauri::command]
async fn listar_membros(
    state: tauri::State<'_, AppState>
) -> Result<Vec<Member>, AppError> {
    let members = member_service::list_all(&state.pool).await?;
    Ok(members)
}
```

### 6.3 Gerenciando Estado Compartilhado (AppState)

```rust
// src-tauri/src/lib.rs
use sqlx::SqlitePool;
use std::sync::Arc;

pub struct AppState {
    pub pool: Arc<SqlitePool>,
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let pool = tauri::async_runtime::block_on(async {
                setup_database().await.expect("Falha ao conectar ao banco")
            });
            app.manage(AppState {
                pool: Arc::new(pool),
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::members::list_members,
            commands::members::create_member,
            commands::members::update_member,
            commands::members::delete_member,
            commands::squads::list_squads,
            commands::events::list_events,
            commands::schedule::generate_schedule,
        ])
        .run(tauri::generate_context!())
        .expect("Erro ao iniciar aplicação Tauri");
}
```

---

## 7. SQLx: Setup, Pool, Migrations e Queries {#sqlx}

SQLx é o toolkit SQL assíncrono do Rust. Diferente de ORMs (SQLAlchemy, Django ORM), SQLx usa **SQL puro** com verificação em tempo de compilação.

### 7.1 Dependências

```toml
# src-tauri/Cargo.toml
[dependencies]
sqlx = { version = "0.8", features = [
    "runtime-tokio",
    "sqlite",
    "migrate",
    "derive",
    "chrono",
] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "2"
tauri = { version = "2", features = [] }
```

### 7.2 Connection Pool e Setup

```rust
// src-tauri/src/database.rs
use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};
use std::time::Duration;

pub async fn setup_database() -> Result<SqlitePool, sqlx::Error> {
    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "sqlite:escala_midia.db".to_string());

    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .acquire_timeout(Duration::from_secs(3))
        .connect(&database_url)
        .await?;

    // Habilita foreign keys no SQLite
    sqlx::query("PRAGMA foreign_keys = ON")
        .execute(&pool)
        .await?;

    // Roda as migrations automaticamente ao iniciar
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await?;

    Ok(pool)
}
```

### 7.3 Migrations

```bash
# Instalar o CLI do SQLx
cargo install sqlx-cli --no-default-features --features sqlite

# Criar uma migration
sqlx migrate add create_members_table

# Rodar migrations
sqlx migrate run
```

```sql
-- migrations/20240101000001_create_members_table.sql
CREATE TABLE IF NOT EXISTS members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT,
    phone       TEXT,
    instagram   TEXT,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- migrations/20240101000002_create_squads_table.sql
CREATE TABLE IF NOT EXISTS squads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT
);

-- migrations/20240101000003_create_squad_members_table.sql
CREATE TABLE IF NOT EXISTS squad_members (
    squad_id    INTEGER NOT NULL REFERENCES squads(id) ON DELETE CASCADE,
    member_id   INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    role        TEXT,
    PRIMARY KEY (squad_id, member_id)
);

-- migrations/20240101000004_create_events_table.sql
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    squad_id    INTEGER REFERENCES squads(id),
    notes       TEXT
);

-- migrations/20240101000005_create_schedule_table.sql
CREATE TABLE IF NOT EXISTS schedule (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    member_id   INTEGER NOT NULL REFERENCES members(id),
    role        TEXT    NOT NULL
);
```

### 7.4 Queries Tipadas

```rust
// src-tauri/src/services/member_service.rs
use sqlx::SqlitePool;
use crate::{error::Result, models::{Member, CreateMemberRequest}};

// Listar todos (query_as! verifica SQL em tempo de compilação)
pub async fn list_all(pool: &SqlitePool) -> Result<Vec<Member>> {
    let members = sqlx::query_as!(
        Member,
        "SELECT id, name, email, phone, instagram, active, created_at
         FROM members
         ORDER BY name"
    )
    .fetch_all(pool)
    .await?;
    Ok(members)
}

// Buscar por ID
pub async fn find_by_id(pool: &SqlitePool, id: i64) -> Result<Member> {
    let member = sqlx::query_as!(
        Member,
        "SELECT id, name, email, phone, instagram, active, created_at
         FROM members WHERE id = ?",
        id
    )
    .fetch_optional(pool)
    .await?
    .ok_or(crate::error::AppError::MemberNotFound(id))?;
    Ok(member)
}

// Criar
pub async fn create(pool: &SqlitePool, req: CreateMemberRequest) -> Result<Member> {
    let result = sqlx::query!(
        "INSERT INTO members (name, email, phone, instagram)
         VALUES (?, ?, ?, ?)
         RETURNING id",
        req.name,
        req.email,
        req.phone,
        req.instagram,
    )
    .fetch_one(pool)
    .await?;

    find_by_id(pool, result.id).await
}

// Atualizar
pub async fn update(
    pool: &SqlitePool,
    id: i64,
    name: Option<String>,
    active: Option<bool>,
) -> Result<Member> {
    sqlx::query!(
        "UPDATE members SET
            name = COALESCE(?, name),
            active = COALESCE(?, active)
         WHERE id = ?",
        name,
        active,
        id
    )
    .execute(pool)
    .await?;

    find_by_id(pool, id).await
}

// Remover
pub async fn delete(pool: &SqlitePool, id: i64) -> Result<()> {
    let result = sqlx::query!("DELETE FROM members WHERE id = ?", id)
        .execute(pool)
        .await?;

    if result.rows_affected() == 0 {
        return Err(crate::error::AppError::MemberNotFound(id));
    }
    Ok(())
}

// Query mais complexa: membros de um squad com roles
pub async fn list_by_squad(pool: &SqlitePool, squad_id: i64) -> Result<Vec<Member>> {
    let members = sqlx::query_as!(
        Member,
        r#"SELECT m.id, m.name, m.email, m.phone, m.instagram, m.active, m.created_at
           FROM members m
           JOIN squad_members sm ON sm.member_id = m.id
           WHERE sm.squad_id = ? AND m.active = 1
           ORDER BY m.name"#,
        squad_id
    )
    .fetch_all(pool)
    .await?;
    Ok(members)
}
```

### 7.5 Modo Offline do SQLx (sem banco em CI)

Para ambientes sem banco de dados (CI/CD, build sem DB):

```bash
# Gera arquivo .sqlx/ com metadados das queries verificadas
cargo sqlx prepare

# Build offline (usa .sqlx/ em vez de conectar ao banco)
SQLX_OFFLINE=true cargo build
```

---

## 8. Estrutura do Projeto Tauri {#estrutura}

```
src-tauri/
├── Cargo.toml
├── build.rs
├── migrations/
│   ├── 20240101000001_create_members_table.sql
│   ├── 20240101000002_create_squads_table.sql
│   └── ...
└── src/
    ├── lib.rs              ← ponto de entrada: setup Tauri + state
    ├── main.rs             ← thin wrapper para desktop
    ├── error.rs            ← AppError com thiserror
    ├── models.rs           ← structs de domínio (Member, Squad, Event...)
    ├── database.rs         ← setup pool + migrations
    ├── commands/
    │   ├── mod.rs
    │   ├── members.rs      ← #[tauri::command] para membros
    │   ├── squads.rs
    │   ├── events.rs
    │   └── schedule.rs
    └── services/
        ├── mod.rs
        ├── member_service.rs   ← lógica de negócio + queries
        ├── squad_service.rs
        ├── event_service.rs
        └── schedule_service.rs
```

---

## 9. Commands Tauri {#commands}

```rust
// src-tauri/src/commands/members.rs
use tauri::State;
use crate::{error::{AppError, Result}, models::*, services::member_service, AppState};

#[tauri::command]
pub async fn list_members(
    state: State<'_, AppState>
) -> Result<Vec<Member>> {
    member_service::list_all(&state.pool).await
}

#[tauri::command]
pub async fn get_member(
    id: i64,
    state: State<'_, AppState>
) -> Result<Member> {
    member_service::find_by_id(&state.pool, id).await
}

#[tauri::command]
pub async fn create_member(
    payload: CreateMemberRequest,
    state: State<'_, AppState>
) -> Result<Member> {
    member_service::create(&state.pool, payload).await
}

#[tauri::command]
pub async fn update_member(
    id: i64,
    payload: UpdateMemberRequest,
    state: State<'_, AppState>
) -> Result<Member> {
    member_service::update(&state.pool, id, payload.name, payload.active).await
}

#[tauri::command]
pub async fn delete_member(
    id: i64,
    state: State<'_, AppState>
) -> Result<()> {
    member_service::delete(&state.pool, id).await
}
```

**No frontend TypeScript:**
```typescript
import { invoke } from '@tauri-apps/api/core';

// Listar membros
const members = await invoke<Member[]>('list_members');

// Criar membro
const newMember = await invoke<Member>('create_member', {
  payload: { name: 'João Silva', phone: '11999999999' }
});

// Tratar erros
try {
  await invoke('delete_member', { id: 999 });
} catch (error) {
  // error é a string do AppError::MemberNotFound
  console.error(error); // "Membro não encontrado: id=999"
}
```

---

## 10. Testes em Rust {#testes}

### 10.1 Testes Unitários

Em Rust, testes ficam **no mesmo arquivo** do código, dentro de um módulo `#[cfg(test)]`:

```rust
// src-tauri/src/services/member_service.rs

// ... código do serviço ...

#[cfg(test)]   // este módulo só compila em modo test
mod tests {
    use super::*;  // importa tudo do módulo pai

    // Teste de lógica pura (sem banco)
    #[test]
    fn test_nome_valido() {
        let nome = "João Silva";
        assert!(!nome.is_empty());
        assert!(nome.len() < 255);
    }

    // Teste com Result
    #[test]
    fn test_error_display() {
        let erro = AppError::MemberNotFound(42);
        assert_eq!(erro.to_string(), "Membro não encontrado: id=42");
    }
}
```

### 10.2 Testes de Integração com Banco (SQLite em memória)

```rust
// src-tauri/src/services/member_service.rs — dentro do mod tests

#[cfg(test)]
mod tests {
    use super::*;
    use sqlx::SqlitePool;

    // Cria banco SQLite em memória para cada teste
    async fn setup_test_db() -> SqlitePool {
        let pool = SqlitePool::connect(":memory:").await.unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();
        pool
    }

    #[tokio::test]  // teste assíncrono
    async fn test_criar_e_buscar_membro() {
        let pool = setup_test_db().await;

        let req = CreateMemberRequest {
            name: "Maria Santos".to_string(),
            email: Some("maria@exemplo.com".to_string()),
            phone: None,
            instagram: None,
        };

        let criado = create(&pool, req).await.unwrap();
        assert_eq!(criado.name, "Maria Santos");
        assert!(criado.id > 0);
        assert!(criado.active);

        let buscado = find_by_id(&pool, criado.id).await.unwrap();
        assert_eq!(buscado.name, criado.name);
    }

    #[tokio::test]
    async fn test_membro_nao_encontrado_retorna_erro() {
        let pool = setup_test_db().await;

        let resultado = find_by_id(&pool, 999).await;
        assert!(resultado.is_err());

        match resultado.unwrap_err() {
            AppError::MemberNotFound(id) => assert_eq!(id, 999),
            outro => panic!("Erro inesperado: {:?}", outro),
        }
    }

    #[tokio::test]
    async fn test_deletar_membro() {
        let pool = setup_test_db().await;

        let req = CreateMemberRequest {
            name: "Pedro".to_string(),
            email: None, phone: None, instagram: None,
        };
        let membro = create(&pool, req).await.unwrap();

        delete(&pool, membro.id).await.unwrap();

        let resultado = find_by_id(&pool, membro.id).await;
        assert!(resultado.is_err());
    }

    #[tokio::test]
    async fn test_listar_membros_de_squad() {
        let pool = setup_test_db().await;

        // Criar squad
        sqlx::query!("INSERT INTO squads (name) VALUES ('Louvor')")
            .execute(&pool).await.unwrap();
        let squad_id = 1i64;

        // Criar membros
        let m1 = create(&pool, CreateMemberRequest {
            name: "Ana".to_string(), email: None, phone: None, instagram: None,
        }).await.unwrap();

        // Associar ao squad
        sqlx::query!(
            "INSERT INTO squad_members (squad_id, member_id) VALUES (?, ?)",
            squad_id, m1.id
        ).execute(&pool).await.unwrap();

        let membros = list_by_squad(&pool, squad_id).await.unwrap();
        assert_eq!(membros.len(), 1);
        assert_eq!(membros[0].name, "Ana");
    }
}
```

### 10.3 Rodando os Testes

```bash
# Todos os testes
cargo test

# Com output impresso (println! visível)
cargo test -- --nocapture

# Filtrar por nome
cargo test test_criar

# Testes de um módulo específico
cargo test members::tests
```

---

## 11. Tabela Comparativa Python → Rust {#python-rust}

| Conceito | Python | Rust |
|---|---|---|
| **Gerenciamento de memória** | Garbage Collector | Ownership + Borrow Checker |
| **Tipos opcionais** | `Optional[str]` / `None` | `Option<String>` / `None` / `Some("...")` |
| **Tratamento de erros** | `try/except Exception` | `Result<T, E>` + operador `?` |
| **Classes** | `class Membro:` | `struct Member {}` |
| **Herança** | `class B(A):` | Traits (sem herança de implementação) |
| **Decorators** | `@dataclass` | `#[derive(Debug, Clone)]` |
| **Módulos** | `from services import member` | `mod services; use services::member;` |
| **Dicionários** | `dict` | `HashMap<K, V>` |
| **Listas** | `list` | `Vec<T>` |
| **Strings** | `str` (unicode) | `&str` (emprestada) / `String` (owned) |
| **Async** | `async def` + `asyncio` | `async fn` + `tokio` |
| **Await** | `await coroutine` | `future.await` |
| **Package manager** | `pip` | `cargo` |
| **Dependências** | `requirements.txt` | `Cargo.toml` |
| **Testes** | `pytest` | `cargo test` + `#[test]` embutido |
| **Variáveis mutáveis** | Por padrão mutável | `let` (imutável) / `let mut` (mutável) |
| **Null safety** | `None` pode aparecer inesperadamente | `Option<T>` força tratamento explícito |
| **Closures** | `lambda x: x + 1` | `\|x\| x + 1` |
| **Iteradores** | `list(map(...))` | `.iter().map(...).collect()` |
| **Serialização JSON** | `json.dumps(dict)` | `serde_json::to_string(&struct)` |
| **ORM** | SQLAlchemy, Django ORM | SQLx (SQL puro tipado) |

---

## 12. Padrões Recomendados para Backend Tauri {#padroes}

### 12.1 Separação de Responsabilidades

```
commands/   → interface com o frontend (valida input, chama services)
services/   → lógica de negócio (pura, testável)
models/     → tipos de dados (structs, enums)
database/   → setup, pool, migrations
error/      → tipos de erro centralizados
```

### 12.2 Commands Finos, Services Gordos

```rust
// ✅ CORRETO: command apenas delega
#[tauri::command]
pub async fn create_member(
    payload: CreateMemberRequest,
    state: State<'_, AppState>
) -> Result<Member> {
    member_service::create(&state.pool, payload).await
}

// ❌ ERRADO: lógica no command
#[tauri::command]
pub async fn create_member(
    payload: CreateMemberRequest,
    state: State<'_, AppState>
) -> Result<Member> {
    if payload.name.is_empty() { return Err(...); }
    let id = sqlx::query!("INSERT INTO members...").execute(&state.pool).await?;
    // ... lógica misturada com interface
}
```

### 12.3 Transações para Operações Compostas

```rust
// Gerar escala: operação atômica (tudo ou nada)
pub async fn generate_schedule(
    pool: &SqlitePool,
    event_id: i64,
    assignments: Vec<(i64, String)>, // (member_id, role)
) -> Result<Vec<Schedule>> {
    let mut tx = pool.begin().await?;

    // Limpar escala anterior
    sqlx::query!("DELETE FROM schedule WHERE event_id = ?", event_id)
        .execute(&mut *tx)
        .await?;

    // Inserir novas atribuições
    for (member_id, role) in &assignments {
        sqlx::query!(
            "INSERT INTO schedule (event_id, member_id, role) VALUES (?, ?, ?)",
            event_id, member_id, role
        )
        .execute(&mut *tx)
        .await?;
    }

    tx.commit().await?;

    // Buscar escala gerada
    let schedule = sqlx::query_as!(
        Schedule,
        "SELECT * FROM schedule WHERE event_id = ? ORDER BY role",
        event_id
    )
    .fetch_all(pool)
    .await?;

    Ok(schedule)
}
```

### 12.4 `Arc` para Estado Compartilhado entre Threads

```rust
use std::sync::Arc;
use sqlx::SqlitePool;

pub struct AppState {
    pub pool: Arc<SqlitePool>,  // Arc = Atomic Reference Count (thread-safe)
}

// Arc permite clonar o ponteiro sem clonar o pool
// Cada clone aponta para o mesmo pool subjacente
```

### 12.5 `tracing` para Logs Estruturados

```toml
[dependencies]
tracing = "0.1"
tracing-subscriber = "0.3"
```

```rust
use tracing::{info, warn, error, instrument};

#[instrument(skip(pool))]  // instrumenta automaticamente com nome da função
pub async fn create_member(pool: &SqlitePool, req: CreateMemberRequest) -> Result<Member> {
    info!(name = %req.name, "Criando novo membro");

    let member = /* ... */;

    info!(id = member.id, "Membro criado com sucesso");
    Ok(member)
}
```

---

## 13. Exemplo Completo: Geração de Escala {#exemplo-escala}

```rust
// src-tauri/src/services/schedule_service.rs

use sqlx::SqlitePool;
use crate::{error::Result, models::*};

/// Gera escala automática para um evento baseada nos membros disponíveis do squad
pub async fn generate_auto_schedule(
    pool: &SqlitePool,
    event_id: i64,
) -> Result<Vec<Schedule>> {
    // 1. Buscar evento com seu squad
    let event = sqlx::query_as!(
        Event,
        "SELECT id, name, date, squad_id, notes FROM events WHERE id = ?",
        event_id
    )
    .fetch_optional(pool)
    .await?
    .ok_or(crate::error::AppError::EventNotFound(event_id))?;

    let squad_id = event.squad_id.ok_or_else(|| {
        crate::error::AppError::Validation(
            "Evento não tem squad associado".to_string()
        )
    })?;

    // 2. Buscar membros ativos do squad
    let members = sqlx::query_as!(
        Member,
        r#"SELECT m.id, m.name, m.email, m.phone, m.instagram, m.active, m.created_at
           FROM members m
           JOIN squad_members sm ON sm.member_id = m.id
           WHERE sm.squad_id = ? AND m.active = 1
           ORDER BY m.name"#,
        squad_id
    )
    .fetch_all(pool)
    .await?;

    if members.is_empty() {
        return Err(crate::error::AppError::Validation(
            "Squad não tem membros ativos".to_string()
        ));
    }

    // 3. Montar atribuições (lógica de negócio)
    let roles = vec!["Apresentador", "Som", "Vídeo", "Vocal 1", "Vocal 2"];
    let assignments: Vec<(i64, String)> = roles
        .iter()
        .enumerate()
        .filter_map(|(i, role)| {
            members.get(i % members.len()).map(|m| (m.id, role.to_string()))
        })
        .collect();

    // 4. Persistir em transação
    let mut tx = pool.begin().await?;

    sqlx::query!("DELETE FROM schedule WHERE event_id = ?", event_id)
        .execute(&mut *tx)
        .await?;

    for (member_id, role) in &assignments {
        sqlx::query!(
            "INSERT INTO schedule (event_id, member_id, role) VALUES (?, ?, ?)",
            event_id, member_id, role
        )
        .execute(&mut *tx)
        .await?;
    }

    tx.commit().await?;

    // 5. Retornar escala criada
    let schedule = sqlx::query_as!(
        Schedule,
        "SELECT id, event_id, member_id, role FROM schedule WHERE event_id = ?",
        event_id
    )
    .fetch_all(pool)
    .await?;

    Ok(schedule)
}
```

---

## Referências {#referencias}

- **The Rust Book** — https://doc.rust-lang.org/book/  
  Capítulo 4 (Ownership), Capítulo 10 (Generics/Traits), Capítulo 16 (Concorrência)
- **Tokio Tutorial** — https://tokio.rs/tokio/tutorial  
  Especialmente: Async in Depth, Shared State, Framing
- **SQLx Documentation** — https://docs.rs/sqlx/latest/sqlx/  
  Especialmente: `query_as!`, `FromRow`, migrations, `SqlitePool`
- **SQLx GitHub** — https://github.com/launchbadge/sqlx  
  README com exemplos práticos e feature flags
- **Serde Documentation** — https://docs.rs/serde/latest/serde/  
  Site oficial com guia: https://serde.rs
- **thiserror** — https://docs.rs/thiserror/latest/thiserror/  
  Para erros tipados em bibliotecas e comandos Tauri
- **Tauri v2 — Calling Rust** — https://v2.tauri.app/develop/calling-rust/  
  Commands, State management, async commands, error handling
- **Tauri v2 Docs** — https://v2.tauri.app/develop/  
  Documentação oficial completa do Tauri v2
- **Rust by Example** — https://doc.rust-lang.org/rust-by-example/  
  Exemplos práticos de cada conceito
- **Async Book** — https://rust-lang.github.io/async-book/  
  Deep dive em Futures, executors, pinning