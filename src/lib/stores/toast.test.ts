import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';

// Mock setTimeout/clearTimeout globalmente
vi.useFakeTimers();

// Importa após configurar mocks
const { toasts, toast } = await import('./toast');

describe('toast store', () => {
  beforeEach(() => {
    // Limpar todos os toasts entre testes
    toast.dismiss('__all__');
    // Rebuscar estado limpo: descartar qualquer pendente
    vi.clearAllTimers();
    get(toasts).forEach(t => toast.dismiss(t.id));
  });

  it('toast.success adiciona item com type success', () => {
    toast.success('tudo certo!');
    const all = get(toasts);
    expect(all).toHaveLength(1);
    expect(all[0].type).toBe('success');
    expect(all[0].message).toBe('tudo certo!');
  });

  it('toast.error adiciona item com type error', () => {
    toast.error('algo deu errado');
    const all = get(toasts);
    expect(all.some(t => t.type === 'error')).toBe(true);
  });

  it('toast.dismiss remove o item pelo id', () => {
    toast.info('oi');
    const id = get(toasts)[0].id;
    toast.dismiss(id);
    expect(get(toasts)).toHaveLength(0);
  });

  it('toast é removido automaticamente após duration', () => {
    toast.success('temporário', 1000);
    expect(get(toasts)).toHaveLength(1);
    vi.advanceTimersByTime(1001);
    expect(get(toasts)).toHaveLength(0);
  });

  it('toast não é removido antes do duration', () => {
    toast.warning('aguarda', 2000);
    vi.advanceTimersByTime(999);
    expect(get(toasts)).toHaveLength(1);
  });
});
