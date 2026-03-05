import { invoke } from '@tauri-apps/api/core';
import type { Event, CreateEventDto, UpdateEventDto, EventSquad, EventSquadDto } from '../types';

export const getEvents = () => invoke<Event[]>('get_events');
export const getEvent = (id: string) => invoke<Event>('get_event', { id });
export const createEvent = (dto: CreateEventDto) => invoke<Event>('create_event', { dto });
export const updateEvent = (id: string, dto: UpdateEventDto) => invoke<Event>('update_event', { id, dto });
export const deleteEvent = (id: string) => invoke<void>('delete_event', { id });
export const getEventSquads = (eventId: string) => invoke<EventSquad[]>('get_event_squads', { eventId });
export const setEventSquads = (eventId: string, squads: EventSquadDto[]) => invoke<EventSquad[]>('set_event_squads', { eventId, squads });
