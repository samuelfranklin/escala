# Project Guidelines

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