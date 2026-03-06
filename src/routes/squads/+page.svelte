<script lang="ts">
  import { onMount } from 'svelte';
  import { getSquads, createSquad, deleteSquad, getSquadMembers, addMemberToSquad, removeMemberFromSquad } from '$lib/api/squads';
  import { getMembers } from '$lib/api/members';
  import { toast } from '$lib/stores/toast';
  import type { Squad, Member } from '$lib/types';

  let squads = $state<Squad[]>([]);
  let allMembers = $state<Member[]>([]);
  let selectedSquad = $state<Squad | null>(null);
  let squadMembers = $state<Member[]>([]);
  let loading = $state(true);
  let showModal = $state(false);
  let newName = $state('');
  let addMemberId = $state('');

  onMount(load);

  async function load() {
    loading = true;
    [squads, allMembers] = await Promise.all([getSquads(), getMembers()]);
    loading = false;
  }

  async function selectSquad(s: Squad) {
    selectedSquad = s;
    squadMembers = await getSquadMembers(s.id);
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    try { await createSquad({ name: newName }); toast.success('Time criado!'); }
    catch (e: any) { toast.error(e.message || 'Erro ao criar time'); return; }
    newName = ''; showModal = false;
    await load();
  }

  async function handleDelete(id: string) {
    if (!confirm('Remover time?')) return;
    try { await deleteSquad(id); toast.success('Time removido.'); }
    catch (e: any) { toast.error(e.message || 'Erro ao remover'); return; }
    if (selectedSquad?.id === id) selectedSquad = null;
    await load();
  }

  async function handleAddMember() {
    if (!selectedSquad || !addMemberId) return;
    await addMemberToSquad(selectedSquad.id, addMemberId);
    addMemberId = '';
    squadMembers = await getSquadMembers(selectedSquad.id);
  }

  async function handleRemoveMember(memberId: string) {
    if (!selectedSquad) return;
    await removeMemberFromSquad(selectedSquad.id, memberId);
    squadMembers = await getSquadMembers(selectedSquad.id);
  }

  const notInSquad = $derived(allMembers.filter(m => !squadMembers.some(sm => sm.id === m.id)));
</script>

<div data-testid="squads-page" class="grid grid-cols-2 gap-6">
  <div>
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">Times</h1>
      <button class="btn btn-primary" data-testid="btn-new-squad" onclick={() => showModal = true}>+ Novo Time</button>
    </div>
    {#if loading}<p>Carregando...</p>
    {:else}
      <div class="flex flex-col gap-2">
        {#each squads as s (s.id)}
          <div data-testid="squad-row" class="card cursor-pointer {selectedSquad?.id===s.id ? 'ring-2 ring-blue-500' : ''}" onclick={() => selectSquad(s)}>
            <div class="flex justify-between">
              <strong>{s.name}</strong>
              <button class="btn btn-danger btn-sm" onclick={(e) => { e.stopPropagation(); handleDelete(s.id); }}>✕</button>
            </div>
            {#if s.description}<p class="text-sm text-slate-500">{s.description}</p>{/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>

  {#if selectedSquad}
    <div>
      <h2 class="text-xl font-semibold mb-4">{selectedSquad.name}</h2>
      <div class="flex gap-2 mb-4">
        <select class="input" name="member_id" data-testid="select-add-member" bind:value={addMemberId}>
          <option value="">Adicionar membro...</option>
          {#each notInSquad as m (m.id)}<option value={m.id}>{m.name}</option>{/each}
        </select>
        <button class="btn btn-primary" data-testid="btn-add-member" onclick={handleAddMember}>Adicionar Membro</button>
      </div>
      <div class="flex flex-col gap-2">
        {#each squadMembers as m (m.id)}
          <div class="card flex justify-between items-center p-3">
            <span>{m.name}</span>
            <button class="btn btn-secondary btn-sm" onclick={() => handleRemoveMember(m.id)}>Remover</button>
          </div>
        {/each}
        {#if squadMembers.length === 0}<p class="text-slate-500">Nenhum membro neste time.</p>{/if}
      </div>
    </div>
  {/if}
</div>

{#if showModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="card w-[360px]" role="dialog" aria-modal="true">
      <h2 class="text-lg font-semibold mb-4">Novo Time</h2>
      <div class="form-group mb-4"><label for="squad-name">Nome *</label><input id="squad-name" name="name" class="input" bind:value={newName} /></div>
      <div class="flex gap-3 justify-end">
        <button class="btn btn-secondary" onclick={() => showModal = false}>Cancelar</button>
        <button class="btn btn-primary" data-testid="btn-save-squad" onclick={handleCreate}>Salvar</button>
      </div>
    </div>
  </div>
{/if}
