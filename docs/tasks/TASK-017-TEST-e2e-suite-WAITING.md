# TASK-017 — Suite E2E Completa (Playwright + Tauri WebDriver)

**Domínio:** TEST  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-014 (frontend completo com todos os fluxos implementados), TASK-006 (gerador de escala pronto)  
**Estimativa:** XL

---

## Descrição

Implementar a suite E2E completa usando Playwright com o driver Tauri. Os testes exercitam o app real compilado — sem mocks de IPC — contra um banco SQLite isolado por teste, cobrindo todos os fluxos críticos definidos no §12 da spec:

1. CRUD de membros
2. Criação de times e associação de membros
3. Criação de eventos e configuração por time
4. Fluxo completo ponta a ponta: membros → times → eventos → geração de escala → verificação do resultado
5. Regressão de indisponibilidade: membro ausente não aparece na escala gerada
6. Regressão de casais: casal cadastrado nunca é escalado no mesmo evento

Além dos testes funcionais, configurar: screenshot automático em falha, relatório HTML Playwright, fixtures de banco isolado por describe-block e smoke tests para todos os fluxos principais.

---

## Critérios de Aceite

- [ ] `playwright.config.ts` configurado com `use.screenshot: 'only-on-failure'` e `reporter: [['html', { open: 'never' }], ['list']]`
- [ ] Fixture `isolatedDb` cria um banco SQLite temporário por teste (`:memory:` ou arquivo em `tmp/`) e executa todas as migrations antes de cada teste
- [ ] Fixture `tauriApp` inicia e encerra o processo Tauri apontando para o banco isolado via variável de ambiente `DATABASE_URL`
- [ ] Todos os seletores usam `data-testid` (nunca classes CSS ou texto literal)
- [ ] Teste 1 — CRUD membros: criar → verificar na lista → editar → verificar atualização → deletar → confirmar remoção
- [ ] Teste 2 — Times: criar time → associar 3 membros → verificar contagem → remover 1 membro → verificar contagem
- [ ] Teste 3 — Eventos: criar evento fixo (domingo) → configurar 2 times com min/max → verificar configuração salva
- [ ] Teste 4 — Fluxo completo: seed de 10 membros + 2 times + 1 evento → gerar escala para 4 datas → verificar que cada data tem membros escalados dentro do `min_members`/`max_members`
- [ ] Teste 5 — Indisponibilidade: membro com indisponibilidade cobrindo a data do evento **não aparece** na escala gerada para aquela data
- [ ] Teste 6 — Casais: par cadastrado como casal **nunca aparece junto** no mesmo `schedule_members` para o mesmo `schedule_id`
- [ ] Smoke tests: um teste `smoke.spec.ts` que navega por todas as rotas principais e verifica que carregam sem erros de console
- [ ] Relatório HTML gerado em `playwright-report/` após cada execução
- [ ] Screenshots de falha salvas em `test-results/` com nome descritivo
- [ ] `npm run test:e2e` executa a suite completa
- [ ] `npm run test:e2e:smoke` executa apenas os smoke tests (< 60s)
- [ ] Todos os 6 fluxos passam no runner Linux com `xvfb-run`

---

## Notas Técnicas

### Estrutura de Arquivos

