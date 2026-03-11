import { invoke } from '@tauri-apps/api/core';
import type { MonthScheduleView, ScheduleView } from '../types';

export const getSchedule = (eventId: string) => invoke<ScheduleView>('get_schedule', { eventId });
export const generateSchedule = (eventId: string) => invoke<ScheduleView>('generate_schedule', { eventId });
export const clearSchedule = (eventId: string) => invoke<void>('clear_schedule', { eventId });

export const getMonthSchedule = (month: string) => invoke<MonthScheduleView>('get_month_schedule', { month });
export const generateMonthSchedule = (month: string) => invoke<MonthScheduleView>('generate_month_schedule', { month });
export const clearMonthSchedule = (month: string) => invoke<void>('clear_month_schedule', { month });
