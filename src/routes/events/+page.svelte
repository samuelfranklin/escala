<script lang="ts">
  import { onMount } from 'svelte';
  import { getEvents, createEvent, deleteEvent, getEventSquads, setEventSquads } from '$lib/api/events';
  import { getSquads } from '$lib/api/squads';
  import { toast } from '$lib/stores/toast';
  import type { Event, CreateEventDto, Squad, EventSquad, EventSquadDto, RecurrenceType } from '$lib/types';
  import * as Dialog from '$lib/components/ui/dialog/index.js';
  import * as Select from '$lib/components/ui/select/index.js';
  import * as Checkbox from '$lib/components/ui/checkbox/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import Icon from '@iconify/svelte';

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
        : { enabled: false, min: 1, max: 1 };
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
      <h1 class="text-2xl font-heading font-bold">Eventos</h1>
      <Button data-testid="btn-new-event" onclick={() => showModal = true}>
        <Icon icon="lucide:plus" class="size-4 mr-1" /> Novo Evento
      </Button>
    </div>

    {#if loading}
      <div class="flex flex-col gap-2">
        {#each [1,2,3] as _}
          <div class="h-16 rounded-lg bg-muted animate-pulse"></div>
        {/each}
      </div>
    {:else if events.length === 0}
      <p class="text-muted-foreground">Nenhum evento cadastrado.</p>
    {:else}
      <div class="flex flex-col gap-2">
        {#each events as e (e.id)}
          <div
            data-testid="event-row"
            class="rounded-lg border bg-card p-3 cursor-pointer transition-all hover:bg-accent {selectedEvent?.id===e.id ? 'ring-2 ring-primary' : ''}"
            onclick={() => selectEvent(e)}
            role="button"
            tabindex="0"
            onkeydown={(ev) => ev.key === 'Enter' && selectEvent(e)}
          >
            <div class="flex justify-between items-start">
              <div>
                <div class="flex items-center gap-2">
                  <strong class="text-sm">{e.name}</strong>
                  <Badge variant="secondary" class="text-xs">{e.event_type}</Badge>
                </div>
                <p class="text-xs text-muted-foreground mt-0.5">{formatRecurrence(e)}</p>
                {#if squadCount(e) > 0}
                  <p class="text-xs text-green-600 mt-0.5">● {squadCount(e)} {squadCount(e) === 1 ? 'time' : 'times'} configurado{squadCount(e) === 1 ? '' : 's'}</p>
                {:else if squadCount(e) === 0}
                  <p class="text-xs text-destructive mt-0.5">✗ Sem times — clique para configurar</p>
                {/if}
              </div>
              <Button variant="ghost" size="icon" class="size-7 text-muted-foreground hover:text-destructive"
                onclick={(ev: MouseEvent) => { ev.stopPropagation(); handleDelete(e.id); }}>
                <Icon icon="lucide:x" class="size-3.5" />
              </Button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Coluna direita: painel de configuração de times -->
  {#if selectedEvent}
    <div>
      <h2 class="text-xl font-heading font-semibold mb-1">{selectedEvent.name}</h2>
      <p class="text-sm text-muted-foreground mb-4">Configurar times para esta escala</p>

      <div class="flex flex-col gap-2 mb-4">
        {#each allSquads as sq (sq.id)}
          <div class="rounded-lg border bg-card p-3">
            <label class="flex items-center gap-3 cursor-pointer">
              <Checkbox.Root
                checked={squadConfig[sq.id].enabled}
                onCheckedChange={(v: boolean | 'indeterminate') => squadConfig[sq.id].enabled = v === true}
              />
              <span class="flex-1 text-sm font-medium">{sq.name}</span>
              {#if squadConfig[sq.id].enabled}
                <span class="flex items-center gap-2 text-sm">
                  <span class="text-muted-foreground">mín</span>
                  <Input
                    type="number" min="1" max="10"
                    class="w-14 py-0.5 px-1.5 text-center h-7"
                    bind:value={squadConfig[sq.id].min}
                    onclick={(e: MouseEvent) => e.stopPropagation()}
                  />
                  <span class="text-muted-foreground">máx</span>
                  <Input
                    type="number" min="1" max="10"
                    class="w-14 py-0.5 px-1.5 text-center h-7"
                    bind:value={squadConfig[sq.id].max}
                    onclick={(e: MouseEvent) => e.stopPropagation()}
                  />
                </span>
              {/if}
            </label>
          </div>
        {/each}

        {#if allSquads.length === 0}
          <p class="text-sm text-muted-foreground">Nenhum time cadastrado. Cadastre times primeiro.</p>
        {/if}
      </div>

      <div class="flex gap-3">
        <Button onclick={handleSaveSquads} disabled={saving}>
          {saving ? 'Salvando...' : 'Salvar Configuração'}
        </Button>
        <Button variant="outline" onclick={() => selectedEvent = null}>Fechar</Button>
      </div>
    </div>
  {:else}
    <div class="flex items-center justify-center text-muted-foreground">
      <p>Selecione um evento para configurar os times da escala.</p>
    </div>
  {/if}
</div>

<Dialog.Root bind:open={showModal}>
  <Dialog.Content class="sm:max-w-[440px]">
    <Dialog.Header>
      <Dialog.Title class="font-heading">Novo Evento</Dialog.Title>
    </Dialog.Header>
    <div class="flex flex-col gap-4 py-2">
      <div class="flex flex-col gap-1.5">
        <Label for="ev-name">Nome *</Label>
        <Input id="ev-name" name="name" bind:value={form.name} />
      </div>

      <div class="flex flex-col gap-1.5">
        <Label>Tipo</Label>
        <Select.Root type="single" onValueChange={(v: any) => {
          form.event_type = v as typeof form.event_type;
          if (v === 'regular') {
            form.event_date = undefined;
            form.day_of_week ??= 0;
            form.recurrence ??= 'weekly';
          } else {
            form.day_of_week = undefined;
            form.recurrence = undefined;
          }
        }}>
          <Select.Trigger>
            {({'regular':'Regular (recorrente)', 'special':'Especial', 'training':'Treinamento'} as Record<string,string>)[form.event_type ?? ''] ?? 'Tipo'}
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="regular">Regular (recorrente)</Select.Item>
            <Select.Item value="special">Especial</Select.Item>
            <Select.Item value="training">Treinamento</Select.Item>
          </Select.Content>
        </Select.Root>
      </div>

      {#if form.event_type === 'regular'}
        <div class="flex flex-col gap-1.5">
          <Label>Dia da semana *</Label>
          <Select.Root type="single" onValueChange={(v: any) => form.day_of_week = Number(v)}>
            <Select.Trigger>
              {DAYS[form.day_of_week ?? 0] ?? 'Selecionar dia'}
            </Select.Trigger>
            <Select.Content>
              {#each DAYS as d, i}
                <Select.Item value={String(i)}>{d}</Select.Item>
              {/each}
            </Select.Content>
          </Select.Root>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label>Frequência *</Label>
          <Select.Root type="single" onValueChange={(v: any) => form.recurrence = v as RecurrenceType}>
            <Select.Trigger>
              {RECURRENCE_LABELS[form.recurrence ?? 'weekly'] ?? 'Frequência'}
            </Select.Trigger>
            <Select.Content>
              <Select.Item value="weekly">Semanal (toda semana)</Select.Item>
              <Select.Item value="biweekly">Quinzenal (a cada 2 semanas)</Select.Item>
              <Select.Item value="monthly_1">Mensal — 1ª semana do mês</Select.Item>
              <Select.Item value="monthly_2">Mensal — 2ª semana do mês</Select.Item>
              <Select.Item value="monthly_3">Mensal — 3ª semana do mês</Select.Item>
              <Select.Item value="monthly_4">Mensal — 4ª semana do mês</Select.Item>
            </Select.Content>
          </Select.Root>
        </div>
      {:else}
        <div class="flex flex-col gap-1.5">
          <Label for="ev-date">Data *</Label>
          <Input id="ev-date" type="date" bind:value={form.event_date} />
        </div>
      {/if}
    </div>
    <Dialog.Footer>
      <Button variant="outline" onclick={() => showModal = false}>Cancelar</Button>
      <Button data-testid="btn-save-event" onclick={handleCreate}>Salvar</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
