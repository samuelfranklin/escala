import { invoke } from '@tauri-apps/api/core';
import type { Availability, CreateAvailabilityDto } from '../types';

export const getAvailability = (memberId: string) => invoke<Availability[]>('get_availability', { memberId });
export const createAvailability = (dto: CreateAvailabilityDto) => invoke<Availability>('create_availability', { dto });
export const deleteAvailability = (id: string) => invoke<void>('delete_availability', { id });
