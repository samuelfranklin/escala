# TASK-027 — Frontend: Members Page Redesign

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-025  
**Estimativa:** M (2–4h)

## Descrição

Reconstruir `src/routes/members/+page.svelte` com componentes shadcn-svelte. Toda a lógica do `<script>` (API calls, $state, handlers) permanece **100% inalterada**. TODOS os `data-testid` devem ser preservados exatamente como estão.

## Critérios de Aceite

- [ ] `data-testid="members-page"` preservado no div raiz
- [ ] `data-testid="member-row"` preservado em cada item da lista
- [ ] `data-testid="btn-new-member"` preservado no botão de criação
- [ ] `data-testid="btn-save-member"` preservado no botão de salvar do modal
- [ ] Search field → `<Input type="search">`
- [ ] Member rows → `<Card.Root class="cursor-pointer">`
- [ ] Rank badge com cores → `<Badge>` com variante ou classe CSS por rank
- [ ] Modal criação → `<Dialog.Root bind:open={showModal}>`
- [ ] Select de rank (criação + edição) → `<Select.Root type="single" onValueChange={...}>`
- [ ] Labels em todos os campos de input → `<Label for="...">`
- [ ] Botões Editar/Remover → `<Button variant="outline" size="sm">` / `<Button variant="destructive" size="sm">`
- [ ] Emojis de contato (📞✉📷) → `<Icon icon="lucide:phone">`, `<Icon icon="lucide:mail">`, `<Icon icon="lucide:instagram">`
- [ ] Testes E2E passando (`pnpm playwright test`)

## Notas Técnicas

### Gotcha crítico: Select com Svelte 5 runes

O `<Select.Root>` do shadcn-svelte (baseado em Bits UI) **não suporta `bind:value` diretamente** no modo runes. Use `onValueChange`:

```svelte
<!-- CRIAR -->
<Select.Root
  type="single"
  value={form.rank}
  onValueChange={(v) => (form.rank = v as Member['rank'])}
>
  <Select.Trigger class="w-full">{RANK_LABELS[form.rank] ?? 'Selecione'}</Select.Trigger>
  <Select.Content>
    <Select.Item value="recruit">Recruta</Select.Item>
    <Select.Item value="member">Membro</Select.Item>
    <Select.Item value="trainer">Treinador</Select.Item>
    <Select.Item value="leader">Líder</Select.Item>
  </Select.Content>
</Select.Root>

<!-- EDITAR (mesma lógica) -->
<Select.Root
  type="single"
  value={editForm.rank ?? ''}
  onValueChange={(v) => (editForm.rank = v as Member['rank'])}
>
```

### Pattern de campo de formulário

```svelte
<div class="grid gap-2">
  <Label for="name">Nome *</Label>
  <Input id="name" bind:value={form.name} />
</div>
```

### Dialog programático (sem Trigger)

```svelte
<Dialog.Root bind:open={showModal}>
  <Dialog.Content class="sm:max-w-[400px]">
    <Dialog.Header>
      <Dialog.Title>Novo Membro</Dialog.Title>
    </Dialog.Header>
    <!-- campos -->
    <Dialog.Footer>
      <Dialog.Close>
        <Button variant="outline">Cancelar</Button>
      </Dialog.Close>
      <Button data-testid="btn-save-member" onclick={handleCreate}>Salvar</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
```

### Rank badge com cor

```svelte
<!-- Mapeamento de rank → variant shadcn ou classe Tailwind -->
const RANK_VARIANTS = {
  leader: 'bg-amber-100 text-amber-700',
  trainer: 'bg-violet-100 text-violet-700',
  member: 'bg-green-100 text-green-700',
  recruit: 'bg-gray-100 text-gray-600',
};

<Badge class={RANK_VARIANTS[m.rank]}>{RANK_LABELS[m.rank]}</Badge>
```

### Referências

- [SPEC-MEMBERS.md](../specs/screens/SPEC-MEMBERS.md)
- [PDR-SHADCN-001.md](../pdrs/PDR-SHADCN-001.md) — seção Select binding gotcha

## Progresso

- [ ] Search → `<Input type="search">`
- [ ] Member rows → `<Card.Root>`
- [ ] Rank badges → `<Badge>` com classe de cor
- [ ] Empty state → preservar com ícone Lucide
- [ ] Painel de detalhe: emojis → `<Icon>`
- [ ] Botões Editar/Remover → `<Button>` variant correto
- [ ] Modal criação → `<Dialog.Root>`
- [ ] Form criação: `<Input>` + `<Label>` + `<Select.Root>`
- [ ] Form edição inline: mesmos componentes
- [ ] Verificar todos os data-testids
- [ ] Rodar E2E tests
- [ ] Commit: `feat(ui): members page redesign com shadcn (#TASK-027)`
