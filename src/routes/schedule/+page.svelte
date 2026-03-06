<script lang="ts">
  import { onMount } from 'svelte';
  import { getMonthSchedule, generateMonthSchedule, clearMonthSchedule } from '$lib/api/schedule';
  import { toast } from '$lib/stores/toast';
  import type { MonthScheduleView, OccurrenceSchedule } from '$lib/types';

  // Mês atual como padrão (formato YYYY-MM)
  const today = new Date();
  const defaultMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;

  let selectedMonth = $state(defaultMonth);
  let monthSchedule = $state<MonthScheduleView | null>(null);
  let loading = $state(false);
  let generating = $state(false);

  onMount(() => loadMonth());

  async function loadMonth() {
    if (!selectedMonth) return;
    loading = true;
    try { monthSchedule = await getMonthSchedule(selectedMonth); }
    catch { monthSchedule = null; }
    finally { loading = false; }
  }

  async function handleGenerate() {
    if (!selectedMonth) return;
    generating = true;
    try {
      monthSchedule = await generateMonthSchedule(selectedMonth);
      toast.success('Escala do mês gerada!');
    } catch (e: any) {
      toast.error(e.message || 'Erro ao gerar escala');
    } finally {
      generating = false;
    }
  }

  async function handleClear() {
    if (!selectedMonth || !confirm('Limpar escala do mês inteiro?')) return;
    await clearMonthSchedule(selectedMonth);
    monthSchedule = { month: selectedMonth, occurrences: [] };
    toast.success('Escala limpa.');
  }

  // Agrupa ocorrências por evento (mantendo ordem cronológica das datas)
  const groupedByEvent = $derived(() => {
    if (!monthSchedule || !monthSchedule.occurrences.length) return [];
    const map = new Map<string, { name: string; occurrences: OccurrenceSchedule[] }>();
    for (const occ of monthSchedule.occurrences) {
      if (!map.has(occ.event_id)) {
        map.set(occ.event_id, { name: occ.event_name, occurrences: [] });
      }
      map.get(occ.event_id)!.occurrences.push(occ);
    }
    return [...map.values()];
  });

  /** Para um grupo de ocorrências de um evento, constrói a tabela:
   *  cells[squad_name][occurrence_date] = memberNames[] */
  function buildEventPivot(occurrences: OccurrenceSchedule[]) {
    const dates = occurrences.map(o => o.occurrence_date);
    const squadsSet = new Set<string>();
    for (const occ of occurrences) {
      for (const e of occ.entries) squadsSet.add(e.squad_name);
    }
    const squads = [...squadsSet].sort();
    const cells: Record<string, Record<string, string[]>> = {};
    for (const sq of squads) {
      cells[sq] = {};
      for (const occ of occurrences) {
        cells[sq][occ.occurrence_date] = occ.entries
          .filter(e => e.squad_name === sq)
          .map(e => e.member_name);
      }
    }
    return { dates, squads, cells };
  }

  function fmtDate(iso: string) {
    const [, m, d] = iso.split('-');
    return `${d}/${m}`;
  }

  function fmtMonthTitle(ym: string) {
    const [y, m] = ym.split('-');
    const names = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                   'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
    return `${names[parseInt(m) - 1]} ${y}`;
  }

  const hasSchedule = $derived(() =>
    !!monthSchedule && monthSchedule.occurrences.length > 0
  );

  function handleExportCsv() {
    if (!monthSchedule) return;
    const lines: string[] = [`"Evento","Data","Time","Membros"`];
    for (const occ of monthSchedule.occurrences) {
      const squadsInOcc: Record<string, string[]> = {};
      for (const e of occ.entries) {
        (squadsInOcc[e.squad_name] ??= []).push(e.member_name);
      }
      for (const [sq, members] of Object.entries(squadsInOcc)) {
        const escape = (s: string) => `"${s.replace(/"/g, '""')}"`;
        lines.push([escape(occ.event_name), escape(fmtDate(occ.occurrence_date)), escape(sq), escape(members.join(', '))].join(','));
      }
    }
    const csv = lines.join('\r\n');
    const name = fmtMonthTitle(selectedMonth).replace(' ', '-').toLowerCase();
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `escala-${name}.csv`; a.click();
    URL.revokeObjectURL(url);
  }

  async function handleCopy() {
    if (!monthSchedule) return;
    const lines: string[] = [`📅 Escala — ${fmtMonthTitle(selectedMonth)}`, ''];
    for (const group of groupedByEvent()) {
      lines.push(`=== ${group.name} ===`);
      for (const occ of group.occurrences) {
        const d = new Date(occ.occurrence_date + 'T12:00:00');
        const weekday = d.toLocaleDateString('pt-BR', { weekday: 'long' });
        lines.push(`  ${fmtDate(occ.occurrence_date)} (${weekday})`);
        const squadsInOcc: Record<string, string[]> = {};
        for (const e of occ.entries) (squadsInOcc[e.squad_name] ??= []).push(e.member_name);
        for (const [sq, members] of Object.entries(squadsInOcc)) {
          lines.push(`    ${sq}: ${members.join(', ')}`);
        }
      }
      lines.push('');
    }
    await navigator.clipboard.writeText(lines.join('\n'));
    toast.success('Copiado!');
  }
</script>

<div data-testid="schedule-page">
  <h1 style="font-size:var(--text-2xl);font-weight:700;margin-bottom:var(--space-6)">Escala</h1>

  <!-- Controles: seletor de mês + botões -->
  <div style="display:flex;gap:var(--space-3);align-items:flex-end;flex-wrap:wrap;margin-bottom:var(--space-6)">
    <div class="form-group" style="flex:0 0 auto">
      <label for="month-select">Mês</label>
      <input id="month-select" class="input" type="month" bind:value={selectedMonth}
        style="min-width:160px"
        onchange={loadMonth} />
    </div>
    <button class="btn btn-primary" data-testid="btn-generate-schedule"
      onclick={handleGenerate} disabled={!selectedMonth || generating}>
      {generating ? 'Gerando...' : '⚡ Gerar Escala do Mês'}
    </button>
    {#if hasSchedule()}
      <button class="btn btn-secondary" onclick={handleClear}>🗑 Limpar Mês</button>
    {/if}
  </div>

  {#if loading}
    <p style="color:var(--text-muted)">Carregando...</p>

  {:else if !hasSchedule()}
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:var(--space-16) 0;color:var(--text-muted);gap:var(--space-3)">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
        <rect x="9" y="3" width="6" height="4" rx="1"/>
        <line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/>
      </svg>
      <p style="font-size:var(--text-sm)">
        Nenhuma escala para {fmtMonthTitle(selectedMonth)}. Clique em "⚡ Gerar Escala do Mês".
      </p>
    </div>

  {:else}
    <!-- Título do mês -->
    <h2 style="font-size:var(--text-xl);font-weight:700;margin-bottom:var(--space-6)">
      {fmtMonthTitle(selectedMonth)}
      <span style="font-size:var(--text-sm);font-weight:400;color:var(--text-muted);margin-left:var(--space-3)">
        {monthSchedule!.occurrences.length} {monthSchedule!.occurrences.length === 1 ? 'ocorrência' : 'ocorrências'}
      </span>
    </h2>

    <!-- Um cartão por evento -->
    {#each groupedByEvent() as group}
      {@const pivot = buildEventPivot(group.occurrences)}
      <div class="card" style="margin-bottom:var(--space-6)">
        <h3 style="font-size:var(--text-base);font-weight:700;margin-bottom:var(--space-4)">{group.name}</h3>
        <div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:var(--text-sm)">
            <thead>
              <tr>
                <th style="padding:var(--space-2) var(--space-3);text-align:left;background:var(--surface-2);border:1px solid var(--border);font-weight:700;white-space:nowrap;min-width:120px">Time</th>
                {#each pivot.dates as date}
                  <th style="padding:var(--space-2) var(--space-3);text-align:left;background:var(--surface-2);border:1px solid var(--border);font-weight:700;white-space:nowrap">
                    {fmtDate(date)}
                  </th>
                {/each}
              </tr>
            </thead>
            <tbody>
              {#each pivot.squads as squad}
                <tr>
                  <td style="padding:var(--space-2) var(--space-3);border:1px solid var(--border);font-weight:600;background:var(--surface-1);white-space:nowrap">{squad}</td>
                  {#each pivot.dates as date}
                    <td style="padding:var(--space-2) var(--space-3);border:1px solid var(--border)">
                      {#if pivot.cells[squad][date]?.length}
                        {pivot.cells[squad][date].join(' · ')}
                      {:else}
                        <span style="color:var(--text-muted)">—</span>
                      {/if}
                    </td>
                  {/each}
                </tr>
              {/each}
              {#if pivot.squads.length === 0}
                <tr>
                  <td colspan={pivot.dates.length + 1} style="padding:var(--space-3);border:1px solid var(--border);color:var(--text-muted);text-align:center">
                    Nenhuma alocação registrada
                  </td>
                </tr>
              {/if}
            </tbody>
          </table>
        </div>
      </div>
    {/each}

    <!-- Botões de export -->
    <div style="display:flex;gap:var(--space-3);flex-wrap:wrap">
      <button class="btn btn-secondary" data-testid="btn-copy-schedule" onclick={handleCopy}>📋 Copiar Mês</button>
      <button class="btn btn-secondary" data-testid="btn-export-csv" onclick={handleExportCsv}>📤 Exportar CSV</button>
    </div>
  {/if}
</div>

