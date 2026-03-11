import { invoke } from '@tauri-apps/api/core';
import type { AppError } from '../types';

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: AppError };

export async function safeInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<ApiResult<T>> {
  try {
    const data = await invoke<T>(cmd, args);
    return { ok: true, data };
  } catch (e) {
    const error = e as AppError;
    return { ok: false, error };
  }
}
