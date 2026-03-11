<script lang="ts">
  import { toasts, toast as toastStore } from '$lib/stores/toast';

  const icons = { success: '✓', warning: '⚠', error: '✕', info: 'ℹ' };
  const colors = {
    success: '#4ade80',
    warning: '#fbbf24',
    error:   '#f87171',
    info:    '#60a5fa',
  };
</script>

<div class="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 pointer-events-none" aria-live="polite" aria-atomic="false">
  {#each $toasts as t (t.id)}
    <div
      class="flex items-center gap-3 px-4 py-3 bg-[var(--surface-elevated,var(--surface-card))] border border-[var(--surface-border)] border-l-4 rounded-md min-w-[280px] max-w-[420px] shadow-lg pointer-events-auto animate-[slide-in_0.2s_ease-out]"
      style="border-left-color:{colors[t.type]}"
    >
      <span class="text-base font-bold shrink-0" style="color:{colors[t.type]}">{icons[t.type]}</span>
      <span class="flex-1 text-sm text-[var(--text-primary)] leading-snug">{t.message}</span>
      <button
        class="bg-transparent border-none cursor-pointer text-slate-500 text-sm p-0 shrink-0 leading-none hover:text-[var(--text-primary)]"
        onclick={() => toastStore.dismiss(t.id)}
        aria-label="Fechar"
      >✕</button>
    </div>
  {/each}
</div>
