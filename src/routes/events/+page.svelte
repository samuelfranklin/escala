<script lang="ts">
  import { onMount } from 'svelte';
  import { getEvents, createEvent, deleteEvent, getEventSquads, setEventSquads } from '$lib/api/events';
  import { getSquads } from '$lib/api/squads';
  import { toast } from '$lib/stores/toast';
  import type { Event, CreateEventDto, Squad, EventSquad, EventSquadDto, RecurrenceType } from '$lib/types';

  let events = $state<Event[]>([]);
  let allSquads = $state<Squad[]>([]);
  let selectedEvent = $state<Event | null>(null);
  let eventSquads = $state<EventSquad[]>([]);
  let eventSquadCounts = $state<Record<string, number>>({});
  let loading = $state(true);
  let saving = $state(false);
  let showModal = $state(false);
  let form = $state<CreateEventDto>({ name: '', event_type: 'regular', day_of_week: 0, recurrence: 'weekly' });

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
    const squads = await getEventSquads(e.id);
    // Montar squadConfig antes de exibir o painel para evitar acesso a chaves inexistentes
    const cfg: Record<string, { enabled: boolean; min: number; max: number }> = {};
    for (const sq of allSquads) {
      const saved = squads.find(es => es.squad_id === sq.id);
      cfg[sq.id] = saved
        ? { enabled: true, min: saved.min_members, max: saved.max_members }
        : { enabled: false, min: 1, max: 3 };
    }
    eventSquads = squads;
    squadConfig = cfg;
    selectedEvent = e; // atribuído por último — painel só renderiza com config pronta
  }

  async function handleSaveSquads() {
    if (!selectedEvent) return;
    saving = true;
    try {
      const items: EventSquadDto[] = Object.entries(squadConfig)
        .filter(([, v]) => v.enabled)
        .map(([squad_id, v]) => ({ squad_id, min_members: v.min, max_members: v.max }));
      eventSquads = await setEventSquads(selectedEvent.id, items);
      eventSquadCounts = { ...eventSquadCounts, [selectedEvent.id]: eventSquads.length };
      toast.success('Configuração salva!');
    } catch (e: any) {
      toast.error(e.message || 'Erro ao salvar configuração');
    } finally {
      saving = false;
    }
  }

  async function handleCreate() {
    if (!form.name.trim()) return;
    if (form.event_type === 'regular') {
      if (form.day_of_week === undefined || !form.recurrence) return;
    } else {
      if (!form.event_date) return;
    }
    try {
      await createEvent(form);
      toast.success('Evento criado!');
      showModal = false;
      form = { name: '', event_type: 'regular', day_of_week: 0, recurrence: 'weekly' };
      await load();
    } catch (e: any) {
      toast.error(e.message || 'Erro ao criar evento');
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Remover evento?')) return;
    try {
      await deleteEvent(id);
      toast.success('Evento removido.');
      if (selectedEvent?.id === id) selectedEvent = null;
      await load();
    } catch (e: any) {
      toast.error(e.message || 'Erro ao remover');
    }
  }

  // Número de squads configurados para exibir no badge
  function squadCount(e: Event): number {
    return eventSquadCounts[e.id] ?? -1;
  }

  const DAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
  const DAYS_FULL = ['domingo', 'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado'];
  const RECURRENCE_LABELS: Record<RecurrenceType, string> = {
    weekly:    'Semanal',
    biweekly:  'Quinzenal',
    monthly_1: '1ª semana do mês',
    monthly_2: '2ª semana do mês',
    monthly_3: '3ª semana do mês',
    monthly_4: '4ª semana do mês',
  };

  function formatRecurrence(e: Event): string {
    if (e.event_type !== 'regular' || e.event_date) return e.event_date ?? '';
    const day = e.day_of_week !== null ? DAYS_FULL[e.day_of_week] : '?';
    const rec = e.recurrence ? RECURRENCE_LABELS[e.recurrence] : '';
    return `Todo ${day} — ${rec}`;
  }
</script>

<div data-testid="events-page" class="grid grid-cols-2 gap-6">
  <!-- Coluna esquerda: lista de eventos -->
  <div>
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">Eventos</h1>
      <button class="btn btn-primary" data-testid="btn-new-event" onclick={() => showModal = true}>+ Novo Evento</button>
    </div>

    {#if loading}
      <p>Carregando...</p>
    {:else if events.length === 0}
      <p class="text-slate-500">Nenhum evento cadastrado.</p>
    {:else}
      <div class="flex flex-col gap-2">
        {#each events as e (e.id)}
          <div
            data-testid="event-row"
            class="card cursor-pointer {selectedEvent?.id===e.id ? 'ring-2 ring-blue-500' : ''}"
            onclick={() => selectEvent(e)}
          >
            <div class="flex justify-between items-start">
              <div>
                <strong>{e.name}</strong>
                <span class="badge badge-blue ml-2">{e.event_type}</span>
                <p class="text-sm text-slate-500 mt-0.5">{formatRecurrence(e)}</p>
                {#if squadCount(e) > 0}
                  <span class="text-xs text-green-500 mt-0.5 block">● {squadCount(e)} {squadCount(e) === 1 ? 'time' : 'times'} configurado{squadCount(e) === 1 ? '' : 's'}</span>
                {:else if squadCount(e) === 0}
                  <span class="text-xs text-red-500 mt-0.5 block">✗ Sem times — clique para configurar</span>
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
      <h2 class="text-xl font-semibold mb-1">{selectedEvent.name}</h2>
      <p class="text-sm text-slate-500 mb-4">Configurar times para esta escala</p>

      <div class="flex flex-col gap-2 mb-4">
        {#each allSquads as sq (sq.id)}
          <div class="card p-3">
            <label class="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                bind:checked={squadConfig[sq.id].enabled}
                class="w-4 h-4 cursor-pointer"
              />
              <span class="flex-1 font-medium">{sq.name}</span>
              {#if squadConfig[sq.id].enabled}
                <span class="flex items-center gap-2 text-sm">
                  <span class="text-slate-500">mín</span>
                  <input
                    type="number" min="1" max="10"
                    class="input w-14 py-0.5 px-1.5 text-center"
                    bind:value={squadConfig[sq.id].min}
                    onclick={(e) => e.stopPropagation()}
                  />
                  <span class="text-slate-500">máx</span>
                  <input
                    type="number" min="1" max="10"
                    class="input w-14 py-0.5 px-1.5 text-center"
                    bind:value={squadConfig[sq.id].max}
                    onclick={(e) => e.stopPropagation()}
                  />
                </span>
              {/if}
            </label>
          </div>
        {/each}

        {#if allSquads.length === 0}
          <p class="text-slate-500">Nenhum time cadastrado. Cadastre times primeiro.</p>
        {/if}
      </div>

      <div class="flex gap-3">
        <button class="btn btn-primary" onclick={handleSaveSquads} disabled={saving}>
          {saving ? 'Salvando...' : 'Salvar Configuração'}
        </button>
        <button class="btn btn-secondary" onclick={() => selectedEvent = null}>Fechar</button>
      </div>
    </div>
  {:else}
    <div class="flex items-center justify-center text-slate-500">
      <p>Selecione um evento para configurar os times da escala.</p>
    </div>
  {/if}
</div>

{#if showModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="card w-[420px]" role="dialog" aria-modal="true">
      <h2 class="text-lg font-semibold mb-4">Novo Evento</h2>
      <div class="flex flex-col gap-3">
        <div class="form-group"><label for="ev-name">Nome *</label><input id="ev-name" name="name" class="input" bind:value={form.name} /></div>

        <div class="form-group"><label for="ev-type">Tipo</label>
          <select id="ev-type" class="input" bind:value={form.event_type}
            onchange={() => {
              if (form.event_type === 'regular') {
                form.event_date = undefined;
                form.day_of_week ??= 0;
                form.recurrence ??= 'weekly';
              } else {
                form.day_of_week = undefined;
                form.recurrence = undefined;
              }
            }}>
            <option value="regular">Regular (recorrente)</option>
            <option value="special">Especial</option>
            <option value="training">Treinamento</option>
          </select>
        </div>

        {#if form.event_type === 'regular'}
          <div class="form-group"><label for="ev-dow">Dia da semana *</label>
            <select id="ev-dow" class="input" bind:value={form.day_of_week}>
              {#each DAYS as d, i}
                <option value={i}>{d}</option>
              {/each}
            </select>
          </div>
          <div class="form-group"><label for="ev-rec">Frequência *</label>
            <select id="ev-rec" class="input" bind:value={form.recurrence}>
              <option value="weekly">Semanal (toda semana)</option>
              <option value="biweekly">Quinzenal (a cada 2 semanas)</option>
              <option value="monthly_1">Mensal — 1ª semana do mês</option>
              <option value="monthly_2">Mensal — 2ª semana do mês</option>
              <option value="monthly_3">Mensal — 3ª semana do mês</option>
              <option value="monthly_4">Mensal — 4ª semana do mês</option>
            </select>
          </div>
        {:else}
          <div class="form-group"><label for="ev-date">Data *</label><input id="ev-date" class="input" type="date" bind:value={form.event_date} /></div>
        {/if}

        <div class="flex gap-3 justify-end">
          <button class="btn btn-secondary" onclick={() => showModal = false}>Cancelar</button>
          <button class="btn btn-primary" data-testid="btn-save-event" onclick={handleCreate}>Salvar</button>
        </div>
      </div>
    </div>
  </div>
{/if}
