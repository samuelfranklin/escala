# TASK-026 — Frontend: Dashboard Page Redesign

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-025  
**Estimativa:** S (1–2h)

## Descrição

Reconstruir a página `src/routes/dashboard/+page.svelte` usando componentes shadcn-svelte. A lógica do `<script>` (chamadas de API, estado, cálculos) permanece **100% inalterada**.

## Critérios de Aceite

- [ ] `data-testid="dashboard"` preservado no elemento raiz
- [ ] 3 KPI cards renderizados com `<Card.Root>` + `<Card.Content>`
- [ ] Ícones inline SVG substituídos por `<Icon icon="lucide:...">` nas cores corretas
- [ ] Badge do tipo de evento → `<Badge variant="secondary">`
- [ ] Botão "Criar Evento" → `<Button href="/events">`
- [ ] Card do próximo evento com `<Card.Root>`
- [ ] Seção de alertas com `<Card.Root>`
- [ ] `pnpm dev` sem erros TypeScript

## Notas Técnicas

### Mapeamento de elementos

| Atual | Novo |
|---|---|
| `<div class="card flex items-center gap-4">` | `<Card.Root><Card.Content class="flex items-center gap-4 pt-6">` |
| Inline SVG icons | `<Icon icon="lucide:users" class="size-5 text-primary" />` |
| `<span class="badge badge-blue">` | `<Badge variant="secondary">` |
| `<a href="/events" class="btn btn-primary">` | `<Button href="/events">` |
| `class="btn btn-secondary"` (links) | `<Button variant="outline" href="...">` |

### Ícones por KPI card

- Membros: `lucide:users`
- Times: `lucide:layers`
- Eventos: `lucide:calendar`
- Próximo evento: `lucide:calendar-days`
- Alertas OK: `lucide:check-circle`
- Alerta warning: `lucide:triangle-alert`

### Referências

- [SPEC-DASHBOARD.md](../specs/screens/SPEC-DASHBOARD.md)

## Progresso

- [ ] Substituir KPI cards por `<Card.Root>`
- [ ] Substituir SVGs por `<Icon>`
- [ ] Substituir `.badge-blue` por `<Badge variant="secondary">`
- [ ] Substituir botão por `<Button>`
- [ ] Substituir próximo evento card por `<Card.Root>`
- [ ] Substituir alertas por `<Card.Root>`
- [ ] Commit: `feat(ui): dashboard redesign com shadcn (#TASK-026)`
