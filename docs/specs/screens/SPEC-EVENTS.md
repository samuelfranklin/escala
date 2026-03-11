# SPEC-EVENTS — Migração da Página de Eventos para shadcn-svelte

**Arquivo alvo:** `src/routes/events/+page.svelte`  
**Status:** WAITING  
**Depende de:** TASK-024 (infra shadcn), TASK-025 (layout shell migrado)  
**Task de implementação:** TASK-029-FRONTEND-shadcn-events

---

## Descrição

A página de eventos tem layout de duas colunas: lista de eventos à esquerda e painel de configuração de times à direita. Esta migração substitui os cards de evento por `<Card.Root>`, os badges de tipo por `<Badge>`, o modal de criação por `<Dialog.*>`, os três `<select>` do formulário por `<Select.Root>`, os checkboxes de squad por `<Checkbox>` e os inputs numéricos de min/max por `<Input type="number">`.

**Todo o bloco `<script>` permanece 100% inalterado.** O estado `squadConfig` e todos os handlers permanecem intocados.

---

## Componentes shadcn a instalar

```bash
pnpm dlx shadcn-svelte@latest add card badge button dialog input label select checkbox
```

| Componente | Import |
|---|---|
| `Card.*` | `import * as Card from "$lib/components/ui/card/index.js"` |
| `Badge` | `import { Badge } from "$lib/components/ui/badge/index.js"` |
| `Button` | `import { Button } from "$lib/components/ui/button/index.js"` |
| `Dialog.*` | `import * as Dialog from "$lib/components/ui/dialog/index.js"` |
| `Input` | `import { Input } from "$lib/components/ui/input/index.js"` |
| `Label` | `import { Label } from "$lib/components/ui/label/index.js"` |
| `Select.*` | `import * as Select from "$lib/components/ui/select/index.js"` |
| `Checkbox` | `import { Checkbox } from "$lib/components/ui/checkbox/index.js"` |
| `Icon` | `import { Icon } from "@iconify/svelte"` |

---

## O que NÃO muda

| Item | Razão |
|---|---|
| **Bloco `<script>` inteiro** | Todos os `$state`, handlers, `DAYS`, `DAYS_FULL`, `RECURRENCE_LABELS`, etc. |
| `data-testid="events-page"` no div raiz | Obrigatório para testes E2E |
| `data-testid="event-row"` em cada linha | Obrigatório — testes E2E contam linhas |
| `data-testid="btn-new-event"` | Obrigatório — testes E2E |
| Layout `grid grid-cols-2 gap-6` | Estrutura de colunas preservada |
| `onclick={() => selectEvent(e)}` nos cards | Handler de seleção preservado |
| `e.stopPropagation()` no botão de delete | Prevenção de propagação preservada |
| `bind:checked={squadConfig[sq.id].enabled}` | Binding do checkbox preservado |
| `bind:value={squadConfig[sq.id].min}` / `.max` | Bindings dos inputs numéricos preservados |
| `onclick={(e) => e.stopPropagation()` nos inputs numéricos | Prevenção de clique no card preservada |
| `formatRecurrence(e)` e `squadCount(e)` | Funções de formatação preservadas |
| Indicadores `text-green-500` / `text-red-500` de squads configurados | Spans com classe Tailwind preservados |
| Condicional `{#if form.event_type === 'regular'}` no modal | Lógica de renderização condicional preservada |

---

## Mapeamento de alterações

| Atual | Novo |
|---|---|
| `<button class="btn btn-primary" data-testid="btn-new-event">` | `<Button data-testid="btn-new-event" onclick={() => showModal = true}>+ Novo Evento</Button>` |
| `<div data-testid="event-row" class="card cursor-pointer ...">` | `<Card.Root data-testid="event-row" class="cursor-pointer ...">` |
| `ring-2 ring-blue-500` no card selecionado | Classe condicional no `Card.Root` |
| `<span class="badge badge-blue ml-2">{e.event_type}</span>` | `<Badge variant="secondary" class="ml-2">{e.event_type}</Badge>` |
| `<button class="btn btn-danger btn-sm" onclick={(ev) => { ev.stopPropagation(); handleDelete(e.id); }}>✕</button>` | `<Button variant="destructive" size="icon" class="size-7" onclick={(ev) => { ev.stopPropagation(); handleDelete(e.id); }}><Icon icon="lucide:x" class="size-3.5" /></Button>` |
| `text-slate-500` em textos secundários | `text-muted-foreground` |
| `<div class="fixed inset-0 bg-black/50 ...">` (modal) | `<Dialog.Root bind:open={showModal}>` |
| `<h2 class="text-lg font-semibold mb-4">Novo Evento</h2>` | `<Dialog.Header><Dialog.Title>Novo Evento</Dialog.Title></Dialog.Header>` |
| `<select class="input" bind:value={form.event_type}>` | `<Select.Root type="single" value={form.event_type} onValueChange={...}>` |
| `<select class="input" bind:value={form.day_of_week}>` | `<Select.Root type="single" value={String(form.day_of_week)} onValueChange={(v) => form.day_of_week = Number(v)}>` |
| `<select class="input" bind:value={form.recurrence}>` | `<Select.Root type="single" value={form.recurrence} onValueChange={...}>` |
| `<input type="text" class="input" bind:value={form.name}>` | `<Input bind:value={form.name} />` com `<Label>` |
| `<input type="date" class="input" bind:value={form.event_date}>` | `<Input type="date" bind:value={form.event_date} />` |
| `<input type="checkbox" bind:checked={squadConfig[sq.id].enabled} class="w-4 h-4">` | `<Checkbox bind:checked={squadConfig[sq.id].enabled} />` com `<Label>` |
| `<input type="number" class="input w-14" bind:value={squadConfig[sq.id].min}>` | `<Input type="number" min="1" max="10" class="w-14" bind:value={squadConfig[sq.id].min} onclick={(e) => e.stopPropagation()} />` |
| `<input type="number" class="input w-14" bind:value={squadConfig[sq.id].max}>` | `<Input type="number" min="1" max="10" class="w-14" bind:value={squadConfig[sq.id].max} onclick={(e) => e.stopPropagation()} />` |
| `<button class="btn btn-primary" onclick={handleSaveSquads}>Salvar</button>` | `<Button onclick={handleSaveSquads} disabled={saving}>Salvar Configuração</Button>` |
| `<button class="btn btn-secondary" onclick={() => showModal = false}>Fechar</button>` | `<Dialog.Close><Button variant="outline">Fechar</Button></Dialog.Close>` |

---

## Código de referência

### Card de evento na lista

```svelte
<Card.Root
  data-testid="event-row"
  class="cursor-pointer transition-all {selectedEvent?.id===e.id ? 'ring-2 ring-blue-500' : ''}"
  onclick={() => selectEvent(e)}
>
  <Card.Content class="pt-4 pb-4">
    <div class="flex justify-between items-start">
      <div>
        <div class="flex items-center gap-2">
          <strong>{e.name}</strong>
          <Badge variant="secondary">{e.event_type}</Badge>
        </div>
        <p class="text-sm text-muted-foreground mt-0.5">{formatRecurrence(e)}</p>
        {#if squadCount(e) > 0}
          <span class="text-xs text-green-500 mt-0.5 block">
            ● {squadCount(e)} {squadCount(e) === 1 ? 'time' : 'times'} configurado{squadCount(e) === 1 ? '' : 's'}
          </span>
        {:else if squadCount(e) === 0}
          <span class="text-xs text-red-500 mt-0.5 block">✗ Sem times — clique para configurar</span>
        {/if}
      </div>
      <Button
        variant="destructive"
        size="icon"
        class="size-7 shrink-0"
        onclick={(ev) => { ev.stopPropagation(); handleDelete(e.id); }}
      >
        <Icon icon="lucide:x" class="size-3.5" />
      </Button>
    </div>
  </Card.Content>
</Card.Root>
```

### Modal de criação de evento

```svelte
<Dialog.Root bind:open={showModal}>
  <Dialog.Content class="max-w-[460px]">
    <Dialog.Header>
      <Dialog.Title>Novo Evento</Dialog.Title>
    </Dialog.Header>
    <div class="flex flex-col gap-4 py-2">
      <div class="grid gap-2">
        <Label for="event-name">Nome *</Label>
        <Input id="event-name" bind:value={form.name} />
      </div>
      <div class="grid gap-2">
        <Label>Tipo</Label>
        <Select.Root
          type="single"
          value={form.event_type}
          onValueChange={(v) => { if (v) form.event_type = v as typeof form.event_type; }}
        >
          <Select.Trigger>
            <Select.Value placeholder="Tipo do evento" />
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="regular">Regular (recorrente)</Select.Item>
            <Select.Item value="special">Especial (data única)</Select.Item>
          </Select.Content>
        </Select.Root>
      </div>

      {#if form.event_type === 'regular'}
        <div class="grid gap-2">
          <Label>Dia da semana</Label>
          <Select.Root
            type="single"
            value={String(form.day_of_week)}
            onValueChange={(v) => { if (v !== undefined) form.day_of_week = Number(v); }}
          >
            <Select.Trigger>
              <Select.Value placeholder="Selecione o dia" />
            </Select.Trigger>
            <Select.Content>
              {#each DAYS as day, i}
                <Select.Item value={String(i)}>{day}</Select.Item>
              {/each}
            </Select.Content>
          </Select.Root>
        </div>
        <div class="grid gap-2">
          <Label>Recorrência</Label>
          <Select.Root
            type="single"
            value={form.recurrence ?? ''}
            onValueChange={(v) => { if (v) form.recurrence = v as typeof form.recurrence; }}
          >
            <Select.Trigger>
              <Select.Value placeholder="Selecione a recorrência" />
            </Select.Trigger>
            <Select.Content>
              {#each Object.entries(RECURRENCE_LABELS) as [val, label]}
                <Select.Item value={val}>{label}</Select.Item>
              {/each}
            </Select.Content>
          </Select.Root>
        </div>
      {:else}
        <div class="grid gap-2">
          <Label for="event-date">Data</Label>
          <Input id="event-date" type="date" bind:value={form.event_date} />
        </div>
      {/if}
    </div>
    <Dialog.Footer>
      <Dialog.Close>
        <Button variant="outline">Cancelar</Button>
      </Dialog.Close>
      <Button onclick={handleCreate}>Criar Evento</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
```

### Painel de configuração de squads (coluna direita)

```svelte
<div class="flex flex-col gap-2 mb-4">
  {#each allSquads as sq (sq.id)}
    <Card.Root class="p-3">
      <div class="flex items-center gap-3">
        <Checkbox
          id="squad-{sq.id}"
          bind:checked={squadConfig[sq.id].enabled}
        />
        <Label for="squad-{sq.id}" class="flex-1 font-medium cursor-pointer">{sq.name}</Label>
        {#if squadConfig[sq.id].enabled}
          <div class="flex items-center gap-2 text-sm">
            <span class="text-muted-foreground">mín</span>
            <Input
              type="number" min="1" max="10"
              class="w-14 py-0.5 px-1.5 text-center h-8"
              bind:value={squadConfig[sq.id].min}
              onclick={(e) => e.stopPropagation()}
            />
            <span class="text-muted-foreground">máx</span>
            <Input
              type="number" min="1" max="10"
              class="w-14 py-0.5 px-1.5 text-center h-8"
              bind:value={squadConfig[sq.id].max}
              onclick={(e) => e.stopPropagation()}
            />
          </div>
        {/if}
      </div>
    </Card.Root>
  {/each}
</div>
<Button onclick={handleSaveSquads} disabled={saving} class="w-full">
  {saving ? 'Salvando...' : 'Salvar Configuração'}
</Button>
```

---

## Checklist de implementação

- [ ] Adicionar imports: `Card`, `Badge`, `Button`, `Dialog`, `Input`, `Label`, `Select`, `Checkbox`, `Icon`
- [ ] Manter `data-testid="events-page"` no div raiz
- [ ] Manter `data-testid="event-row"` em cada card de evento
- [ ] Manter `data-testid="btn-new-event"` no botão de novo evento
- [ ] Substituir cards `.card` por `<Card.Root>` mantendo `ring-2` condicional
- [ ] Substituir `.badge .badge-blue` por `<Badge variant="secondary">`
- [ ] Substituir botão `✕` delete por `<Button variant="destructive" size="icon">` + `<Icon icon="lucide:x">`
- [ ] Manter spans `text-green-500` / `text-red-500` dos indicadores de squads configurados (não substituir por Badge)
- [ ] Substituir modal custom por `<Dialog.Root bind:open={showModal}>`
- [ ] Substituir `<select>` de `event_type` por `<Select.Root type="single">`
- [ ] Substituir `<select>` de `day_of_week` por `<Select.Root>` com conversão `Number(v)` no `onValueChange`
- [ ] Substituir `<select>` de `recurrence` por `<Select.Root type="single">`
- [ ] Substituir `<input type="checkbox">` por `<Checkbox bind:checked={...}>` com `<Label>` vinculado por `id`
- [ ] Substituir `<input type="number" class="input w-14">` por `<Input type="number" class="w-14">` mantendo `onclick={(e) => e.stopPropagation()}`
- [ ] Substituir `.btn .btn-primary` por `<Button>`
- [ ] Substituir `.btn .btn-secondary` por `<Button variant="outline">`
- [ ] Substituir `.btn .btn-danger` por `<Button variant="destructive">`
- [ ] `pnpm typecheck` sem erros (atenção ao `day_of_week` — `Select.Root value` é `string`, converter para `Number` no handler)
- [ ] E2E: fluxo criar evento, configurar squads, salvar configuração funcional
