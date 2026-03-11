# TASK-031 — Frontend: Availability + Couples Pages Redesign

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P2  
**Depende de:** TASK-025  
**Estimativa:** S (1–2h)

## Descrição

Reconstruir as páginas `src/routes/availability/+page.svelte` e `src/routes/couples/+page.svelte` com componentes shadcn-svelte. São as duas páginas mais simples — sem modais complexos. Toda a lógica do `<script>` permanece **100% inalterada**.

## Critérios de Aceite

### Availability

- [ ] Member select → `<Select.Root type="single" onValueChange={(v) => { selectedMemberId = v; loadAvailability(); }}`
- [ ] Date input → `<Input type="date" bind:value={newDate} />`
- [ ] Reason input → `<Input bind:value={newReason} placeholder="Motivo (opcional)" />`
- [ ] Botão adicionar → `<Button>`
- [ ] Itens da lista → `<Card.Root>` ou `<div>` com estilo consistente
- [ ] Botão deletar entry → `<Button variant="destructive" size="sm">`

### Couples

- [ ] Member A select → `<Select.Root type="single" onValueChange={(v) => (memberA = v)}>`
- [ ] Member B select → `<Select.Root type="single" onValueChange={(v) => (memberB = v)}>`
- [ ] Botão adicionar casal → `<Button>`
- [ ] Lista de casais → `<Card.Root>` ou `<div>` por casal
- [ ] Botão deletar casal → `<Button variant="destructive" size="sm">`

## Notas Técnicas

### Gotcha crítico: Availability Select + onchange

A page atual usa `onchange={() => loadAvailability()}` no `<select>` nativo. No `<Select.Root>` shadcn, o equivalente é combinar no callback `onValueChange`:

```svelte
<Select.Root
  type="single"
  value={selectedMemberId}
  onValueChange={(v) => { selectedMemberId = v; loadAvailability(); }}
>
```

### Label para campos de formulário

```svelte
<div class="grid gap-2">
  <Label for="date">Data de indisponibilidade</Label>
  <Input id="date" type="date" bind:value={newDate} />
</div>
```

### Ícones sugeridos

- Casal: `lucide:heart` (cor rose)
- Disponibilidade: `lucide:calendar-x`
- Adicionar: `lucide:plus`
- Deletar: `lucide:trash-2`

### Referências

- [SPEC-AVAILABILITY.md](../specs/screens/SPEC-AVAILABILITY.md)
- [SPEC-COUPLES.md](../specs/screens/SPEC-COUPLES.md)

## Progresso

**Availability:**
- [ ] Member select → `<Select.Root>` com `loadAvailability()` no `onValueChange`
- [ ] Date input → `<Input type="date">`
- [ ] Reason input → `<Input>`
- [ ] Add button → `<Button>`
- [ ] Entry list → `<Card.Root>` ou divs
- [ ] Delete → `<Button variant="destructive" size="sm">`

**Couples:**
- [ ] Member A/B selects → `<Select.Root>`
- [ ] Add couple → `<Button>`
- [ ] Couple list → cards/badges
- [ ] Delete → `<Button variant="destructive" size="sm">`

- [ ] Commit: `feat(ui): availability + couples redesign com shadcn (#TASK-031)`
