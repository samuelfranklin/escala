# TASK-028 — Frontend: Squads Page Redesign

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-025  
**Estimativa:** M (2–4h)

## Descrição

Reconstruir `src/routes/squads/+page.svelte` com componentes shadcn-svelte. Toda a lógica do `<script>` permanece **100% inalterada**.

## Critérios de Aceite

- [ ] Squad list cards → `<Card.Root class="cursor-pointer">`
- [ ] Selected card com ring → `class:ring-2={selectedSquad?.id === s.id}` preservado
- [ ] Botão novo time → `<Button>`
- [ ] Modal criação → `<Dialog.Root bind:open={showModal}>`
- [ ] Input nome do time → `<Input bind:value={newName} />`
- [ ] Select para adicionar membro → `<Select.Root type="single" onValueChange={...}>`
- [ ] Membros do time → `<Badge variant="outline">` com botão X
- [ ] Botão remover membro → `<Button variant="ghost" size="icon">`
- [ ] Botão deletar time → `<Button variant="destructive" size="sm">`
- [ ] `pnpm dev` sem erros TypeScript

## Notas Técnicas

### Select de membro (adição)

```svelte
<Select.Root
  type="single"
  value={addMemberId}
  onValueChange={(v) => (addMemberId = v)}
>
  <Select.Trigger class="flex-1">
    {allMembers.find(m => m.id === addMemberId)?.name ?? 'Selecionar membro...'}
  </Select.Trigger>
  <Select.Content>
    {#each allMembers.filter(m => m.active) as member}
      <Select.Item value={member.id}>{member.name}</Select.Item>
    {/each}
  </Select.Content>
</Select.Root>
```

### Member chips no painel

```svelte
{#each squadMembers as m (m.id)}
  <div class="flex items-center gap-1">
    <Badge variant="outline">{m.name}</Badge>
    <Button variant="ghost" size="icon" class="size-5"
      onclick={() => handleRemoveMember(m.id)}>
      <Icon icon="lucide:x" class="size-3" />
    </Button>
  </div>
{/each}
```

### Referências

- [SPEC-SQUADS.md](../specs/screens/SPEC-SQUADS.md)

## Progresso

- [ ] Squad cards → `<Card.Root>`
- [ ] Painel detalhe de squad
- [ ] Modal criação com `<Input>`
- [ ] Select de membro → `<Select.Root>`
- [ ] Member chips with `<Badge>` + remove button
- [ ] Delete squad → `<Button variant="destructive">`
- [ ] Commit: `feat(ui): squads page redesign com shadcn (#TASK-028)`
