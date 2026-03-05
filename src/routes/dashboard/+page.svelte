<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers } from '$lib/api/members';
  import { getSquads } from '$lib/api/squads';
  import { getEvents } from '$lib/api/events';

  let memberCount = $state(0);
  let squadCount = $state(0);
  let eventCount = $state(0);

  onMount(async () => {
    const [members, squads, events] = await Promise.all([getMembers(), getSquads(), getEvents()]);
    memberCount = members.length;
    squadCount = squads.length;
    eventCount = events.length;
  });
</script>

<div>
  <h1 style="font-size: var(--text-2xl); font-weight: 700; margin-bottom: var(--space-6)">Dashboard</h1>
  <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4)">
    <div class="card"><p class="badge badge-blue">Membros</p><p style="font-size:var(--text-3xl);font-weight:700;margin-top:var(--space-2)">{memberCount}</p></div>
    <div class="card"><p class="badge badge-green">Times</p><p style="font-size:var(--text-3xl);font-weight:700;margin-top:var(--space-2)">{squadCount}</p></div>
    <div class="card"><p class="badge badge-yellow">Eventos</p><p style="font-size:var(--text-3xl);font-weight:700;margin-top:var(--space-2)">{eventCount}</p></div>
  </div>
</div>
