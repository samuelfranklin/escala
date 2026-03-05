<script lang="ts">
  import { onMount } from 'svelte';
  import { getEvents, createEvent, deleteEvent, getEventSquads, setEventSquads } from '$lib/api/events';
  import { getSquads } from '$lib/api/squads';
  import type { Event, CreateEventDto, Squad, EventSquad, EventSquadDto } from '$lib/types';

  let events = $state<Event[]>([]);
  let allSquads = $state<Squad[]>([]);
  let selectedEvent = $state<Event | null>(null);
  let eventSquads = $state<EventSquad[]>([]);
  let eventSquadCounts = $state<Record<string, number>>({});
  let loading = $state(true);
  let saving = $state(false);
  let showModal = $state(false);
  let error = $state('');
  let form = $state<CreateEventDto>({ name: '', event_date: '', event_type: 'regular' });

  // Estado local de configuração dos squads no painel
  // squad_id → { enabled, min, max }
  let squadConfig = $state<Record<string, { enabled: boolean; min: number; max: number }>>({});

  onMount(load);

  async function load() {
    loading = true;
    const [evs, squads] = await Promise.all([getEvents(), getSquads()]);
    events = evs;
    allSquads = squads;
    // Busca contagem de squads configurados para todos os eventos
    const counts: Record<string, number> = {};
    await Promise.all(evs.map(async (e) => {
      const sq = await getEventSquads(e.id);
      counts[e.id] = sq.length;
    }));
    eventSquadCounts = counts;
    loading = false;
  }

  async function selectEvent(e: Event) {
    selectedEvent = e;
    eventSquads = await getEventSquads(e.id);
    // Inicializar squadConfig com base no que já está salvo
    const cfg: Record<string, { enabled: boolean; min: number; max: number }> = {};
    for (const sq of allSquads) {
      const saved = eventSquads.find(es => es.squad_id === sq.id);
      cfg[sq.id] = saved
        ? { enabled: true, min: saved.min_members, max: saved.max_members }
        : { enabled: false, min: 1, max: 3 };
    }
    squadConfig = cfg;
  }

  async function handleSaveSquads() {
    if (!selectedEvent) return;
    saving = true; error = '';
    try {
      const items: EventSquadDto[] = Object.entries(squadConfig)
        .filter(([, v]) => v.enabled)
        .map(([squad_id, v]) => ({ squad_id, min_members: v.min, max_members: v.max }));
      eventSquads = await setEventSquads(selectedEvent.id, items);
      // Atualizar cache de contagem do evento salvo
      eventSquadCounts = { ...eventSquadCounts, [selectedEvent.id]: eventSquads.length };
    } catch (e: any) {
      error = e.message || 'Erro ao salvar configuração';
    } finally {
      saving = false;
    }
  }

  async function handleCreate() {
    if (!form.name.trim() || !form.event_date) return;
    try {
      await createEvent(form);
      showModal = false;
      form = { name: '', event_date: '', event_type: 'regular' };
      await load();
    } catch (e: any) {
      error = e.message || 'Erro ao criar evento';
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Remover evento?')) return;
    try {
      await deleteEvent(id);
      if (selectedEvent?.id === id) selectedEvent = null;
      await load();
    } catch (e: any) {
      error = e.message || 'Erro ao remover';
    }
  }

  // Número de squads configurados para exibir no badge
  function squadCount(e: Event): number {
    return eventSquadCounts[e.id] ?? -1;
  }
</script>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-6)">
  <!-- Coluna esquerda: lista de eventos -->
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)">
      <h1 style="font-size:var(--text-2xl);font-weight:700">Eventos</h1>
      <button class="btn btn-primary" onclick={() => showModal = true}>+ Novo Evento</button>
    </div>

    {#if error}<p style="color:var(--color-danger-500);margin-bottom:var(--space-3)">{error}</p>{/if}

    {#if loading}
      <p>Carregando...</p>
    {:else if events.length === 0}
      <p style="color:var(--text-muted)">Nenhum evento cadastrado.</p>
    {:else}
      <div style="display:flex;flex-direction:column;gap:var(--space-2)">
        {#each events as e (e.id)}
          <div
            class="card"
            style="cursor:pointer;border-color:{selectedEvent?.id===e.id?'var(--color-primary-500)':'var(--surface-border)'}"
            onclick={() => selectEvent(e)}
          >
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div>
                <strong>{e.name}</strong>
                <span class="badge badge-blue" style="margin-left:var(--space-2)">{e.event_type}</span>
                <p style="font-size:var(--text-sm);color:var(--text-muted);margin-top:2px">{e.event_date}</p>
                {#if squadCount(e) > 0}
                  <span style="font-size:var(--text-xs);color:var(--color-success);margin-top:2px;display:block">● {squadCount(e)} {squadCount(e) === 1 ? 'time' : 'times'} configurado{squadCount(e) === 1 ? '' : 's'}</span>
                {:else if squadCount(e) === 0}
                  <span style="font-size:var(--text-xs);color:var(--color-danger-500);margin-top:2px;display:block">✗ Sem times — clique para configurar</span>
                {/if}
              </div>
              <button
                class="btn btn-danger btn-sm"
                onclick={(ev) => { ev.stopPropagation(); handleDelete(e.id); }}
              >✕</button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Coluna direita: painel de configuração de times -->
  {#if selectedEvent}
    <div>
      <h2 style="font-size:var(--text-xl);font-weight:600;margin-bottom:var(--space-1)">{selectedEvent.name}</h2>
      <p style="font-size:var(--text-sm);color:var(--text-muted);margin-bottom:var(--space-4)">Configurar times para esta escala</p>

      <div style="display:flex;flex-direction:column;gap:var(--space-2);margin-bottom:var(--space-4)">
        {#each allSquads as sq (sq.id)}
          <div class="card" style="padding:var(--space-3)">
            <label style="display:flex;align-items:center;gap:var(--space-3);cursor:pointer">
              <input
                type="checkbox"
                bind:checked={squadConfig[sq.id].enabled}
                style="width:16px;height:16px;cursor:pointer"
              />
              <span style="flex:1;font-weight:500">{sq.name}</span>
              {#if squadConfig[sq.id].enabled}
                <span style="display:flex;align-items:center;gap:var(--space-2);font-size:var(--text-sm)">
                  <span style="color:var(--text-muted)">mín</span>
                  <input
                    type="number" min="1" max="10"
                    class="input"
                    style="width:56px;padding:2px 6px;text-align:center"
                    bind:value={squadConfig[sq.id].min}
                    onclick={(e) => e.stopPropagation()}
                  />
                  <span style="color:var(--text-muted)">máx</span>
                  <input
                    type="number" min="1" max="10"
                    class="input"
                    style="width:56px;padding:2px 6px;text-align:center"
                    bind:value={squadConfig[sq.id].max}
                    onclick={(e) => e.stopPropagation()}
                  />
                </span>
              {/if}
            </label>
          </div>
        {/each}

        {#if allSquads.length === 0}
          <p style="color:var(--text-muted)">Nenhum time cadastrado. Cadastre times primeiro.</p>
        {/if}
      </div>

      <div style="display:flex;gap:var(--space-3)">
        <button class="btn btn-primary" onclick={handleSaveSquads} disabled={saving}>
          {saving ? 'Salvando...' : 'Salvar Configuração'}
        </button>
        <button class="btn btn-secondary" onclick={() => selectedEvent = null}>Fechar</button>
      </div>
    </div>
  {:else}
    <div style="display:flex;align-items:center;justify-content:center;color:var(--text-muted)">
      <p>Selecione um evento para configurar os times da escala.</p>
    </div>
  {/if}
</div>

{#if showModal}
  <div style="position:fixed;inset:0;background:rgb(0 0 0/0.5);display:flex;align-items:center;justify-content:center;z-index:50">
    <div class="card" style="width:400px">
      <h2 style="font-size:var(--text-lg);font-weight:600;margin-bottom:var(--space-4)">Novo Evento</h2>
      <div style="display:flex;flex-direction:column;gap:var(--space-3)">
        <div class="form-group"><label for="ev-name">Nome *</label><input id="ev-name" class="input" bind:value={form.name} /></div>
        <div class="form-group"><label for="ev-date">Data *</label><input id="ev-date" class="input" type="date" bind:value={form.event_date} /></div>
        <div class="form-group"><label for="ev-type">Tipo</label>
          <select id="ev-type" class="input" bind:value={form.event_type}>
            <option value="regular">Regular</option>
            <option value="special">Especial</option>
            <option value="training">Treinamento</option>
          </select>
        </div>
        <div style="display:flex;gap:var(--space-3);justify-content:flex-end">
          <button class="btn btn-secondary" onclick={() => showModal = false}>Cancelar</button>
          <button class="btn btn-primary" onclick={handleCreate}>Salvar</button>
        </div>
      </div>
    </div>
  </div>
{/if}
