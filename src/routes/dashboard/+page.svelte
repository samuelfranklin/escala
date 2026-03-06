<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers } from '$lib/api/members';
  import { getSquads, getSquadMembers } from '$lib/api/squads';
  import { getEvents, getEventSquads } from '$lib/api/events';
  import { formatDateLong, getNextEvent } from '$lib/utils';
  import type { Member, Squad, Event, EventSquad } from '$lib/types';

  let members = $state<Member[]>([]);
  let squads = $state<Squad[]>([]);
  let events = $state<Event[]>([]);
  let squadsWithMembers = $state(0);
  let eventsThisMonth = $state(0);
  let nextEvent = $state<Event | null>(null);
  let nextEventSquads = $state<EventSquad[]>([]);
  let eventsWithoutSquads = $state(0);
  let membersWithoutSquad = $state(0);
  let loading = $state(true);

  onMount(async () => {
    const today = new Date().toISOString().slice(0, 10);
    const thisMonth = today.slice(0, 7);

    const [ms, ss, es] = await Promise.all([getMembers(), getSquads(), getEvents()]);
    members = ms;
    squads = ss;
    events = es;

    eventsThisMonth = es.filter(e => e.event_date?.startsWith(thisMonth)).length;
    nextEvent = getNextEvent(es, today);

    // Squads com membros
    const memberCounts = await Promise.all(ss.map(s => getSquadMembers(s.id)));
    squadsWithMembers = memberCounts.filter(m => m.length > 0).length;

    // Membros sem time
    const allSquadMemberIds = new Set(memberCounts.flat().map(m => m.id));
    membersWithoutSquad = ms.filter(m => m.active && !allSquadMemberIds.has(m.id)).length;

    // Eventos sem squads configurados
    const eventSquadsList = await Promise.all(es.map(e => getEventSquads(e.id)));
    eventsWithoutSquads = eventSquadsList.filter(sl => sl.length === 0).length;

    // Squads do próximo evento
    if (nextEvent) {
      nextEventSquads = await getEventSquads(nextEvent.id);
    }

    loading = false;
  });

  const activeMembers = $derived(() => members.filter(m => m.active).length);
</script>

<div data-testid="dashboard">
  <h1 class="text-2xl font-heading font-bold mb-6">Dashboard</h1>

  {#if loading}
    <div class="grid grid-cols-3 gap-4 mb-8">
      {#each [1,2,3] as _}
        <div class="h-24 rounded-lg bg-muted animate-pulse"></div>
      {/each}
    </div>
  {:else}
    <!-- KPI Cards -->
    <div class="grid grid-cols-3 gap-4 mb-8">
      <div class="rounded-xl border bg-card p-4 flex items-center gap-4 shadow-sm">
        <div class="w-11 h-11 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-blue-600">
            <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>
          </svg>
        </div>
        <div>
          <p class="text-3xl font-bold leading-none">{members.length}</p>
          <p class="text-xs font-semibold text-muted-foreground mt-0.5">Membros</p>
          <p class="text-xs text-muted-foreground">{activeMembers()} ativos</p>
        </div>
      </div>

      <div class="rounded-xl border bg-card p-4 flex items-center gap-4 shadow-sm">
        <div class="w-11 h-11 rounded-lg bg-violet-50 flex items-center justify-center shrink-0">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
          </svg>
        </div>
        <div>
          <p class="text-3xl font-bold leading-none">{squads.length}</p>
          <p class="text-xs font-semibold text-muted-foreground mt-0.5">Times</p>
          <p class="text-xs text-muted-foreground">{squadsWithMembers} c/ membros</p>
        </div>
      </div>

      <div class="rounded-xl border bg-card p-4 flex items-center gap-4 shadow-sm">
        <div class="w-11 h-11 rounded-lg bg-yellow-50 flex items-center justify-center shrink-0">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </div>
        <div>
          <p class="text-3xl font-bold leading-none">{events.length}</p>
          <p class="text-xs font-semibold text-muted-foreground mt-0.5">Eventos</p>
          <p class="text-xs text-muted-foreground">{eventsThisMonth} este mês</p>
        </div>
      </div>
    </div>

    <!-- Próximo Evento -->
    <h2 class="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3">Próximo Evento</h2>
    {#if nextEvent}
      <div class="rounded-xl border bg-card p-5 mb-8 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-lg font-bold font-heading">{nextEvent.name}</p>
            <p class="text-sm text-muted-foreground mt-0.5">{nextEvent.event_date ? formatDateLong(nextEvent.event_date) : ''}</p>
            <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold mt-2">{nextEvent.event_type}</span>
          </div>
          {#if nextEventSquads.length > 0}
            <p class="text-sm text-green-600 whitespace-nowrap font-semibold">✓ {nextEventSquads.length} {nextEventSquads.length === 1 ? 'time' : 'times'} configurado{nextEventSquads.length > 1 ? 's' : ''}</p>
          {:else}
            <a href="/events" class="text-sm text-amber-700 font-semibold whitespace-nowrap no-underline hover:underline">⚠ Sem times — Configurar →</a>
          {/if}
        </div>
      </div>
    {:else}
      <div class="rounded-xl border bg-card p-8 mb-8 text-center text-muted-foreground shadow-sm">
        <p class="mb-3">Nenhum evento próximo.</p>
        <a href="/events" class="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors no-underline">+ Criar Evento</a>
      </div>
    {/if}

    <!-- Alertas -->
    <h2 class="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3">Alertas</h2>
    {#if eventsWithoutSquads === 0 && membersWithoutSquad === 0}
      <div class="rounded-xl border bg-card p-4 flex items-center gap-3 text-green-600 shadow-sm">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <p class="text-sm font-semibold">Tudo configurado!</p>
      </div>
    {:else}
      <div class="rounded-xl border bg-card p-4 flex flex-col gap-3 shadow-sm">
        {#if eventsWithoutSquads > 0}
          <div class="flex items-center justify-between gap-4">
            <p class="text-sm text-amber-700">
              ⚠ {eventsWithoutSquads} {eventsWithoutSquads === 1 ? 'evento sem times configurados' : 'eventos sem times configurados'}
            </p>
            <a href="/events" class="text-sm font-semibold text-primary no-underline hover:underline whitespace-nowrap">Corrigir →</a>
          </div>
        {/if}
        {#if membersWithoutSquad > 0}
          <div class="flex items-center justify-between gap-4">
            <p class="text-sm text-amber-700">
              ⚠ {membersWithoutSquad} {membersWithoutSquad === 1 ? 'membro ativo sem time' : 'membros ativos sem time'}
            </p>
            <a href="/squads" class="text-sm font-semibold text-primary no-underline hover:underline whitespace-nowrap">Corrigir →</a>
          </div>
        {/if}
      </div>
    {/if}
  {/if}
</div>

