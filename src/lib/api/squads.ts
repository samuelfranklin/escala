import { invoke } from '@tauri-apps/api/core';
import type { Squad, Member, CreateSquadDto, UpdateSquadDto } from '../types';

export const getSquads = () => invoke<Squad[]>('get_squads');
export const getSquad = (id: string) => invoke<Squad>('get_squad', { id });
export const createSquad = (dto: CreateSquadDto) => invoke<Squad>('create_squad', { dto });
export const updateSquad = (id: string, dto: UpdateSquadDto) => invoke<Squad>('update_squad', { id, dto });
export const deleteSquad = (id: string) => invoke<void>('delete_squad', { id });
export const getSquadMembers = (squadId: string) => invoke<Member[]>('get_squad_members', { squadId });
export const addMemberToSquad = (squadId: string, memberId: string, role = 'member') => invoke<void>('add_member_to_squad', { squadId, memberId, role });
export const removeMemberFromSquad = (squadId: string, memberId: string) => invoke<void>('remove_member_from_squad', { squadId, memberId });
