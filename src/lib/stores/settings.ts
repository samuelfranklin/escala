import { writable, derived, get } from 'svelte/store';
import type { ScheduleConfig, UpdateScheduleConfigDto } from '../types';
import { getScheduleConfig, updateScheduleConfig } from '../api/settings';

const _config = writable<ScheduleConfig | null>(null);
const _loading = writable(false);

export const settingsConfig = { subscribe: _config.subscribe };
export const settingsLoading = { subscribe: _loading.subscribe };

export const settings = {
  get config() { return get(_config); },
  get loading() { return get(_loading); },
  subscribe: _config.subscribe,

  async load() {
    _loading.set(true);
    try { _config.set(await getScheduleConfig()); }
    catch (e) { throw e; }
    finally { _loading.set(false); }
  },

  async save(dto: UpdateScheduleConfigDto) {
    _loading.set(true);
    try { _config.set(await updateScheduleConfig(dto)); }
    catch (e) { throw e; }
    finally { _loading.set(false); }
  },
};
