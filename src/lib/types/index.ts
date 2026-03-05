// TypeScript types — mirror Rust structs exactly

export type MemberRank = 'leader' | 'trainer' | 'member' | 'recruit';

export interface Member {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  instagram: string | null;
  rank: MemberRank;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateMemberDto {
  name: string;
  email?: string;
  phone?: string;
  instagram?: string;
  rank?: MemberRank;
}

export interface UpdateMemberDto {
  name?: string;
  email?: string;
  phone?: string;
  instagram?: string;
  rank?: MemberRank;
  active?: boolean;
}

export interface Squad {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateSquadDto { name: string; description?: string; }
export interface UpdateSquadDto { name?: string; description?: string; }

export type EventType = 'regular' | 'special' | 'training';

export interface Event {
  id: string;
  name: string;
  event_date: string;
  event_type: EventType;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateEventDto {
  name: string;
  event_date: string;
  event_type?: EventType;
  notes?: string;
}

export interface UpdateEventDto {
  name?: string;
  event_date?: string;
  event_type?: EventType;
  notes?: string;
}

export interface ScheduleEntryView {
  entry_id: string;
  squad_id: string;
  squad_name: string;
  member_id: string;
  member_name: string;
}

export interface ScheduleView {
  event_id: string;
  event_name: string;
  event_date: string;
  entries: ScheduleEntryView[];
}

export interface Couple {
  id: string;
  member_a_id: string;
  member_b_id: string;
  created_at: string;
}

export interface CreateCoupleDto { member_a_id: string; member_b_id: string; }

export interface Availability {
  id: string;
  member_id: string;
  unavailable_date: string;
  reason: string | null;
  created_at: string;
}

export interface CreateAvailabilityDto {
  member_id: string;
  unavailable_date: string;
  reason?: string;
}

// API error shape from Rust AppError (serialized as tagged union)
export interface AppError {
  type: 'NotFound' | 'Validation' | 'Conflict' | 'Database' | 'Internal';
  message: string;
}
