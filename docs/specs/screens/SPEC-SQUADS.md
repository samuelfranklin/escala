# SPEC-SQUADS — Migração da Página de Times para shadcn-svelte

**Arquivo alvo:** `src/routes/squads/+page.svelte`  
**Status:** WAITING  
**Depende de:** TASK-024 (infra shadcn), TASK-025 (layout shell migrado)  
**Task de implementação:** TASK-028-FRONTEND-shadcn-squads

---

## Descrição

A página de times tem layout de duas colunas: lista de squads à esquerda e painel de gerenciamento de membros à direita. Os `<div class="card">` migram para `<Card.Root>`, o modal de criação de squad migra para `<Dialog.*>`, o dropdown de adicionar membro migra de `<select class="input">` para `<Select.Root>`, e todos os botões migram para `<Button>`.

**Todo o bloco `<script>` permanece 100% inalterado.**

---

## Componentes shadcn a instalar

```bash
pnpm dlx shadcn-svelte@latest add card badge button dialog input label select
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
| `Icon` | `import { Icon } from "@iconify/svelte"` |

---

## O que NÃO muda

| Item | Razão |
|---|---|
| **Bloco `<script>` inteiro** | Todos os handlers, `$state`, `$derived` |
| `data-testid="squads-page"` no div raiz | Obrigatório para testes E2E |
| `data-testid="squad-row"` em cada linha | Obrigatório — testes E2E contam linhas |
| `data-testid="btn-new-squad"` | Obrigatório — testes E2E |
| `data-testid="btn-save-squad"` | Obrigatório — testes E2E |
| `data-testid="select-add-member"` | Obrigatório — testes E2E |
| `data-testid="btn-add-member"` | Obrigatório — testes E2E |
| Layout `grid grid-cols-2 gap-6` | Estrutura de colunas preservada |
| `onclick={() => selectSquad(s)}` | Handler de seleção preservado |
| `e.stopPropagation()` no botão de delete dentro do card | Prevenção de propagação preservada |
| `$derived` `notInSquad` | Filtragem de membros disponíveis preservada |
| `bind:value={addMemberId}` no select | Binding de estado preservado |
| `bind:value={newName}` no input de nome | Binding de estado preservado |

---

## Mapeamento de alterações

| Atual | Novo |
|---|---|
| `<button class="btn btn-primary" data-testid="btn-new-squad">` | `<Button data-testid="btn-new-squad" onclick={() => showModal = true}>+ Novo Time</Button>` |
| `<div data-testid="squad-row" class="card cursor-pointer ...">` | `<Card.Root data-testid="squad-row" class="cursor-pointer p-4 ...">` |
| `ring-2 ring-blue-500` no card selecionado | Classe condicional preservada no `Card.Root` |
| `<button class="btn btn-danger btn-sm" onclick={(e) => { e.stopPropagation(); handleDelete(s.id); }}>✕</button>` | `<Button variant="destructive" size="icon" class="size-7" onclick={(e) => { e.stopPropagation(); handleDelete(s.id); }}><Icon icon="lucide:x" class="size-3.5" /></Button>` |
| `<select class="input" name="member_id" data-testid="select-add-member" bind:value={addMemberId}>` | `<Select.Root type="single" value={addMemberId} onValueChange={(v) => { if (v) addMemberId = v; }}>` com `data-testid` no `<Select.Trigger>` |
| `<button class="btn btn-primary" data-testid="btn-add-member">Adicionar Membro</button>` | `<Button data-testid="btn-add-member" onclick={handleAddMember}>Adicionar Membro</Button>` |
| `<div class="card flex justify-between items-center p-3">` (membro no squad) | `<Card.Root class="flex justify-between items-center p-3">` |
| `<button class="btn btn-secondary btn-sm" onclick={() => handleRemoveMember(m.id)}>Remover</button>` | `<Button variant="outline" size="sm" onclick={() => handleRemoveMember(m.id)}>Remover</Button>` |
| `<div class="fixed inset-0 bg-black/50 ...">` (modal) | `<Dialog.Root bind:open={showModal}>` |
| `<div class="card w-[360px]" role="dialog">` | `<Dialog.Content class="max-w-[360px]">` |
| `<h2 class="text-lg font-semibold mb-4">Novo Time</h2>` | `<Dialog.Header><Dialog.Title>Novo Time</Dialog.Title></Dialog.Header>` |
| `<div class="form-group mb-4"><label>Nome *</label><input>` | `<div class="grid gap-2"><Label for="squad-name">Nome *</Label><Input id="squad-name" ...></div>` |
| `<button class="btn btn-secondary">Cancelar</button>` | `<Dialog.Close><Button variant="outline">Cancelar</Button></Dialog.Close>` |
| `<button class="btn btn-primary" data-testid="btn-save-squad">Salvar</button>` | `<Button data-testid="btn-save-squad" onclick={handleCreate}>Salvar</Button>` |

---

## Atenção especial: `data-testid` no Select shadcn

O `<Select.Root>` do shadcn-svelte não renderiza um `<select>` nativo — ele usa um trigger custom. O `data-testid="select-add-member"` deve ser movido para o `<Select.Trigger>`:

```svelte
<Select.Trigger data-testid="select-add-member" class="flex-1">
  <Select.Value placeholder="Adicionar membro..." />
</Select.Trigger>
```

Se os testes E2E usarem `getByTestId('select-add-member')` e depois `.selectOption()`, precisará ser adaptado para clicar no trigger e depois no item. Verificar os testes E2E após a migração.

---

## Código de referência

### Lista de squads

```svelte
<div class="flex flex-col gap-2">
  {#each squads as s (s.id)}
    <Card.Root
      data-testid="squad-row"
      class="cursor-pointer transition-all {selectedSquad?.id===s.id ? 'ring-2 ring-blue-500' : ''}"
      onclick={() => selectSquad(s)}
    >
      <Card.Content class="flex justify-between items-center p-4">
        <div>
          <strong>{s.name}</strong>
          {#if s.description}<p class="text-sm text-muted-foreground">{s.description}</p>{/if}
        </div>
        <Button
          variant="destructive"
          size="icon"
          class="size-7 shrink-0"
          onclick={(e) => { e.stopPropagation(); handleDelete(s.id); }}
        >
          <Icon icon="lucide:x" class="size-3.5" />
        </Button>
      </Card.Content>
    </Card.Root>
  {/each}
</div>
```

### Painel direito — adicionar membro ao squad

```svelte
<div class="flex gap-2 mb-4">
  <Select.Root
    type="single"
    value={addMemberId}
    onValueChange={(v) => { if (v) addMemberId = v; }}
  >
    <Select.Trigger data-testid="select-add-member" class="flex-1">
      <Select.Value placeholder="Adicionar membro..." />
    </Select.Trigger>
    <Select.Content>
      {#each notInSquad as m (m.id)}
        <Select.Item value={m.id}>{m.name}</Select.Item>
      {/each}
    </Select.Content>
  </Select.Root>
  <Button data-testid="btn-add-member" onclick={handleAddMember}>
    Adicionar Membro
  </Button>
</div>
```

### Lista de membros do squad

```svelte
<div class="flex flex-col gap-2">
  {#each squadMembers as m (m.id)}
    <Card.Root>
      <Card.Content class="flex justify-between items-center p-3">
        <span>{m.name}</span>
        <Button variant="outline" size="sm" onclick={() => handleRemoveMember(m.id)}>
          Remover
        </Button>
      </Card.Content>
    </Card.Root>
  {/each}
  {#if squadMembers.length === 0}
    <p class="text-muted-foreground text-sm">Nenhum membro neste time.</p>
  {/if}
</div>
```

### Modal de criação de squad

```svelte
<Dialog.Root bind:open={showModal}>
  <Dialog.Content class="max-w-[360px]">
    <Dialog.Header>
      <Dialog.Title>Novo Time</Dialog.Title>
    </Dialog.Header>
    <div class="grid gap-2 py-2">
      <Label for="squad-name">Nome *</Label>
      <Input id="squad-name" name="name" bind:value={newName} />
    </div>
    <Dialog.Footer>
      <Dialog.Close>
        <Button variant="outline">Cancelar</Button>
      </Dialog.Close>
      <Button data-testid="btn-save-squad" onclick={handleCreate}>Salvar</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
```

---

## Checklist de implementação

- [ ] Adicionar imports: `Card`, `Badge`, `Button`, `Dialog`, `Input`, `Label`, `Select`, `Icon`
- [ ] Manter `data-testid="squads-page"` no div raiz
- [ ] Manter `data-testid="squad-row"` em cada card de squad
- [ ] Manter `data-testid="btn-new-squad"` no botão de novo time
- [ ] Manter `data-testid="btn-save-squad"` no botão salvar do modal
- [ ] Mover `data-testid="select-add-member"` para `<Select.Trigger>` (não em `<Select.Root>`)
- [ ] Manter `data-testid="btn-add-member"` no botão adicionar membro
- [ ] Substituir cards `.card` por `<Card.Root>` mantendo `ring-2` condicional
- [ ] Substituir botão `✕` de delete por `<Button variant="destructive" size="icon">` com `<Icon icon="lucide:x">`
- [ ] Substituir `<select class="input">` por `<Select.Root type="single">` com todos os membros como `<Select.Item>`
- [ ] Substituir modal custom por `<Dialog.Root bind:open={showModal}>`
- [ ] Substituir `<input class="input">` do nome do squad por `<Input>` com `<Label>`
- [ ] Substituir `.btn .btn-secondary` por `<Button variant="outline">`
- [ ] Substituir `.btn .btn-primary` por `<Button>`
- [ ] Substituir `.btn .btn-danger` por `<Button variant="destructive">`
- [ ] `pnpm typecheck` sem erros
- [ ] E2E: verificar se testes que usam `select-add-member` ainda passam (pode precisar de atualização nos testes)
- [ ] E2E: fluxo criar squad, adicionar membro, remover membro funcional
