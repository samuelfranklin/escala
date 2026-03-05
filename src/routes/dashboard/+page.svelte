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

    eventsThisMonth = es.filter(e => e.event_date.startsWith(thisMonth)).length;
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

<div>
  <h1 style="font-size:var(--text-2xl);font-weight:700;margin-bottom:var(--space-6)">Dashboard</h1>

  {#if loading}
    <p style="color:var(--text-muted)">Carregando...</p>
  {:else}
    <!-- KPI Cards -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:var(--space-4);margin-bottom:var(--space-8)">
      <!-- Membros -->
      <div class="card" style="display:flex;align-items:center;gap:var(--space-4)">
        <div style="width:44px;height:44px;border-radius:var(--radius-lg);background:var(--color-primary-50);display:flex;align-items:center;justify-content:center;flex-shrink:0">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary-600)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>
          </svg>
        </div>
        <div>
          <p style="font-size:var(--text-3xl);font-weight:700;line-height:1">{members.length}</p>
          <p style="font-size:var(--text-xs);font-weight:600;color:var(--text-muted);margin-top:2px">Membros</p>
          <p style="font-size:var(--text-xs);color:var(--text-muted)">{activeMembers()} ativos</p>
        </div>
      </div>

      <!-- Times -->
      <div class="card" style="display:flex;align-items:center;gap:var(--space-4)">
        <div style="width:44px;height:44px;border-radius:var(--radius-lg);background:#ede9fe;display:flex;align-items:center;justify-content:center;flex-shrink:0">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
          </svg>
        </div>
        <div>
          <p style="font-size:var(--text-3xl);font-weight:700;line-height:1">{squads.length}</p>
          <p style="font-size:var(--text-xs);font-weight:600;color:var(--text-muted);margin-top:2px">Times</p>
          <p style="font-size:var(--text-xs);color:var(--text-muted)">{squadsWithMembers} c/ membros</p>
        </div>
      </div>

      <!-- Eventos -->
      <div class="card" style="display:flex;align-items:center;gap:var(--space-4)">
        <div style="width:44px;height:44px;border-radius:var(--radius-lg);background:#fef9c3;display:flex;align-items:center;justify-content:center;flex-shrink:0">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </div>
        <div>
          <p style="font-size:var(--text-3xl);font-weight:700;line-height:1">{events.length}</p>
          <p style="font-size:var(--text-xs);font-weight:600;color:var(--text-muted);margin-top:2px">Eventos</p>
          <p style="font-size:var(--text-xs);color:var(--text-muted)">{eventsThisMonth} este mês</p>
        </div>
      </div>
    </div>

    <!-- Próximo Evento -->
    <h2 style="font-size:var(--text-base);font-weight:700;margin-bottom:var(--space-3);color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em">Próximo Evento</h2>
    {#if nextEvent}
      <div class="card" style="margin-bottom:var(--space-8)">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:var(--space-4)">
          <div>
            <p style="font-size:var(--text-lg);font-weight:700">{nextEvent.name}</p>
            <p style="font-size:var(--text-sm);color:var(--text-muted);margin-top:2px">{formatDateLong(nextEvent.event_date)}</p>
            <span class="badge badge-blue" style="margin-top:var(--space-2)">{nextEvent.event_type}</span>
          </div>
          {#if nextEventSquads.length > 0}
            <p style="font-size:var(--text-sm);color:#16a34a;white-space:nowrap;font-weight:600">✓ {nextEventSquads.length} {nextEventSquads.length === 1 ? 'time' : 'times'} configurado{nextEventSquads.length > 1 ? 's' : ''}</p>
          {:else}
            <a href="/events" style="font-size:var(--text-sm);color:#b45309;font-weight:600;white-space:nowrap;text-decoration:none">⚠ Sem times — Configurar →</a>
          {/if}
        </div>
      </div>
    {:else}
      <div class="card" style="margin-bottom:var(--space-8);text-align:center;padding:var(--space-8);color:var(--text-muted)">
        <p style="margin-bottom:var(--space-2)">Nenhum evento próximo.</p>
        <a href="/events" class="btn btn-primary" style="display:inline-block">+ Criar Evento</a>
      </div>
    {/if}

    <!-- Alertas -->
    <h2 style="font-size:var(--text-base);font-weight:700;margin-bottom:var(--space-3);color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em">Alertas</h2>
    {#if eventsWithoutSquads === 0 && membersWithoutSquad === 0}
      <div class="card" style="display:flex;align-items:center;gap:var(--space-3);color:#16a34a">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <p style="font-size:var(--text-sm);font-weight:600">Tudo configurado!</p>
      </div>
    {:else}
      <div class="card" style="display:flex;flex-direction:column;gap:var(--space-3)">
        {#if eventsWithoutSquads > 0}
          <div style="display:flex;align-items:center;justify-content:space-between;gap:var(--space-4)">
            <p style="font-size:var(--text-sm);color:#b45309">
              ⚠ {eventsWithoutSquads} {eventsWithoutSquads === 1 ? 'evento sem times configurados' : 'eventos sem times configurados'}
            </p>
            <a href="/events" style="font-size:var(--text-sm);font-weight:600;color:var(--color-primary-600);text-decoration:none;white-space:nowrap">Corrigir →</a>
          </div>
        {/if}
        {#if membersWithoutSquad > 0}
          <div style="display:flex;align-items:center;justify-content:space-between;gap:var(--space-4)">
            <p style="font-size:var(--text-sm);color:#b45309">
              ⚠ {membersWithoutSquad} {membersWithoutSquad === 1 ? 'membro ativo sem time' : 'membros ativos sem time'}
            </p>
            <a href="/squads" style="font-size:var(--text-sm);font-weight:600;color:var(--color-primary-600);text-decoration:none;white-space:nowrap">Corrigir →</a>
          </div>
        {/if}
      </div>
    {/if}
  {/if}
</div>

