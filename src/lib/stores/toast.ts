import { writable } from 'svelte/store';

export interface Toast {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  duration: number;
}

const { subscribe, update } = writable<Toast[]>([]);

function add(type: Toast['type'], message: string, duration = 4000) {
  const id = crypto.randomUUID();
  update((toasts) => [...toasts, { id, type, message, duration }]);
  setTimeout(() => dismiss(id), duration);
}

function dismiss(id: string) {
  update((toasts) => toasts.filter((t) => t.id !== id));
}

export const toasts = { subscribe };

export const toast = {
  success: (message: string, duration?: number) => add('success', message, duration),
  warning: (message: string, duration?: number) => add('warning', message, duration),
  error:   (message: string, duration?: number) => add('error',   message, duration),
  info:    (message: string, duration?: number) => add('info',    message, duration),
  dismiss,
};
