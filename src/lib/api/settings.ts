import { invoke } from '@tauri-apps/api/core';
import type { ScheduleConfig, UpdateScheduleConfigDto } from '../types';

export const getScheduleConfig = () => invoke<ScheduleConfig>('get_schedule_config');
export const updateScheduleConfig = (dto: UpdateScheduleConfigDto) =>
  invoke<ScheduleConfig>('update_schedule_config', { dto });
