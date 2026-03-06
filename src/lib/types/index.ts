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
export type RecurrenceType = 'weekly' | 'biweekly' | 'monthly_1' | 'monthly_2' | 'monthly_3' | 'monthly_4';

export interface Event {
  id: string;
  name: string;
  /** Presente apenas para eventos especiais/treinamentos */
  event_date: string | null;
  event_type: EventType;
  /** 0=Dom, 1=Seg, 2=Ter, 3=Qua, 4=Qui, 5=Sex, 6=Sáb — apenas para eventos regulares */
  day_of_week: number | null;
  /** Frequência de recorrência — apenas para eventos regulares */
  recurrence: RecurrenceType | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateEventDto {
  name: string;
  /** Obrigatório para special/training; omitir para regular */
  event_date?: string;
  event_type?: EventType;
  day_of_week?: number;
  recurrence?: RecurrenceType;
  notes?: string;
}

export interface UpdateEventDto {
  name?: string;
  event_date?: string;
  event_type?: EventType;
  day_of_week?: number;
  recurrence?: RecurrenceType;
  notes?: string;
}

export interface EventSquad {
  squad_id: string;
  squad_name: string;
  min_members: number;
  max_members: number;
}

export interface EventSquadDto {
  squad_id: string;
  min_members: number;
  max_members: number;
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
  event_date: string | null;
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
