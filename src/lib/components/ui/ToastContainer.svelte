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

<div class="toast-container" aria-live="polite" aria-atomic="false">
  {#each $toasts as t (t.id)}
    <div class="toast toast-{t.type}" style="border-left-color:{colors[t.type]}">
      <span class="toast-icon" style="color:{colors[t.type]}">{icons[t.type]}</span>
      <span class="toast-message">{t.message}</span>
      <button class="toast-close" onclick={() => toastStore.dismiss(t.id)} aria-label="Fechar">✕</button>
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    bottom: var(--space-6);
    right: var(--space-6);
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    pointer-events: none;
  }
  .toast {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3) var(--space-4);
    background: var(--surface-elevated);
    border: 1px solid var(--surface-border);
    border-left-width: 4px;
    border-radius: 6px;
    min-width: 280px;
    max-width: 420px;
    box-shadow: 0 4px 12px rgb(0 0 0 / 0.3);
    pointer-events: all;
    animation: slide-in 0.2s ease-out;
  }
  .toast-icon {
    font-size: var(--text-base);
    font-weight: 700;
    flex-shrink: 0;
  }
  .toast-message {
    flex: 1;
    font-size: var(--text-sm);
    color: var(--text-primary);
    line-height: 1.4;
  }
  .toast-close {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-muted);
    font-size: var(--text-sm);
    padding: 0;
    flex-shrink: 0;
    line-height: 1;
  }
  .toast-close:hover { color: var(--text-primary); }
  @keyframes slide-in {
    from { transform: translateX(110%); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
  }
</style>
