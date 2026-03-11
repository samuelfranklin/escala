# TASK-029 — Frontend: Events Page Redesign

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-025  
**Estimativa:** M (2–4h)

## Descrição

Reconstruir `src/routes/events/+page.svelte` com componentes shadcn-svelte. Toda a lógica do `<script>` permanece **100% inalterada**. TODOS os `data-testid` devem ser preservados.

## Critérios de Aceite

- [ ] `data-testid="events-page"` preservado no div raiz
- [ ] `data-testid="event-row"` preservado em cada item da lista
- [ ] `data-testid="btn-new-event"` preservado no botão de criação
- [ ] Event list cards → `<Card.Root class="cursor-pointer">`
- [ ] Event type badge → `<Badge variant="secondary">`
- [ ] Status de squads (verde/vermelho) → `<span>` com classes Tailwind preservado
- [ ] Botão novo evento → `<Button data-testid="btn-new-event">`
- [ ] Botão deletar evento → `<Button variant="destructive" size="icon">`
- [ ] Modal → `<Dialog.Root bind:open={showModal}>`
- [ ] 3 selects no modal (event_type, day_of_week, recurrence) → `<Select.Root>`
- [ ] Data input para eventos especiais → `<Input type="date">`
- [ ] Checkboxes de squad → `<Checkbox bind:checked={squadConfig[sq.id].enabled}>`
- [ ] Inputs min/max → `<Input type="number" class="w-14">` preservando `onclick={(e) => e.stopPropagation()}`
- [ ] Testes E2E passando

## Notas Técnicas

### Gotcha: day_of_week é number, Select retorna string

```svelte
<Select.Root
  type="single"
  value={String(form.day_of_week ?? 0)}
  onValueChange={(v) => (form.day_of_week = Number(v))}
>
  <Select.Trigger>{DAYS[form.day_of_week ?? 0]}</Select.Trigger>
  <Select.Content>
    {#each DAYS as day, i}
      <Select.Item value={String(i)}>{day}</Select.Item>
    {/each}
  </Select.Content>
</Select.Root>
```

### Checkbox de squad com Svelte 5 runes

```svelte
import * as Checkbox from "$lib/components/ui/checkbox/index.js";
import { Label } from "$lib/components/ui/label/index.js";

<div class="flex items-center gap-3">
  <Checkbox.Root
    id={`sq-${sq.id}`}
    bind:checked={squadConfig[sq.id].enabled}
  />
  <Label for={`sq-${sq.id}`} class="flex-1 cursor-pointer font-medium">
    {sq.name}
  </Label>
</div>
```

### Modal condicional (tipo regular vs especial)

O modal atual condicionalmente mostra campos de `day_of_week`/`recurrence` OU `event_date`. Este comportamento lógico deve ser preservado; apenas os inputs mudam de `.input` para `<Input>` e `<select>` para `<Select.Root>`.

### Referências

- [SPEC-EVENTS.md](../specs/screens/SPEC-EVENTS.md)

## Progresso

- [ ] Event rows → `<Card.Root>`
- [ ] Event type → `<Badge variant="secondary">`
- [ ] Botão novo → `<Button data-testid="btn-new-event">`
- [ ] Botão deletar por row → `<Button variant="destructive" size="icon">`
- [ ] Modal → `<Dialog.Root>`
- [ ] Select event_type → `<Select.Root>`
- [ ] Select day_of_week → `<Select.Root>` (converter string→number)
- [ ] Select recurrence → `<Select.Root>`
- [ ] Input event_date → `<Input type="date">`
- [ ] Checkbox squads → `<Checkbox.Root>`
- [ ] Input min/max → `<Input type="number">`
- [ ] Verificar data-testids
- [ ] Rodar E2E tests
- [ ] Commit: `feat(ui): events page redesign com shadcn (#TASK-029)`
