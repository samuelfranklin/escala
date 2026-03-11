# TASK-030 — Frontend: Schedule Page Redesign

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-025  
**Estimativa:** S (1–2h)

## Descrição

Reconstruir `src/routes/schedule/+page.svelte` com componentes shadcn-svelte. Toda a lógica do `<script>` permanece **100% inalterada**.

## Critérios de Aceite

- [ ] Month picker → `<Input type="month" bind:value={selectedMonth} class="w-40" />`
- [ ] Botão "Gerar Escala" → `<Button>` com loading state (disabled + Spinner quando `generating=true`)
- [ ] Botão "Limpar Escala" → `<Button variant="destructive">`
- [ ] Occurrences por evento: cada ocorrência em `<Card.Root>`
- [ ] Squad names → `<Badge variant="outline">`
- [ ] Member names na escala → texto simples ou `<span>`
- [ ] Empty state → card com mensagem + botão
- [ ] Loading → spinner ou texto "Carregando..."
- [ ] `pnpm dev` sem erros TypeScript

## Notas Técnicas

### Loading state em botão

```svelte
<Button onclick={handleGenerate} disabled={generating}>
  {#if generating}
    <Icon icon="lucide:loader-circle" class="animate-spin" />
    Gerando...
  {:else}
    <Icon icon="lucide:wand-sparkles" />
    Gerar Escala
  {/if}
</Button>
```

### Tabela de escala

A tabela HTML pode ser mantida semanticamente (thead/tbody/tr/td), apenas com classes Tailwind atualizadas. Evitar migrar para um componente Table do shadcn desnecessariamente — só se for P2 refactor.

### Referências

- [SPEC-SCHEDULE.md](../specs/screens/SPEC-SCHEDULE.md)

## Progresso

- [ ] Month input → `<Input type="month">`
- [ ] Botão Gerar → `<Button>` com loading
- [ ] Botão Limpar → `<Button variant="destructive">`
- [ ] Occurrences → `<Card.Root>` por ocorrência
- [ ] Squad badges → `<Badge variant="outline">`
- [ ] Empty state card
- [ ] Commit: `feat(ui): schedule page redesign com shadcn (#TASK-030)`
