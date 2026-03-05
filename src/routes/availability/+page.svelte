<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers } from '$lib/api/members';
  import { getAvailability, createAvailability, deleteAvailability } from '$lib/api/availability';
  import type { Member, Availability } from '$lib/types';

  let members = $state<Member[]>([]);
  let selectedMemberId = $state('');
  let availability = $state<Availability[]>([]);
  let newDate = $state('');
  let newReason = $state('');

  onMount(async () => { members = await getMembers(); });

  async function loadAvailability() {
    if (!selectedMemberId) return;
    availability = await getAvailability(selectedMemberId);
  }

  async function handleAdd() {
    if (!selectedMemberId || !newDate) return;
    await createAvailability({ member_id: selectedMemberId, unavailable_date: newDate, reason: newReason || undefined });
    newDate = ''; newReason = '';
    await loadAvailability();
  }
</script>

<div>
  <h1 style="font-size:var(--text-2xl);font-weight:700;margin-bottom:var(--space-6)">Disponibilidade</h1>
  <div style="display:flex;gap:var(--space-3);margin-bottom:var(--space-6)">
    <select class="input" style="max-width:250px" bind:value={selectedMemberId} onchange={loadAvailability}>
      <option value="">Selecione um membro...</option>
      {#each members as m (m.id)}<option value={m.id}>{m.name}</option>{/each}
    </select>
  </div>
  {#if selectedMemberId}
    <div style="display:flex;gap:var(--space-3);margin-bottom:var(--space-4)">
      <input class="input" type="date" bind:value={newDate} style="max-width:180px" />
      <input class="input" placeholder="Motivo (opcional)" bind:value={newReason} style="max-width:200px" />
      <button class="btn btn-primary" onclick={handleAdd}>Adicionar Indisponibilidade</button>
    </div>
    {#each availability as a (a.id)}
      <div class="card" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-2)">
        <span>{a.unavailable_date}{#if a.reason} — {a.reason}{/if}</span>
        <button class="btn btn-danger btn-sm" onclick={() => deleteAvailability(a.id).then(loadAvailability)}>✕</button>
      </div>
    {/each}
  {/if}
</div>
