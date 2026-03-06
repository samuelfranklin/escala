# SPEC-AVAILABILITY — Migração da Página de Disponibilidade para shadcn-svelte

**Arquivo alvo:** `src/routes/availability/+page.svelte`  
**Status:** WAITING  
**Depende de:** TASK-024 (infra shadcn), TASK-025 (layout shell migrado)  
**Task de implementação:** TASK-031-FRONTEND-shadcn-availability

---

## Descrição

A página de disponibilidade é uma das mais simples: um seletor de membro, campos de data e motivo, botão de adicionar, e uma lista de indisponibilidades com botão de remoção. A migração substitui o `<select>` nativo por `<Select.Root>`, os `<input class="input">` por `<Input>`, o botão por `<Button>`, e os cards da lista por `<Card.Root>`.

**Todo o bloco `<script>` permanece 100% inalterado.**

---

## Componentes shadcn a instalar

```bash
pnpm dlx shadcn-svelte@latest add card button input label select
```

| Componente | Import |
|---|---|
| `Card.*` | `import * as Card from "$lib/components/ui/card/index.js"` |
| `Button` | `import { Button } from "$lib/components/ui/button/index.js"` |
| `Input` | `import { Input } from "$lib/components/ui/input/index.js"` |
| `Label` | `import { Label } from "$lib/components/ui/label/index.js"` |
| `Select.*` | `import * as Select from "$lib/components/ui/select/index.js"` |
| `Icon` | `import { Icon } from "@iconify/svelte"` |

---

## O que NÃO muda

| Item | Razão |
|---|---|
| **Bloco `<script>` inteiro** | `$state`, `onMount`, `loadAvailability`, `handleAdd` |
| `bind:value={selectedMemberId}` | Binding do membro selecionado |
| `onchange={loadAvailability}` | Handler de mudança de seleção |
| `bind:value={newDate}` | Binding da data |
| `bind:value={newReason}` | Binding do motivo |
| `onclick={handleAdd}` | Handler de adicionar indisponibilidade |
| `onclick={() => deleteAvailability(a.id).then(loadAvailability)` | Handler de remoção inline |
| `{#if selectedMemberId}` | Condicional de exibição do formulário |
| `{a.unavailable_date}{#if a.reason} — {a.reason}{/if}` | Exibição condicional do motivo |

---

## Mapeamento de alterações

| Atual | Novo |
|---|---|
| `<select class="input max-w-[250px]" bind:value={selectedMemberId} onchange={loadAvailability}>` | `<Select.Root type="single" value={selectedMemberId} onValueChange={(v) => { if (v) { selectedMemberId = v; loadAvailability(); } }}>` |
| `<option value="">Selecione um membro...</option>` | `<Select.Value placeholder="Selecione um membro..." />` |
| `{#each members as m (m.id)}<option value={m.id}>{m.name}</option>{/each}` | `{#each members as m (m.id)}<Select.Item value={m.id}>{m.name}</Select.Item>{/each}` |
| `<input class="input max-w-[180px]" type="date" bind:value={newDate} />` | `<Input type="date" class="max-w-[180px]" bind:value={newDate} />` |
| `<input class="input max-w-[200px]" placeholder="Motivo (opcional)" bind:value={newReason} />` | `<Input class="max-w-[200px]" placeholder="Motivo (opcional)" bind:value={newReason} />` |
| `<button class="btn btn-primary" onclick={handleAdd}>Adicionar Indisponibilidade</button>` | `<Button onclick={handleAdd}>Adicionar Indisponibilidade</Button>` |
| `<div class="card flex justify-between items-center mb-2">` | `<Card.Root class="mb-2"><Card.Content class="flex justify-between items-center p-3">` |
| `<button class="btn btn-danger btn-sm" onclick={...}>✕</button>` | `<Button variant="destructive" size="icon" class="size-7 shrink-0" onclick={...}><Icon icon="lucide:x" class="size-3.5" /></Button>` |

---

## Atenção: Select shadcn vs native select com `onchange`

O `<Select.Root>` não emite um evento `change` nativo — usa `onValueChange`. O handler `loadAvailability` precisa ser chamado dentro do `onValueChange`:

```svelte
<!-- CORRETO -->
<Select.Root
  type="single"
  value={selectedMemberId}
  onValueChange={(v) => { if (v) { selectedMemberId = v; loadAvailability(); } }}
>
```

Isso preserva o comportamento do `onchange={loadAvailability}` original sem alterar a função `loadAvailability` no script.

---

## Código de referência

### Seletor de membro

```svelte
<div class="flex gap-3 mb-6">
  <Select.Root
    type="single"
    value={selectedMemberId}
    onValueChange={(v) => { if (v) { selectedMemberId = v; loadAvailability(); } }}
  >
    <Select.Trigger class="max-w-[250px]">
      <Select.Value placeholder="Selecione um membro..." />
    </Select.Trigger>
    <Select.Content>
      {#each members as m (m.id)}
        <Select.Item value={m.id}>{m.name}</Select.Item>
      {/each}
    </Select.Content>
  </Select.Root>
</div>
```

### Formulário de nova indisponibilidade

```svelte
{#if selectedMemberId}
  <div class="flex gap-3 mb-4 flex-wrap items-end">
    <div class="flex flex-col gap-1.5">
      <Label for="avail-date">Data</Label>
      <Input id="avail-date" type="date" class="max-w-[180px]" bind:value={newDate} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="avail-reason">Motivo</Label>
      <Input id="avail-reason" class="max-w-[200px]" placeholder="Motivo (opcional)" bind:value={newReason} />
    </div>
    <Button onclick={handleAdd}>Adicionar Indisponibilidade</Button>
  </div>

  {#each availability as a (a.id)}
    <Card.Root class="mb-2">
      <Card.Content class="flex justify-between items-center p-3">
        <span class="text-sm">
          {a.unavailable_date}{#if a.reason} — {a.reason}{/if}
        </span>
        <Button
          variant="destructive"
          size="icon"
          class="size-7 shrink-0"
          onclick={() => deleteAvailability(a.id).then(loadAvailability)}
        >
          <Icon icon="lucide:x" class="size-3.5" />
        </Button>
      </Card.Content>
    </Card.Root>
  {/each}
{/if}
```

---

## Checklist de implementação

- [ ] Adicionar imports: `Card`, `Button`, `Input`, `Label`, `Select`, `Icon`
- [ ] Substituir `<select class="input">` por `<Select.Root type="single" ...>` com `onValueChange` chamando `loadAvailability()`
- [ ] Manter `bind:value={selectedMemberId}` via `value={selectedMemberId}` + `onValueChange`
- [ ] Substituir `<input class="input" type="date">` por `<Input type="date">` com `<Label>`
- [ ] Substituir `<input class="input" placeholder="Motivo">` por `<Input>` com `<Label>`
- [ ] Substituir `<button class="btn btn-primary">` por `<Button>`
- [ ] Substituir `<div class="card ...">` de cada item por `<Card.Root><Card.Content>`
- [ ] Substituir `<button class="btn btn-danger btn-sm">✕</button>` por `<Button variant="destructive" size="icon">` + `<Icon icon="lucide:x">`
- [ ] Verificar que `{a.unavailable_date}{#if a.reason} — {a.reason}{/if}` permanece inalterado
- [ ] `pnpm typecheck` sem erros
- [ ] Testar fluxo: selecionar membro → lista carrega → adicionar data → item aparece → remover item
