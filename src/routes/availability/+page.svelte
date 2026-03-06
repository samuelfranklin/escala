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
  <h1 class="text-2xl font-bold mb-6">Disponibilidade</h1>
  <div class="flex gap-3 mb-6">
    <select class="input max-w-[250px]" bind:value={selectedMemberId} onchange={loadAvailability}>
      <option value="">Selecione um membro...</option>
      {#each members as m (m.id)}<option value={m.id}>{m.name}</option>{/each}
    </select>
  </div>
  {#if selectedMemberId}
    <div class="flex gap-3 mb-4">
      <input class="input max-w-[180px]" type="date" bind:value={newDate} />
      <input class="input max-w-[200px]" placeholder="Motivo (opcional)" bind:value={newReason} />
      <button class="btn btn-primary" onclick={handleAdd}>Adicionar Indisponibilidade</button>
    </div>
    {#each availability as a (a.id)}
      <div class="card flex justify-between items-center mb-2">
        <span>{a.unavailable_date}{#if a.reason} — {a.reason}{/if}</span>
        <button class="btn btn-danger btn-sm" onclick={() => deleteAvailability(a.id).then(loadAvailability)}>✕</button>
      </div>
    {/each}
  {/if}
</div>
