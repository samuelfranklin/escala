import { describe, it, expect } from 'vitest';
import { maskPhone, pivotSchedule, generateCsv, generateCopyText, formatDateLong, getNextEvent } from './index';
import type { ScheduleView } from '$lib/types';

describe('maskPhone', () => {
  it('string vazia retorna vazia', () => {
    expect(maskPhone('')).toBe('');
  });

  it('apenas letras/símbolos retorna vazia', () => {
    expect(maskPhone('abc!@#')).toBe('');
  });

  it('11 dígitos → (11) 99999-9999', () => {
    expect(maskPhone('11999999999')).toBe('(11) 99999-9999');
  });

  it('formatado já → mesmo resultado', () => {
    expect(maskPhone('(11) 99999-9999')).toBe('(11) 99999-9999');
  });

  it('3 dígitos → parcial sem fechar DDD', () => {
    expect(maskPhone('119')).toBe('(11) 9');
  });

  it('2 dígitos → só DDD aberto', () => {
    expect(maskPhone('11')).toBe('(11');
  });

  it('trunca em 11 dígitos', () => {
    expect(maskPhone('119999999991234')).toBe('(11) 99999-9999');
  });
});

// ── pivotSchedule ─────────────────────────────────────────────────────────────

const sampleView: ScheduleView = {
  event_id: 'e1',
  event_name: 'Culto Domingo',
  event_date: '2026-03-08',
  entries: [
    { entry_id: '1', squad_id: 's1', squad_name: 'Câmera',      member_id: 'm1', member_name: 'João' },
    { entry_id: '2', squad_id: 's1', squad_name: 'Câmera',      member_id: 'm2', member_name: 'Ana' },
    { entry_id: '3', squad_id: 's2', squad_name: 'Transmissão', member_id: 'm3', member_name: 'Pedro' },
  ],
};

describe('pivotSchedule', () => {
  it('entries vazia → columns [] e rows []', () => {
    const result = pivotSchedule({ ...sampleView, entries: [] });
    expect(result.columns).toEqual([]);
    expect(result.rows).toEqual([]);
  });

  it('2 squads e 3 membros → 2 colunas, 1 linha', () => {
    const { columns, rows } = pivotSchedule(sampleView);
    expect(columns).toEqual(['Câmera', 'Transmissão']);
    expect(rows).toHaveLength(1);
    expect(rows[0].squads['Câmera']).toEqual(['João', 'Ana']);
    expect(rows[0].squads['Transmissão']).toEqual(['Pedro']);
  });
});

// ── generateCsv ───────────────────────────────────────────────────────────────

describe('generateCsv', () => {
  it('gera CSV bem formado', () => {
    const pivot = pivotSchedule(sampleView);
    const csv = generateCsv(pivot);
    // Deve conter cabeçalho com Data, Câmera, Transmissão
    expect(csv).toContain('"Data"');
    expect(csv).toContain('"Câmera"');
    // Deve conter os membros
    expect(csv).toContain('João, Ana');
    expect(csv).toContain('"Pedro"');
  });

  it('escapa vírgulas e aspas nos nomes', () => {
    const tricky: ScheduleView = {
      ...sampleView,
      entries: [{ entry_id: '1', squad_id: 's1', squad_name: 'Âudio', member_id: 'm1', member_name: 'Silva, João "Zé"' }],
    };
    const { columns, rows } = pivotSchedule(tricky);
    const csv = generateCsv({ columns, rows });
    expect(csv).toContain('Silva, João ""Zé""');
  });
});

// ── generateCopyText ──────────────────────────────────────────────────────────

describe('generateCopyText', () => {
  it('texto legível para WhatsApp', () => {
    const pivot = pivotSchedule(sampleView);
    const text = generateCopyText(pivot, 'Culto Domingo');
    expect(text).toContain('Escala — Culto Domingo');
    expect(text).toContain('Câmera: João, Ana');
    expect(text).toContain('Transmissão: Pedro');
  });

  it('pivot vazio retorna string vazia', () => {
    expect(generateCopyText({ columns: [], rows: [] }, 'Evento')).toBe('');
  });
});

// ── formatDateLong ────────────────────────────────────────────────────────────

describe('formatDateLong', () => {
  it('formata data ISO em pt-BR longo', () => {
    const result = formatDateLong('2026-03-08');
    expect(result).toMatch(/domingo/i);
    expect(result).toMatch(/março/i);
    expect(result).toMatch(/2026/);
  });
});

// ── getNextEvent ──────────────────────────────────────────────────────────────

describe('getNextEvent', () => {
  const events = [
    { id: '1', event_date: '2026-01-01' },
    { id: '2', event_date: '2026-03-15' },
    { id: '3', event_date: '2026-03-08' },
  ];

  it('retorna o evento mais próximo (hoje ou futuro)', () => {
    const next = getNextEvent(events, '2026-03-08');
    expect(next?.id).toBe('3');
  });

  it('retorna null se todos estão no passado', () => {
    expect(getNextEvent(events, '2026-12-31')).toBeNull();
  });

  it('retorna null para array vazio', () => {
    expect(getNextEvent([], '2026-03-08')).toBeNull();
  });
});
