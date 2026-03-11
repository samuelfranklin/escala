# SPEC-COUPLES — Migração da Página de Restrições de Casais para shadcn-svelte

**Arquivo alvo:** `src/routes/couples/+page.svelte`  
**Status:** WAITING  
**Depende de:** TASK-024 (infra shadcn), TASK-025 (layout shell migrado)  
**Task de implementação:** TASK-032-FRONTEND-shadcn-couples

---

## Descrição

A página de casais é a mais simples do app: dois dropdowns de membro, um botão de adicionar restrição, e uma lista de pares com botão de remoção. A migração substitui os dois `<select class="input">` por `<Select.Root>`, o botão por `<Button>`, e os cards de par por `<Card.Root>`. O emoji `💑` do separador de par pode ser substituído por `<Icon icon="lucide:heart" />`.

**Todo o bloco `<script>` permanece 100% inalterado.**

---

## Componentes shadcn a instalar

```bash
pnpm dlx shadcn-svelte@latest add card button select
```

| Componente | Import |
|---|---|
| `Card.*` | `import * as Card from "$lib/components/ui/card/index.js"` |
| `Button` | `import { Button } from "$lib/components/ui/button/index.js"` |
| `Select.*` | `import * as Select from "$lib/components/ui/select/index.js"` |
| `Icon` | `import { Icon } from "@iconify/svelte"` |

---

## O que NÃO muda

| Item | Razão |
|---|---|
| **Bloco `<script>` inteiro** | `$state`, `onMount`, `getName`, `handleCreate` |
| `bind:value={memberA}` | Binding do membro A |
| `bind:value={memberB}` | Binding do membro B |
| `onclick={handleCreate}` | Handler de criação de restrição |
| `onclick={() => deleteCouple(c.id).then(...)` | Handler de remoção inline |
| `getName(c.member_a_id)` / `getName(c.member_b_id)` | Função de resolução de nome |
| Validação `memberA === memberB` no handler | Lógica de negócio preservada no script |

---

## Mapeamento de alterações

| Atual | Novo |
|---|---|
| `<select class="input max-w-[200px]" bind:value={memberA}>` | `<Select.Root type="single" value={memberA} onValueChange={(v) => { if (v) memberA = v; }}>` |
| `<option value="">Membro A...</option>` + options dos membros | `<Select.Value placeholder="Membro A..." />` + `<Select.Item>` por membro |
| `<select class="input max-w-[200px]" bind:value={memberB}>` | `<Select.Root type="single" value={memberB} onValueChange={(v) => { if (v) memberB = v; }}>` |
| `<option value="">Membro B...</option>` + options dos membros | `<Select.Value placeholder="Membro B..." />` + `<Select.Item>` por membro |
| `<button class="btn btn-primary" onclick={handleCreate}>Adicionar Restrição</button>` | `<Button onclick={handleCreate}>Adicionar Restrição</Button>` |
| `<div class="card flex justify-between items-center">` | `<Card.Root><Card.Content class="flex justify-between items-center p-4">` |
| `{getName(c.member_a_id)} 💑 {getName(c.member_b_id)}` | `{getName(c.member_a_id)} <Icon icon="lucide:heart" class="size-4 text-rose-500 inline mx-1" /> {getName(c.member_b_id)}` |
| `<button class="btn btn-danger btn-sm" onclick={...}>✕</button>` | `<Button variant="destructive" size="icon" class="size-7 shrink-0" onclick={...}><Icon icon="lucide:x" class="size-3.5" /></Button>` |
| `<p class="text-slate-500 mb-6">` | `<p class="text-muted-foreground mb-6">` |

---

## Código de referência

### Formulário de adição de restrição

```svelte
<div class="flex gap-3 mb-6 flex-wrap items-end">
  <!-- Membro A -->
  <Select.Root
    type="single"
    value={memberA}
    onValueChange={(v) => { if (v) memberA = v; }}
  >
    <Select.Trigger class="max-w-[200px]">
      <Select.Value placeholder="Membro A..." />
    </Select.Trigger>
    <Select.Content>
      {#each members as m (m.id)}
        <Select.Item value={m.id}>{m.name}</Select.Item>
      {/each}
    </Select.Content>
  </Select.Root>

  <!-- Membro B -->
  <Select.Root
    type="single"
    value={memberB}
    onValueChange={(v) => { if (v) memberB = v; }}
  >
    <Select.Trigger class="max-w-[200px]">
      <Select.Value placeholder="Membro B..." />
    </Select.Trigger>
    <Select.Content>
      {#each members as m (m.id)}
        <Select.Item value={m.id}>{m.name}</Select.Item>
      {/each}
    </Select.Content>
  </Select.Root>

  <Button onclick={handleCreate}>Adicionar Restrição</Button>
</div>
```

### Lista de pares

```svelte
<div class="flex flex-col gap-2">
  {#each couples as c (c.id)}
    <Card.Root>
      <Card.Content class="flex justify-between items-center p-4">
        <span class="flex items-center gap-1.5 text-sm font-medium">
          {getName(c.member_a_id)}
          <Icon icon="lucide:heart" class="size-4 text-rose-500" />
          {getName(c.member_b_id)}
        </span>
        <Button
          variant="destructive"
          size="icon"
          class="size-7 shrink-0"
          onclick={() => deleteCouple(c.id).then(() => getCouples().then(r => couples = r))}
        >
          <Icon icon="lucide:x" class="size-3.5" />
        </Button>
      </Card.Content>
    </Card.Root>
  {/each}
  {#if couples.length === 0}
    <p class="text-muted-foreground text-sm">Nenhuma restrição cadastrada.</p>
  {/if}
</div>
```

---

## Checklist de implementação

- [ ] Adicionar imports: `Card`, `Button`, `Select`, `Icon`
- [ ] Substituir `<select class="input" bind:value={memberA}>` por `<Select.Root type="single" value={memberA} onValueChange={...}>`
- [ ] Substituir `<select class="input" bind:value={memberB}>` por `<Select.Root type="single" value={memberB} onValueChange={...}>`
- [ ] Verificar que ambos os selects listam o mesmo array `members` com `<Select.Item value={m.id}>`
- [ ] Substituir `<button class="btn btn-primary" onclick={handleCreate}>` por `<Button onclick={handleCreate}>`
- [ ] Substituir `<div class="card flex justify-between ...">` por `<Card.Root><Card.Content>`
- [ ] Substituir emoji `💑` por `<Icon icon="lucide:heart" class="size-4 text-rose-500" />`
- [ ] Substituir `<button class="btn btn-danger btn-sm">✕</button>` por `<Button variant="destructive" size="icon">`
- [ ] Substituir `text-slate-500` por `text-muted-foreground`
- [ ] Adicionar estado vazio: `{#if couples.length === 0}<p class="text-muted-foreground text-sm">Nenhuma restrição cadastrada.</p>{/if}`
- [ ] `pnpm typecheck` sem erros
- [ ] Testar fluxo: selecionar A + B → adicionar → aparece na lista → remover
