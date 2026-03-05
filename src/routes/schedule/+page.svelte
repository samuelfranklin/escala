<script lang="ts">
  import { onMount } from 'svelte';
  import { getEvents } from '$lib/api/events';
  import { getSchedule, generateSchedule, clearSchedule } from '$lib/api/schedule';
  import type { Event, ScheduleView } from '$lib/types';

  let events = $state<Event[]>([]);
  let selectedEventId = $state('');
  let schedule = $state<ScheduleView | null>(null);
  let loading = $state(false);
  let generating = $state(false);
  let error = $state('');

  onMount(async () => { events = await getEvents(); });

  async function loadSchedule() {
    if (!selectedEventId) return;
    loading = true; error = '';
    try { schedule = await getSchedule(selectedEventId); }
    catch { schedule = null; }
    finally { loading = false; }
  }

  async function handleGenerate() {
    if (!selectedEventId) return;
    generating = true; error = '';
    try { schedule = await generateSchedule(selectedEventId); }
    catch (e: any) { error = e.message || 'Erro ao gerar escala'; }
    finally { generating = false; }
  }

  async function handleClear() {
    if (!selectedEventId || !confirm('Limpar escala?')) return;
    await clearSchedule(selectedEventId);
    schedule = null;
  }

  // Group entries by squad
  const bySquad = $derived(() => {
    if (!schedule) return [];
    const map = new Map<string, { squadName: string; members: string[] }>();
    for (const e of schedule.entries) {
      if (!map.has(e.squad_id)) map.set(e.squad_id, { squadName: e.squad_name, members: [] });
      map.get(e.squad_id)!.members.push(e.member_name);
    }
    return [...map.values()];
  });
</script>

<div>
  <h1 style="font-size:var(--text-2xl);font-weight:700;margin-bottom:var(--space-6)">Escala</h1>

  <div style="display:flex;gap:var(--space-3);align-items:flex-end;margin-bottom:var(--space-6)">
    <div class="form-group" style="flex:1;max-width:300px">
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

  {#if error}<p style="color:var(--color-danger-500);margin-bottom:var(--space-4)">{error}</p>{/if}

  {#if loading}<p>Carregando...</p>
  {:else if schedule}
    <div>
      <h2 style="font-size:var(--text-lg);font-weight:600;margin-bottom:var(--space-4)">{schedule.event_name} — {schedule.event_date}</h2>
      {#if bySquad().length === 0}
        <p style="color:var(--text-muted)">Escala vazia. Clique em "Gerar Escala" para criar.</p>
      {:else}
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:var(--space-4)">
          {#each bySquad() as group}
            <div class="card">
              <h3 style="font-size:var(--text-sm);font-weight:700;margin-bottom:var(--space-3);color:var(--color-primary-600)">{group.squadName}</h3>
              <ul style="list-style:none;display:flex;flex-direction:column;gap:var(--space-1)">
                {#each group.members as name}<li style="font-size:var(--text-sm)">{name}</li>{/each}
              </ul>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else if selectedEventId}
    <p style="color:var(--text-muted)">Nenhuma escala para este evento ainda.</p>
  {/if}
</div>
