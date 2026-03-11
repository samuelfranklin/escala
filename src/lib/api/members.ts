import { invoke } from '@tauri-apps/api/core';
import type { Member, CreateMemberDto, UpdateMemberDto } from '../types';

export const getMembers = () => invoke<Member[]>('get_members');
export const getMember = (id: string) => invoke<Member>('get_member', { id });
export const createMember = (dto: CreateMemberDto) => invoke<Member>('create_member', { dto });
export const updateMember = (id: string, dto: UpdateMemberDto) => invoke<Member>('update_member', { id, dto });
export const deleteMember = (id: string) => invoke<void>('delete_member', { id });
