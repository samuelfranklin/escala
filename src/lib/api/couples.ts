import { invoke } from '@tauri-apps/api/core';
import type { Couple, CreateCoupleDto } from '../types';

export const getCouples = () => invoke<Couple[]>('get_couples');
export const createCouple = (dto: CreateCoupleDto) => invoke<Couple>('create_couple', { dto });
export const deleteCouple = (id: string) => invoke<void>('delete_couple', { id });
