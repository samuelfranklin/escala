# TASK-021 — Sistema de Toast (Feedback de Ações)

**Domínio:** FRONTEND  
**Status:** DONE  
**Prioridade:** P1 (alta — todas as telas precisam de feedback adequado; hoje só há texto de erro inline)  
**Depende de:** TASK-008 (design system)  
**Estimativa:** S (< 2h)

---

## Descrição

A spec (§8, Componentes-chave) define um componente `Toast` com variantes `success`, `warning`, `error`, `info`. Atualmente todas as telas mostram erros como texto `<p>` inline e não há feedback de sucesso em nenhuma operação.

O sistema de toast é um pré-requisito de UX para as tasks seguintes (TASK-019, TASK-020, TASK-022).

---

## Critérios de Aceite

### Store — `src/lib/stores/ui.ts` (estender o existente)

- [ ] Adicionar ao store `ui.ts` uma fila de toasts:

```typescript
export interface Toast {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  duration?: number; // ms, default 4000
}

// API pública:
export const toast = {
  success: (message: string, duration?: number) => void,
  warning: (message: string, duration?: number) => void,
  error:   (message: string, duration?: number) => void,
  info:    (message: string, duration?: number) => void,
  dismiss: (id: string) => void,
};
```

- [ ] Cada toast tem `id` gerado com `crypto.randomUUID()` (disponível no Tauri WebView)
- [ ] Auto-dismiss: após `duration` ms, remove da fila automaticamente via `setTimeout`
- [ ] `dismiss(id)` remove imediatamente (para botão ✕)

### Componente — `src/lib/components/ui/ToastContainer.svelte`

- [ ] Posicionado no canto inferior direito com `position: fixed; bottom: var(--space-6); right: var(--space-6); z-index: 100`
- [ ] Empilha múltiplos toasts verticalmente (gap `var(--space-2)`)
- [ ] Cada toast exibe:
  - Ícone à esquerda por tipo: ✓ (success), ⚠ (warning), ✗ (error), ℹ (info)
  - Borda esquerda colorida:
    - `success` → `--color-success: #4ade80`
    - `warning` → `--color-warning: #fbbf24`
    - `error`   → `--color-error: #f87171` (usar `--color-danger-500` se definido)
    - `info`    → `--color-info: #60a5fa`
  - Texto da mensagem
  - Botão ✕ para dismiss manual
- [ ] Animação de entrada: slide-in da direita (usando CSS `@keyframes`)
- [ ] Animação de saída: fade-out antes de remover do DOM

### Integração no Layout

- [ ] Montar `<ToastContainer />` em `src/routes/+layout.svelte` (uma única vez, fora do slot)

### Substituição dos erros inline existentes

- [ ] `src/routes/members/+page.svelte` — substituir `error` string por `toast.error(...)`
- [ ] `src/routes/squads/+page.svelte` — idem
- [ ] `src/routes/events/+page.svelte` — idem
- [ ] `src/routes/schedule/+page.svelte` — idem (manter exibição do erro de escala no painel, mas adicionar toast também)
- [ ] Adicionar `toast.success('Membro criado com sucesso!')` após operações de criação bem-sucedidas
- [ ] Adicionar `toast.success('Removido.')` após deleções bem-sucedidas

### Testes Vitest

- [ ] `toast.success('msg')` adiciona item com `type: 'success'` na fila
- [ ] `toast.dismiss(id)` remove o item da fila
- [ ] Após `duration` ms, item é removido automaticamente (usar `vi.useFakeTimers`)

---

## Notas Técnicas

- Não usar biblioteca de toast externa — implementar tudo em ~80 linhas conforme spec "sem CDNs externos em produção"
- O `ToastContainer` deve usar `{#each $toasts as t (t.id)}` com a `key` para que as animações funcionem corretamente
- Animação CSS simples é suficiente — não usar Svelte transitions complexas para não introduzir dependências
- O store de toast pode ser um `writable<Toast[]>` separado em `src/lib/stores/toast.ts` para manter `ui.ts` limpo, mas exportar via `src/lib/stores/index.ts`
