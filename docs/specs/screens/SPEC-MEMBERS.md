# SPEC-MEMBERS — Migração da Página de Membros para shadcn-svelte

**Arquivo alvo:** `src/routes/members/+page.svelte`  
**Status:** WAITING  
**Depende de:** TASK-024 (infra shadcn), TASK-025 (layout shell migrado)  
**Task de implementação:** TASK-027-FRONTEND-shadcn-members

---

## Descrição

A página de membros tem layout de duas colunas (lista à esquerda, detalhe/edição à direita) com modal de criação. Esta migração substitui: o campo de busca por `<Input>`, os cards de membro por `<Card.Root>`, o modal custom por `<Dialog.*>`, o `<select>` de rank por `<Select.*>`, todos os inputs por `<Input>` + `<Label>`, os badges inline de rank por `<Badge>`, e os botões por `<Button>`.

**Todo o bloco `<script>` permanece 100% inalterado.** Nenhuma linha de lógica de negócio, handlers ou `$state` é tocada.

---

## Componentes shadcn a instalar

```bash
pnpm dlx shadcn-svelte@latest add card input label button badge dialog select
```

| Componente | Import |
|---|---|
| `Card.*` | `import * as Card from "$lib/components/ui/card/index.js"` |
| `Input` | `import { Input } from "$lib/components/ui/input/index.js"` |
| `Label` | `import { Label } from "$lib/components/ui/label/index.js"` |
| `Button` | `import { Button } from "$lib/components/ui/button/index.js"` |
| `Badge` | `import { Badge } from "$lib/components/ui/badge/index.js"` |
| `Dialog.*` | `import * as Dialog from "$lib/components/ui/dialog/index.js"` |
| `Select.*` | `import * as Select from "$lib/components/ui/select/index.js"` |
| `Icon` | `import { Icon } from "@iconify/svelte"` |

---

## O que NÃO muda

| Item | Razão |
|---|---|
| **Bloco `<script>` inteiro** | Todos os `$state`, `$derived`, `onMount`, handlers |
| `data-testid="members-page"` no div raiz | Obrigatório — testes E2E selecionam por este atributo |
| `data-testid="member-row"` em cada linha | Obrigatório — testes E2E contam linhas |
| `data-testid="btn-new-member"` | Obrigatório — testes E2E clicam neste botão |
| `data-testid="btn-save-member"` | Obrigatório — testes E2E clicam neste botão |
| Layout `grid grid-cols-[360px_1fr] gap-6` | Estrutura de colunas preservada |
| `onclick={() => selectMember(m)}` em cada linha | Handler de seleção preservado |
| `onclick={() => showModal = true}` | Abertura do modal preservada |
| `bind:value={search}` no input de busca | Binding de estado preservado |
| `maskPhone()` no oninput do telefone | Utilitário de máscara preservado |
| `m.active ? '' : 'opacity-50'` | Estilo de membro inativo preservado |
| `selectedMember?.id === m.id ? 'ring-2 ring-blue-500' : ''` | Indicador de seleção DEVE ser preservado |
| `RANK_LABELS` e `RANK_COLORS` no script | Dicionários de exibição preservados |

---

## Mapeamento de alterações

| Atual | Novo |
|---|---|
| `<button class="btn btn-primary" data-testid="btn-new-member">` | `<Button data-testid="btn-new-member">+ Novo</Button>` |
| `<input class="input mb-3" type="search" ...>` | `<Input type="search" placeholder="Buscar membro..." bind:value={search} class="mb-3" />` |
| `<div class="card cursor-pointer p-3" data-testid="member-row">` | `<Card.Root data-testid="member-row" class="cursor-pointer p-3 ...">` |
| `ring-2 ring-blue-500` no card selecionado | `class:ring-2={selectedMember?.id===m.id} class:ring-blue-500={selectedMember?.id===m.id}` |
| `<span style="background:{RANK_COLORS[m.rank]}22;...">` (rank badge inline) | `<Badge style="background:{RANK_COLORS[m.rank]}22;color:{RANK_COLORS[m.rank]}">` |
| `<div class="fixed inset-0 bg-black/50 ...">` (modal) | `<Dialog.Root bind:open={showModal}>` |
| `<div class="card w-[400px]" role="dialog">` | `<Dialog.Content class="max-w-[400px]">` |
| `<h2 class="text-lg font-semibold mb-4">Novo Membro</h2>` | `<Dialog.Header><Dialog.Title>Novo Membro</Dialog.Title></Dialog.Header>` |
| `<div class="form-group"><label>Nome *</label><input class="input" ...>` | `<div class="grid gap-2"><Label for="name">Nome *</Label><Input id="name" ...></div>` |
| `<select id="rank" class="input" bind:value={form.rank}>` | `<Select.Root type="single" ...>` (ver código de referência) |
| `<button class="btn btn-secondary" onclick={() => showModal = false}>Cancelar</button>` | `<Dialog.Close><Button variant="outline">Cancelar</Button></Dialog.Close>` |
| `<button class="btn btn-primary" data-testid="btn-save-member">Salvar</button>` | `<Button data-testid="btn-save-member" onclick={handleCreate}>Salvar</Button>` |
| `<div class="form-group">` no formulário de edição inline | `<div class="grid gap-2">` |
| `<input class="input" ...>` no formulário de edição | `<Input ...>` com `<Label>` |
| `<button class="btn btn-primary" onclick={handleUpdate}>Salvar</button>` | `<Button onclick={handleUpdate}>Salvar</Button>` |
| `<button class="btn btn-secondary" onclick={() => editing = false}>Cancelar</button>` | `<Button variant="outline" onclick={() => editing = false}>Cancelar</Button>` |
| `<button class="btn btn-secondary btn-sm" onclick={() => startEdit(...)}>✏ Editar</button>` | `<Button variant="outline" size="sm" onclick={() => startEdit(selectedMember!)}>Editar</Button>` + `<Icon icon="lucide:pencil" />` |
| `<button class="btn btn-danger btn-sm" onclick={() => handleDelete(...)}>🗑 Remover</button>` | `<Button variant="destructive" size="sm" onclick={() => handleDelete(selectedMember!.id)}>Remover</Button>` |
| `<p class="text-sm">📞 {selectedMember.phone}</p>` | `<p class="text-sm flex items-center gap-2"><Icon icon="lucide:phone" class="size-3.5" />{selectedMember.phone}</p>` |
| `<p class="text-sm">✉ {selectedMember.email}</p>` | `<p class="text-sm flex items-center gap-2"><Icon icon="lucide:mail" class="size-3.5" />{selectedMember.email}</p>` |
| `<p class="text-sm">📷 {selectedMember.instagram}</p>` | `<p class="text-sm flex items-center gap-2"><Icon icon="lucide:instagram" class="size-3.5" />{selectedMember.instagram}</p>` |
| `<span class="badge badge-blue">{sq.name}</span>` (times do membro) | `<Badge variant="secondary">{sq.name}</Badge>` |
| `<span class="badge badge-red ml-2">Inativo</span>` | `<Badge variant="destructive" class="ml-2">Inativo</Badge>` |
| `<p class="text-3xl mb-2">👥</p>` (empty state) | `<Icon icon="lucide:users" class="size-12 text-muted-foreground mb-2" />` |

---

## Código de referência

### Campo de busca

```svelte
<Input type="search" placeholder="Buscar membro..." bind:value={search} class="mb-3" />
```

### Card de membro na lista (com ring de seleção)

```svelte
<Card.Root
  data-testid="member-row"
  class="cursor-pointer p-3 transition-all {m.active ? '' : 'opacity-50'} {selectedMember?.id===m.id ? 'ring-2 ring-blue-500' : ''}"
  onclick={() => selectMember(m)}
>
  <div class="flex justify-between items-center">
    <strong class="text-sm">{m.name}</strong>
    <Badge style="background:{RANK_COLORS[m.rank]}22;color:{RANK_COLORS[m.rank]}">
      {RANK_LABELS[m.rank] ?? m.rank}
    </Badge>
  </div>
  {#if !m.active}<p class="text-xs text-destructive mt-0.5">Inativo</p>{/if}
</Card.Root>
```

### Modal de criação com Dialog

```svelte
<Dialog.Root bind:open={showModal}>
  <Dialog.Content class="max-w-[400px]">
    <Dialog.Header>
      <Dialog.Title>Novo Membro</Dialog.Title>
    </Dialog.Header>
    <div class="flex flex-col gap-4 py-2">
      <div class="grid gap-2">
        <Label for="name">Nome *</Label>
        <Input id="name" name="name" bind:value={form.name} />
      </div>
      <div class="grid gap-2">
        <Label for="email">Email</Label>
        <Input id="email" type="email" bind:value={form.email} />
      </div>
      <div class="grid gap-2">
        <Label for="phone">Telefone</Label>
        <Input id="phone" placeholder="(11) 99999-9999"
          value={form.phone}
          oninput={(e) => { form.phone = maskPhone((e.target as HTMLInputElement).value); }} />
      </div>
      <div class="grid gap-2">
        <Label for="instagram">Instagram</Label>
        <Input id="instagram" placeholder="@usuario" bind:value={form.instagram} />
      </div>
      <div class="grid gap-2">
        <Label for="rank">Rank</Label>
        <Select.Root
          type="single"
          value={form.rank}
          onValueChange={(v) => { if (v) form.rank = v as typeof form.rank; }}
        >
          <Select.Trigger id="rank">
            <Select.Value placeholder="Selecione o rank" />
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="recruit">Recruta</Select.Item>
            <Select.Item value="member">Membro</Select.Item>
            <Select.Item value="trainer">Treinador</Select.Item>
            <Select.Item value="leader">Líder</Select.Item>
          </Select.Content>
        </Select.Root>
      </div>
    </div>
    <Dialog.Footer>
      <Dialog.Close>
        <Button variant="outline">Cancelar</Button>
      </Dialog.Close>
      <Button data-testid="btn-save-member" onclick={handleCreate}>Salvar</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
```

### Formulário de edição inline (Select para rank)

```svelte
<!-- Substituir apenas o <select> do editForm.rank -->
<div class="grid gap-2">
  <Label for="edit-rank">Rank</Label>
  <Select.Root
    type="single"
    value={editForm.rank}
    onValueChange={(v) => { if (v) editForm.rank = v as typeof editForm.rank; }}
  >
    <Select.Trigger id="edit-rank">
      <Select.Value placeholder="Selecione o rank" />
    </Select.Trigger>
    <Select.Content>
      <Select.Item value="recruit">Recruta</Select.Item>
      <Select.Item value="member">Membro</Select.Item>
      <Select.Item value="trainer">Treinador</Select.Item>
      <Select.Item value="leader">Líder</Select.Item>
    </Select.Content>
  </Select.Root>
</div>
```

### Painel de detalhes — informações de contato

```svelte
<div class="flex flex-col gap-2 mb-6">
  {#if selectedMember.phone}
    <p class="text-sm flex items-center gap-2">
      <Icon icon="lucide:phone" class="size-3.5 text-muted-foreground" />
      {selectedMember.phone}
    </p>
  {/if}
  {#if selectedMember.email}
    <p class="text-sm flex items-center gap-2">
      <Icon icon="lucide:mail" class="size-3.5 text-muted-foreground" />
      {selectedMember.email}
    </p>
  {/if}
  {#if selectedMember.instagram}
    <p class="text-sm flex items-center gap-2">
      <Icon icon="lucide:instagram" class="size-3.5 text-muted-foreground" />
      {selectedMember.instagram}
    </p>
  {/if}
</div>
```

---

## Checklist de implementação

- [ ] Adicionar imports: `Card`, `Input`, `Label`, `Button`, `Badge`, `Dialog`, `Select`, `Icon` ao `<script>` (NÃO remover imports existentes)
- [ ] Manter `data-testid="members-page"` no div raiz
- [ ] Manter `data-testid="member-row"` em cada linha de membro
- [ ] Manter `data-testid="btn-new-member"` no botão de novo membro
- [ ] Manter `data-testid="btn-save-member"` no botão de salvar do modal
- [ ] Substituir `<input class="input mb-3" type="search">` por `<Input type="search">`
- [ ] Substituir cards `.card` por `<Card.Root>` mantendo o `ring-2` condicional
- [ ] Substituir badges inline de rank por `<Badge style="...">` com os mesmos valores de cor
- [ ] Substituir modal custom (`fixed inset-0 bg-black/50`) por `<Dialog.Root bind:open={showModal}>`
- [ ] Substituir `<select class="input" bind:value={form.rank}>` por `<Select.Root type="single" ...>`
- [ ] Substituir `<select class="input" bind:value={editForm.rank}>` por `<Select.Root type="single" ...>` no formulário de edição
- [ ] Substituir todos `<input class="input">` por `<Input>` com `<Label>` nos padrão `<div class="grid gap-2">`
- [ ] Substituir botões `.btn .btn-primary` por `<Button>`
- [ ] Substituir botões `.btn .btn-secondary` por `<Button variant="outline">`
- [ ] Substituir botões `.btn .btn-danger` por `<Button variant="destructive">`
- [ ] Substituir emojis de contato (📞✉📷) por `<Icon>` correspondentes
- [ ] Substituir emoji 👥 do empty state por `<Icon icon="lucide:users">`
- [ ] Substituir `.badge .badge-blue` dos times associados por `<Badge variant="secondary">`
- [ ] Substituir `.badge .badge-red` (Inativo) por `<Badge variant="destructive">`
- [ ] `pnpm typecheck` sem erros
- [ ] E2E: `data-testid="member-row"` ainda selecionável, contagem de linhas funcional
- [ ] E2E: fluxo criar/editar/deletar membro funcional
