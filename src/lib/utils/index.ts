export function maskPhone(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 11);
  if (digits.length <= 2)  return digits.length ? `(${digits}` : '';
  if (digits.length <= 7)  return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}

// ── Schedule pivot ────────────────────────────────────────────────────────────

import type { ScheduleView } from '$lib/types';

export interface SchedulePivot {
  eventDate: string;
  squads: Record<string, string[]>;
}

export function pivotSchedule(view: ScheduleView): { columns: string[]; rows: SchedulePivot[] } {
  if (!view.entries.length) return { columns: [], rows: [] };

  const eventDate = view.event_date ?? 'recorrente';
  const columnsSet: string[] = [];
  const rowMap = new Map<string, Record<string, string[]>>();

  for (const entry of view.entries) {
    if (!columnsSet.includes(entry.squad_name)) columnsSet.push(entry.squad_name);
    if (!rowMap.has(eventDate)) rowMap.set(eventDate, {});
    const row = rowMap.get(eventDate)!;
    if (!row[entry.squad_name]) row[entry.squad_name] = [];
    row[entry.squad_name].push(entry.member_name);
  }

  const rows: SchedulePivot[] = [...rowMap.entries()].map(([eventDate, squads]) => ({
    eventDate,
    squads,
  }));

  return { columns: columnsSet, rows };
}

export function generateCsv(pivot: { columns: string[]; rows: SchedulePivot[] }): string {
  const escape = (s: string) => `"${s.replace(/"/g, '""')}"`;
  const header = ['Data', ...pivot.columns].map(escape).join(',');
  const lines = pivot.rows.map(row => {
    const date = escape(formatDate(row.eventDate));
    const cells = pivot.columns.map(col => escape((row.squads[col] ?? []).join(', ')));
    return [date, ...cells].join(',');
  });
  return [header, ...lines].join('\r\n');
}

export function generateCopyText(
  pivot: { columns: string[]; rows: SchedulePivot[] },
  eventName: string
): string {
  if (!pivot.rows.length) return '';
  const row = pivot.rows[0];
  const header = `Escala — ${eventName} (${formatDate(row.eventDate)})`;
  const lines = pivot.columns.map(col => {
    const members = (row.squads[col] ?? []).join(', ');
    return `${col}: ${members || '—'}`;
  });
  return [header, ...lines].join('\n');
}

function formatDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

// ── Date formatting ───────────────────────────────────────────────────────────

export function formatDateLong(iso: string): string {
  return new Date(iso + 'T00:00:00').toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function getNextEvent<T extends { event_date: string | null }>(
  events: T[],
  today: string
): T | null {
  const future = events
    .filter(e => e.event_date !== null && e.event_date >= today)
    .sort((a, b) => a.event_date!.localeCompare(b.event_date!));
  return future[0] ?? null;
}
