# SPEC-SCHEDULE — Migração da Página de Escala para shadcn-svelte

**Arquivo alvo:** `src/routes/schedule/+page.svelte`  
**Status:** WAITING  
**Depende de:** TASK-024 (infra shadcn), TASK-025 (layout shell migrado)  
**Task de implementação:** TASK-030-FRONTEND-shadcn-schedule

---

## Descrição

A página de escala tem três zonas: (1) barra de controles com seletor de mês e botões, (2) estado vazio com SVG inline, (3) tabela pivot por evento com cards de evento. Esta migração é a mais conservadora do conjunto: a tabela `<table>` permanece em HTML nativo, os cards de evento viram `<Card.Root>`, os botões migram para `<Button>`, o SVG inline do empty state vira `<Icon>`, e o input de mês vira `<Input>`.

**Todo o bloco `<script>` permanece 100% inalterado.** O estado `selectedMonth`, `monthSchedule`, `groupedByEvent()`, `buildEventPivot()`, `handleGenerate`, `handleClear`, `handleCopy`, `handleExportCsv` etc. não são tocados.

---

## Componentes shadcn a instalar

```bash
pnpm dlx shadcn-svelte@latest add card button input label
```

| Componente | Import |
|---|---|
| `Card.*` | `import * as Card from "$lib/components/ui/card/index.js"` |
| `Button` | `import { Button } from "$lib/components/ui/button/index.js"` |
| `Input` | `import { Input } from "$lib/components/ui/input/index.js"` |
| `Label` | `import { Label } from "$lib/components/ui/label/index.js"` |
| `Icon` | `import { Icon } from "@iconify/svelte"` |

---

## O que NÃO muda

| Item | Razão |
|---|---|
| **Bloco `<script>` inteiro** | Toda a lógica de geração, agrupamento, pivot, export |
| `data-testid="schedule-page"` no div raiz | Obrigatório para testes E2E |
| `data-testid="btn-generate-schedule"` | Obrigatório para testes E2E |
| `data-testid="btn-copy-schedule"` | Obrigatório para testes E2E |
| `data-testid="btn-export-csv"` | Obrigatório para testes E2E |
| `bind:value={selectedMonth}` + `onchange={loadMonth}` | Binding e handler do seletor de mês |
| `disabled={!selectedMonth \|\| generating}` no botão gerar | Estado de desabilitado preservado |
| `{generating ? 'Gerando...' : '⚡ Gerar Escala do Mês'}` | Texto dinâmico preservado |
| Bloco `{#if loading}` / `{:else if !hasSchedule()}` / `{:else}` | Condicional de estados preservado |
| `<table>` com `<thead>`, `<tbody>`, `<tr>`, `<td>` | Estrutura de tabela HTML preservada |
| Classes Tailwind das células da tabela (`border border-slate-200`, etc.) | Estilização da tabela preservada |
| `{pivot.cells[squad][date].join(' · ')}` | Formatação de membros na célula preservada |
| `fmtDate(date)` nas colunas de datas | Formatação de datas preservada |
| Lógica `{#if pivot.squads.length === 0}` | Estado vazio da tabela preservado |

---

## Mapeamento de alterações

| Atual | Novo |
|---|---|
| `<div class="form-group flex-none"><label for="month-select">Mês</label><input class="input min-w-[160px]" type="month">` | `<div class="flex flex-col gap-1.5"><Label for="month-select">Mês</Label><Input id="month-select" type="month" class="min-w-[160px]" bind:value={selectedMonth} onchange={loadMonth} /></div>` |
| `<button class="btn btn-primary" data-testid="btn-generate-schedule" ...>` | `<Button data-testid="btn-generate-schedule" onclick={handleGenerate} disabled={!selectedMonth \|\| generating}>...</Button>` |
| `<button class="btn btn-secondary" onclick={handleClear}>🗑 Limpar Mês</button>` | `<Button variant="destructive" onclick={handleClear}><Icon icon="lucide:trash-2" class="size-4 mr-2" />Limpar Mês</Button>` |
| `<p class="text-slate-500">Carregando...</p>` | `<p class="text-muted-foreground">Carregando...</p>` |
| `<div class="flex flex-col items-center ... text-slate-500 gap-3">` (empty state) | `<div class="flex flex-col items-center ... text-muted-foreground gap-3">` |
| `<svg width="48" height="48" ...>` (ícone de clipboard inline) | `<Icon icon="lucide:clipboard-list" class="size-12 text-muted-foreground" />` |
| `<div class="card mb-6">` (card de evento na tabela) | `<Card.Root class="mb-6"><Card.Content class="pt-4">` |
| `<h3 class="text-base font-bold mb-4">{group.name}</h3>` | Permanece como `<h3>` interno ao `<Card.Content>` |
| `<button class="btn btn-secondary" data-testid="btn-copy-schedule">📋 Copiar Mês</button>` | `<Button variant="outline" data-testid="btn-copy-schedule" onclick={handleCopy}><Icon icon="lucide:clipboard" class="size-4 mr-2" />Copiar Mês</Button>` |
| `<button class="btn btn-secondary" data-testid="btn-export-csv">📤 Exportar CSV</button>` | `<Button variant="outline" data-testid="btn-export-csv" onclick={handleExportCsv}><Icon icon="lucide:download" class="size-4 mr-2" />Exportar CSV</Button>` |
| `text-slate-500` em textos secundários | `text-muted-foreground` |
| `text-slate-400` nas células vazias da tabela | `text-muted-foreground` |
| `bg-slate-100` / `border-slate-200` nos `<th>` da tabela | Manter classes Tailwind nativas (tabela não usa shadcn) |

---

## Código de referência

### Barra de controles

```svelte
<div class="flex gap-3 items-end flex-wrap mb-6">
  <div class="flex flex-col gap-1.5">
    <Label for="month-select">Mês</Label>
    <Input
      id="month-select"
      type="month"
      class="min-w-[160px]"
      bind:value={selectedMonth}
      onchange={loadMonth}
    />
  </div>
  <Button
    data-testid="btn-generate-schedule"
    onclick={handleGenerate}
    disabled={!selectedMonth || generating}
  >
    <Icon icon="lucide:zap" class="size-4 mr-2" />
    {generating ? 'Gerando...' : 'Gerar Escala do Mês'}
  </Button>
  {#if hasSchedule()}
    <Button variant="destructive" onclick={handleClear}>
      <Icon icon="lucide:trash-2" class="size-4 mr-2" />
      Limpar Mês
    </Button>
  {/if}
</div>
```

### Estado vazio (empty state)

```svelte
{:else if !hasSchedule()}
  <div class="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
    <Icon icon="lucide:clipboard-list" class="size-12" />
    <p class="text-sm">
      Nenhuma escala para {fmtMonthTitle(selectedMonth)}. Clique em "Gerar Escala do Mês".
    </p>
  </div>
```

### Card por evento (com tabela preservada)

```svelte
{#each groupedByEvent() as group}
  {@const pivot = buildEventPivot(group.occurrences)}
  <Card.Root class="mb-6">
    <Card.Content class="pt-6">
      <h3 class="text-base font-bold mb-4">{group.name}</h3>
      <div class="overflow-x-auto">
        <!-- Tabela HTML preservada integralmente -->
        <table class="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th class="px-3 py-2 text-left bg-slate-100 border border-slate-200 font-bold whitespace-nowrap min-w-[120px]">Time</th>
              {#each pivot.dates as date}
                <th class="px-3 py-2 text-left bg-slate-100 border border-slate-200 font-bold whitespace-nowrap">
                  {fmtDate(date)}
                </th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each pivot.squads as squad}
              <tr>
                <td class="px-3 py-2 border border-slate-200 font-semibold bg-slate-50 whitespace-nowrap">{squad}</td>
                {#each pivot.dates as date}
                  <td class="px-3 py-2 border border-slate-200">
                    {#if pivot.cells[squad][date]?.length}
                      {pivot.cells[squad][date].join(' · ')}
                    {:else}
                      <span class="text-muted-foreground">—</span>
                    {/if}
                  </td>
                {/each}
              </tr>
            {/each}
            {#if pivot.squads.length === 0}
              <tr>
                <td colspan={pivot.dates.length + 1} class="px-3 py-3 border border-slate-200 text-muted-foreground text-center">
                  Nenhuma alocação registrada
                </td>
              </tr>
            {/if}
          </tbody>
        </table>
      </div>
    </Card.Content>
  </Card.Root>
{/each}
```

### Botões de export

```svelte
<div class="flex gap-3 flex-wrap">
  <Button variant="outline" data-testid="btn-copy-schedule" onclick={handleCopy}>
    <Icon icon="lucide:clipboard" class="size-4 mr-2" />
    Copiar Mês
  </Button>
  <Button variant="outline" data-testid="btn-export-csv" onclick={handleExportCsv}>
    <Icon icon="lucide:download" class="size-4 mr-2" />
    Exportar CSV
  </Button>
</div>
```

---

## Checklist de implementação

- [ ] Adicionar imports: `Card`, `Button`, `Input`, `Label`, `Icon`
- [ ] Manter `data-testid="schedule-page"` no div raiz
- [ ] Manter `data-testid="btn-generate-schedule"` no botão gerar (com `disabled` preservado)
- [ ] Manter `data-testid="btn-copy-schedule"` no botão copiar
- [ ] Manter `data-testid="btn-export-csv"` no botão exportar
- [ ] Substituir `<div class="form-group">` + `<label>` + `<input class="input">` por `<Label>` + `<Input>`
- [ ] Substituir `<button class="btn btn-primary" data-testid="btn-generate-schedule">` por `<Button data-testid="btn-generate-schedule">`
- [ ] Substituir `<button class="btn btn-secondary">🗑 Limpar Mês</button>` por `<Button variant="destructive">` com `<Icon icon="lucide:trash-2">`
- [ ] Substituir SVG clipboard inline (48x48) por `<Icon icon="lucide:clipboard-list" class="size-12">`
- [ ] Substituir `<div class="card mb-6">` por `<Card.Root class="mb-6">` com `<Card.Content class="pt-6">`
- [ ] **Preservar** toda a estrutura `<table>` interna sem alteração
- [ ] Substituir `text-slate-500` por `text-muted-foreground`
- [ ] Substituir `text-slate-400` por `text-muted-foreground`
- [ ] Substituir botões de export por `<Button variant="outline">` com ícones Lucide
- [ ] `pnpm typecheck` sem erros
- [ ] Verificar que a tabela pivot renderiza corretamente com dados reais
- [ ] E2E: `btn-generate-schedule`, `btn-copy-schedule`, `btn-export-csv` ainda selecionáveis
