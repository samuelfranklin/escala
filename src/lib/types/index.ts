// TypeScript types mirroring Rust structs
// Will be completed in TASK-010

export interface Member {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  instagram?: string;
  rank: 'leader' | 'trainer' | 'member' | 'recruit';
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Squad {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Event {
  id: string;
  name: string;
  event_date: string;
  event_type: string;
  created_at: string;
  updated_at: string;
}
