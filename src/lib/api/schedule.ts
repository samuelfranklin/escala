import { invoke } from '@tauri-apps/api/core';
import type { ScheduleView } from '../types';

export const getSchedule = (eventId: string) => invoke<ScheduleView>('get_schedule', { eventId });
export const generateSchedule = (eventId: string) => invoke<ScheduleView>('generate_schedule', { eventId });
export const clearSchedule = (eventId: string) => invoke<void>('clear_schedule', { eventId });
