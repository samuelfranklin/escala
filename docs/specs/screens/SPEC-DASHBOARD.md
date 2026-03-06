# SPEC-DASHBOARD — Migração da Página Dashboard para shadcn-svelte

**Arquivo alvo:** `src/routes/dashboard/+page.svelte`  
**Status:** WAITING  
**Depende de:** TASK-024 (infra shadcn), TASK-025 (layout shell migrado)  
**Task de implementação:** TASK-026-FRONTEND-shadcn-dashboard

---

## Descrição

Substituir os três KPI cards com SVG inline, o card de próximo evento e o card de alertas por `<Card.*>` do shadcn-svelte. Os ícones SVG inline são substituídos por `<Icon />` do `@iconify/svelte`. O badge de `event_type` migra de `.badge .badge-blue` para `<Badge variant="secondary">`. O botão "Criar Evento" migra para `<Button>`.

**Todo o bloco `<script>` permanece 100% inalterado.**

---

## Componentes shadcn a instalar

```bash
pnpm dlx shadcn-svelte@latest add card badge button
```

| Componente | Import |
|---|---|
| `Card.*` | `import * as Card from "$lib/components/ui/card/index.js"` |
| `Badge` | `import { Badge } from "$lib/components/ui/badge/index.js"` |
| `Button` | `import { Button } from "$lib/components/ui/button/index.js"` |
| `Icon` | `import { Icon } from "@iconify/svelte"` |

---

## O que NÃO muda

| Item | Razão |
|---|---|
| **Bloco `<script>` inteiro** | Lógica de estado, `onMount`, chamadas API, deriveds |
| `data-testid="dashboard"` no div raiz | Obrigatório para testes E2E |
| `formatDateLong(nextEvent.event_date)` | Utilitário de formatação de data |
| `getNextEvent(es, today)` | Lógica de negócio |
| Todos os `href` para `/events` e `/squads` | Links de navegação preservados |
| Textos e lógica condicional (`{#if nextEvent}`, `{#if eventsWithoutSquads > 0}`, etc.) | Toda a lógica de renderização |
| `activeMembers()` derived | Permanece no script |

---

## Mapeamento de alterações

| Atual | Novo |
|---|---|
| `<div class="card flex items-center gap-4">` (KPI) | `<Card.Root><Card.Content class="flex items-center gap-4 pt-6">` |
| `<div class="w-11 h-11 rounded-lg bg-blue-50 ...">` + `<svg>` inline | `<div class="... bg-blue-50 ..."><Icon icon="lucide:users" class="text-blue-600 size-5" /></div>` |
| `<p class="text-3xl font-bold">` (número KPI) | Permanece; dentro de `<Card.Content>` |
| `<div class="card mb-8">` (próximo evento) | `<Card.Root class="mb-8"><Card.Content class="pt-6">` |
| `<span class="badge badge-blue mt-2">{nextEvent.event_type}</span>` | `<Badge variant="secondary" class="mt-2">{nextEvent.event_type}</Badge>` |
| `<a href="/events" class="btn btn-primary inline-block">+ Criar Evento</a>` | `<Button href="/events" class="mt-3">+ Criar Evento</Button>` |
| `<div class="card flex flex-col gap-3">` (alertas) | `<Card.Root><Card.Content class="flex flex-col gap-3 pt-6">` |
| `<div class="card flex items-center gap-3 text-green-600">` (tudo ok) | `<Card.Root class="border-green-200"><Card.Content class="flex items-center gap-3 pt-6 text-green-600">` |
| SVG check verde inline | `<Icon icon="lucide:check" class="size-5 shrink-0" />` |

### Mapeamento de ícones SVG inline → Lucide

| Card | SVG atual | Lucide novo |
|---|---|---|
| Membros | `<path d="M17 21v-2a4 4 0 00-4-4H5...">` | `<Icon icon="lucide:users" />` |
| Times | `<polygon points="12 2 2 7 12 12 22 7 12 2"/>` (layers) | `<Icon icon="lucide:layers" />` |
| Eventos | `<rect x="3" y="4" width="18" height="18" rx="2"/>` (calendar) | `<Icon icon="lucide:calendar" />` |
| Alerta OK | `<polyline points="20 6 9 17 4 12"/>` (check) | `<Icon icon="lucide:check" />` |

### Cores dos ícones KPI

| Card | Container bg | Icon color |
|---|---|---|
| Membros | `bg-blue-50` | `text-blue-600` |
| Times | `bg-violet-50` | `text-violet-600` |
| Eventos | `bg-yellow-50` | `text-yellow-700` |

---

## Código de referência

### Estrutura KPI cards

```svelte
<div class="grid grid-cols-3 gap-4 mb-8">
  <!-- KPI Membros -->
  <Card.Root>
    <Card.Content class="flex items-center gap-4 pt-6">
      <div class="w-11 h-11 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
        <Icon icon="lucide:users" class="size-5 text-blue-600" />
      </div>
      <div>
        <p class="text-3xl font-bold leading-none">{members.length}</p>
        <p class="text-xs font-semibold text-muted-foreground mt-0.5">Membros</p>
        <p class="text-xs text-muted-foreground">{activeMembers()} ativos</p>
      </div>
    </Card.Content>
  </Card.Root>

  <!-- KPI Times -->
  <Card.Root>
    <Card.Content class="flex items-center gap-4 pt-6">
      <div class="w-11 h-11 rounded-lg bg-violet-50 flex items-center justify-center shrink-0">
        <Icon icon="lucide:layers" class="size-5 text-violet-600" />
      </div>
      <div>
        <p class="text-3xl font-bold leading-none">{squads.length}</p>
        <p class="text-xs font-semibold text-muted-foreground mt-0.5">Times</p>
        <p class="text-xs text-muted-foreground">{squadsWithMembers} c/ membros</p>
      </div>
    </Card.Content>
  </Card.Root>

  <!-- KPI Eventos -->
  <Card.Root>
    <Card.Content class="flex items-center gap-4 pt-6">
      <div class="w-11 h-11 rounded-lg bg-yellow-50 flex items-center justify-center shrink-0">
        <Icon icon="lucide:calendar" class="size-5 text-yellow-700" />
      </div>
      <div>
        <p class="text-3xl font-bold leading-none">{events.length}</p>
        <p class="text-xs font-semibold text-muted-foreground mt-0.5">Eventos</p>
        <p class="text-xs text-muted-foreground">{eventsThisMonth} este mês</p>
      </div>
    </Card.Content>
  </Card.Root>
</div>
```

### Próximo evento card

```svelte
{#if nextEvent}
  <Card.Root class="mb-8">
    <Card.Content class="pt-6">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-lg font-bold">{nextEvent.name}</p>
          <p class="text-sm text-muted-foreground mt-0.5">
            {nextEvent.event_date ? formatDateLong(nextEvent.event_date) : ''}
          </p>
          <Badge variant="secondary" class="mt-2">{nextEvent.event_type}</Badge>
        </div>
        {#if nextEventSquads.length > 0}
          <p class="text-sm text-green-600 whitespace-nowrap font-semibold">
            ✓ {nextEventSquads.length} {nextEventSquads.length === 1 ? 'time' : 'times'} configurado{nextEventSquads.length > 1 ? 's' : ''}
          </p>
        {:else}
          <a href="/events" class="text-sm text-amber-700 font-semibold whitespace-nowrap no-underline">
            ⚠ Sem times — Configurar →
          </a>
        {/if}
      </div>
    </Card.Content>
  </Card.Root>
{:else}
  <Card.Root class="mb-8">
    <Card.Content class="flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
      <p class="mb-3">Nenhum evento próximo.</p>
      <Button href="/events">+ Criar Evento</Button>
    </Card.Content>
  </Card.Root>
{/if}
```

### Alertas card

```svelte
{#if eventsWithoutSquads === 0 && membersWithoutSquad === 0}
  <Card.Root class="border-green-200">
    <Card.Content class="flex items-center gap-3 pt-6 text-green-600">
      <Icon icon="lucide:check" class="size-5 shrink-0" />
      <p class="text-sm font-semibold">Tudo configurado!</p>
    </Card.Content>
  </Card.Root>
{:else}
  <Card.Root>
    <Card.Content class="flex flex-col gap-3 pt-6">
      {#if eventsWithoutSquads > 0}
        <div class="flex items-center justify-between gap-4">
          <p class="text-sm text-amber-700">
            ⚠ {eventsWithoutSquads} {eventsWithoutSquads === 1 ? 'evento sem times configurados' : 'eventos sem times configurados'}
          </p>
          <a href="/events" class="text-sm font-semibold text-blue-600 no-underline whitespace-nowrap">Corrigir →</a>
        </div>
      {/if}
      {#if membersWithoutSquad > 0}
        <div class="flex items-center justify-between gap-4">
          <p class="text-sm text-amber-700">
            ⚠ {membersWithoutSquad} {membersWithoutSquad === 1 ? 'membro ativo sem time' : 'membros ativos sem time'}
          </p>
          <a href="/squads" class="text-sm font-semibold text-blue-600 no-underline whitespace-nowrap">Corrigir →</a>
        </div>
      {/if}
    </Card.Content>
  </Card.Root>
{/if}
```

---

## Checklist de implementação

- [ ] Adicionar imports: `Card`, `Badge`, `Button`, `Icon` — remover nenhum import existente do `<script>`
- [ ] Manter `data-testid="dashboard"` no div raiz
- [ ] Substituir 3 KPI `<div class="card">` por `<Card.Root><Card.Content>` com `<Icon>` correspondente
- [ ] Substituir SVG inline de membros por `<Icon icon="lucide:users" />`
- [ ] Substituir SVG inline de times por `<Icon icon="lucide:layers" />`
- [ ] Substituir SVG inline de eventos por `<Icon icon="lucide:calendar" />`
- [ ] Substituir SVG inline de check por `<Icon icon="lucide:check" />`
- [ ] Substituir `.badge .badge-blue` do `event_type` por `<Badge variant="secondary">`
- [ ] Substituir `<a class="btn btn-primary">+ Criar Evento</a>` por `<Button href="/events">`
- [ ] Substituir card de alerta "OK" por `<Card.Root class="border-green-200">`
- [ ] Substituir card de alertas com itens por `<Card.Root><Card.Content class="flex flex-col gap-3">`
- [ ] Verificar: headings `<h1>` e `<h2>` com classe `text-slate-500` substituem por `text-muted-foreground`
- [ ] `pnpm typecheck` sem erros
- [ ] Visual: cards com sombra e borda padrão do shadcn visíveis
