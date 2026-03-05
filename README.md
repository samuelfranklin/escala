# Escala Mídia

> **App desktop multiplataforma para gestão de escalas do time de mídia.**
> Construído integralmente com **AI Pair-Coding** — GitHub Copilot CLI + agentes especializados.

[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)](https://github.com)
[![Stack](https://img.shields.io/badge/stack-Tauri%20v2%20%2B%20Svelte%20%2B%20Rust-orange)](https://tauri.app)
[![Plataformas](https://img.shields.io/badge/plataformas-Windows%20%7C%20Linux%20%7C%20macOS-blue)](docs/specs/app.spec.md)
[![Testes](https://img.shields.io/badge/cobertura%20alvo-100%25-brightgreen)](docs/specs/app.spec.md#12-estratégia-de-testes)

---

## O que é

Coordenadores de time de mídia de igrejas gerenciam manualmente em planilhas quem serve em cada culto — um processo propenso a conflitos de disponibilidade, esquecimentos e retrabalho semanal.

**Escala Mídia** resolve isso com um app desktop que:

- 📋 Cadastra **membros**, **times** (squads) e **eventos**
- 🔄 Registra **indisponibilidades** e **restrições** (ex.: casais que não servem juntos)
- ⚡ **Gera escalas automaticamente** respeitando todas as regras
- 📤 **Exporta** a escala em formatos prontos para compartilhar
- 🖥️ Funciona **100% offline**, sem depender de internet ou servidores externos

---

## Stack Tecnológico

| Camada | Tecnologia | Por quê |
|---|---|---|
| **Framework desktop** | [Tauri v2](https://tauri.app) | Binário nativo (~5 MB), seguro por padrão, multiplataforma |
| **Backend** | [Rust](https://rust-lang.org) + [SQLx](https://github.com/launchbadge/sqlx) | Performance, segurança de memória, queries verificadas em compile-time |
| **Banco de dados** | SQLite | Offline-first, zero configuração, arquivo único portátil |
| **Frontend** | [Svelte 5](https://svelte.dev) + TypeScript | Bundle pequeno, reatividade nativa, tipagem forte |
| **Testes E2E** | [Playwright](https://playwright.dev) + Tauri WebDriver | Testa a aplicação real, sem mocks da UI |
| **CI/CD** | GitHub Actions | Build multiplataforma + gates de cobertura automáticos |

---

## Por que essas decisões de arquitetura?

### Tauri ao invés de Electron
Electron embarca um Chromium completo (~150 MB). Tauri usa a WebView nativa do sistema operacional, resultando em binários de **~5 MB** com a mesma experiência de UI web. Tauri v2 também introduziu um modelo de **capabilities** (permissões por feature) que elimina a superfície de ataque do `shell: all`.

### Rust ao invés de Node/Python no backend
Rust oferece **segurança de memória em compile-time** (sem GC, sem null pointers, sem race conditions) e performance próxima de C. Para um app que manipula dados de pessoas e gera escalas com regras complexas, a confiabilidade do compilador Rust é um ativo — bugs viram erros de compilação, não crashes em produção.

### SQLx ao invés de Diesel ou ORMs pesados
SQLx verifica as queries SQL em **tempo de compilação** (via macros `query!`), combinando a flexibilidade de SQL puro com a segurança de tipos. Diesel exige um schema Rust separado e tem curva de aprendizado maior; SQLx mantém o SQL como fonte da verdade.

### Svelte ao invés de React/Vue
Svelte compila para JavaScript puro sem runtime virtual DOM — bundle menor e performance melhor para uma app desktop. O modelo de reatividade `$state` do Svelte 5 é mais simples que hooks React para casos de uso de formulários e listas.

### SQLite ao invés de banco de dados servidor
O produto é **offline-first** por design — o coordenador precisa usar o app sem internet no culto. SQLite é um arquivo local único, sem configuração, portátil (backup = copiar o arquivo) e suportado nativamente pelo SQLx.

---

## Plataformas

| Plataforma | Formato de instalação |
|---|---|
| Windows 10/11 (x64) | `.msi` (WiX) e `.exe` (NSIS) |
| Linux x64/ARM64 | `.AppImage`, `.deb`, `.rpm` |
| macOS 12+ (Intel + Apple Silicon) | `.dmg` (assinado + notarizado) |

---

## Desenvolvimento com AI Pair-Coding

Este projeto é desenvolvido integralmente com **GitHub Copilot CLI** em modo de par — o desenvolvedor humano define o **o quê** e **por quê**, os agentes de IA executam o **como** com supervisão contínua.

O fluxo de trabalho usa **TDD estrito**:

```
RED   → Agente escreve teste que falha (especifica o comportamento)
GREEN → Agente implementa o mínimo para passar
REFACTOR → Agente melhora qualidade mantendo testes verdes
```

Agentes especializados atuam em domínios específicos (backend, frontend, segurança, UX, arquitetura) conforme descrito em [`AGENTS.md`](AGENTS.md).

**Cobertura de testes:** ≥ 75% durante dev → ≥ 90% em RC → 100% em v1.0.

---

## Documentação

| Documento | Descrição |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Fonte da verdade para agentes de IA — leia antes de qualquer tarefa |
| [`docs/specs/app.spec.md`](docs/specs/app.spec.md) | Especificação técnica completa (arquitetura, dados, testes, deploy) |
| [`docs/pdrs/PDR-TAURI-001.md`](docs/pdrs/PDR-TAURI-001.md) | Pesquisa técnica sobre Tauri v2 |
| [`docs/pdrs/PDR-RUST-001.md`](docs/pdrs/PDR-RUST-001.md) | Pesquisa técnica sobre Rust para o projeto |
| [`docs/tasks/`](docs/tasks/) | Tasks de desenvolvimento com status e critérios de aceite |

---

## Licença

MIT © Time de Mídia
