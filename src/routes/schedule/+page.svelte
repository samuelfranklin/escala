<script lang="ts">
  import { onMount } from 'svelte';
  import { getEvents } from '$lib/api/events';
  import { getSchedule, generateSchedule, clearSchedule } from '$lib/api/schedule';
  import { toast } from '$lib/stores/toast';
  import { pivotSchedule, generateCsv, generateCopyText } from '$lib/utils';
  import type { Event, ScheduleView } from '$lib/types';

  let events = $state<Event[]>([]);
  let selectedEventId = $state('');
  let schedule = $state<ScheduleView | null>(null);
  let loading = $state(false);
  let generating = $state(false);

  onMount(async () => { events = await getEvents(); });

  async function loadSchedule() {
    if (!selectedEventId) return;
    loading = true;
    try { schedule = await getSchedule(selectedEventId); }
    catch { schedule = null; }
    finally { loading = false; }
  }

  async function handleGenerate() {
    if (!selectedEventId) return;
    generating = true;
    try { schedule = await generateSchedule(selectedEventId); toast.success('Escala gerada!'); }
    catch (e: any) { toast.error(e.message || 'Erro ao gerar escala'); }
    finally { generating = false; }
  }

  async function handleClear() {
    if (!selectedEventId || !confirm('Limpar escala?')) return;
    await clearSchedule(selectedEventId);
    schedule = null;
  }

  const pivot = $derived(() => schedule ? pivotSchedule(schedule) : { columns: [], rows: [] });

  function handleExportCsv() {
    if (!schedule) return;
    const csv = generateCsv(pivot());
    const name = schedule.event_name.replace(/\s+/g, '-').toLowerCase();
    const filename = `escala-${name}-${schedule.event_date}.csv`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  }

  async function handleCopy() {
    if (!schedule) return;
    const text = generateCopyText(pivot(), schedule.event_name);
    await navigator.clipboard.writeText(text);
    toast.success('Copiado!');
  }
</script>

<div>
  <h1 style="font-size:var(--text-2xl);font-weight:700;margin-bottom:var(--space-6)">Escala</h1>

  <div style="display:flex;gap:var(--space-3);align-items:flex-end;flex-wrap:wrap;margin-bottom:var(--space-6)">
    <div class="form-group" style="flex:1;max-width:320px">
      <label for="event-select">Evento</label>
      <select id="event-select" class="input" bind:value={selectedEventId} onchange={loadSchedule}>
        <option value="">Selecione um evento...</option>
        {#each events as e (e.id)}<option value={e.id}>{e.name} — {e.event_date}</option>{/each}
      </select>
    </div>
    <button class="btn btn-primary" onclick={handleGenerate} disabled={!selectedEventId || generating}>
      {generating ? 'Gerando...' : '⚡ Gerar Escala'}
    </button>
    {#if schedule}
      <button class="btn btn-secondary" onclick={handleClear}>Limpar</button>
    {/if}
  </div>

  {#if !selectedEventId}
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:var(--space-16) 0;color:var(--text-muted);gap:var(--space-3)">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
        <rect x="9" y="3" width="6" height="4" rx="1"/>
        <line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/>
      </svg>
      <p style="font-size:var(--text-sm)">Selecione um evento para ver ou gerar a escala.</p>
    </div>

  {:else if loading}
    <p style="color:var(--text-muted)">Carregando...</p>

  {:else if schedule}
    <div>
      <h2 style="font-size:var(--text-lg);font-weight:600;margin-bottom:var(--space-4)">
        {schedule.event_name} — {schedule.event_date}
      </h2>

      {#if pivot().rows.length === 0}
        <p style="color:var(--text-muted)">Escala vazia. Clique em "Gerar Escala" para criar.</p>
      {:else}
        <!-- Tabela cruzada Data × Squad -->
        <div style="overflow-x:auto;margin-bottom:var(--space-6)">
          <table style="width:100%;border-collapse:collapse;font-size:var(--text-sm)">
            <thead>
              <tr>
                <th style="padding:var(--space-3) var(--space-4);text-align:left;background:var(--surface-2);border:1px solid var(--border);font-weight:700">Data</th>
                {#each pivot().columns as col}
                  <th style="padding:var(--space-3) var(--space-4);text-align:left;background:var(--surface-2);border:1px solid var(--border);font-weight:700;white-space:nowrap">{col}</th>
                {/each}
              </tr>
            </thead>
            <tbody>
              {#each pivot().rows as row}
                <tr>
                  <td style="padding:var(--space-3) var(--space-4);border:1px solid var(--border);white-space:nowrap;font-weight:600">
                    {row.eventDate.split('-').reverse().slice(0,2).join('/')}
                  </td>
                  {#each pivot().columns as col}
                    <td style="padding:var(--space-3) var(--space-4);border:1px solid var(--border)">
                      {#if row.squads[col]?.length}
                        {row.squads[col].join(' · ')}
                      {:else}
                        <span style="color:var(--text-muted)">—</span>
                      {/if}
                    </td>
                  {/each}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <!-- Botões de export -->
        <div style="display:flex;gap:var(--space-3);flex-wrap:wrap">
          <button class="btn btn-secondary" onclick={handleCopy}>📋 Copiar</button>
          <button class="btn btn-secondary" onclick={handleExportCsv}>📤 Exportar CSV</button>
          <button class="btn btn-secondary" disabled title="Em breve">📄 Exportar PDF</button>
        </div>
      {/if}
    </div>

  {:else}
    <p style="color:var(--text-muted)">Nenhuma escala para este evento ainda. Clique em "⚡ Gerar Escala".</p>
  {/if}
</div>

