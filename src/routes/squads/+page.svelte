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

<div data-testid="squads-page" style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-6)">
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)">
      <h1 style="font-size:var(--text-2xl);font-weight:700">Times</h1>
      <button class="btn btn-primary" data-testid="btn-new-squad" onclick={() => showModal = true}>+ Novo Time</button>
    </div>
    {#if loading}<p>Carregando...</p>
    {:else}
      <div style="display:flex;flex-direction:column;gap:var(--space-2)">
        {#each squads as s (s.id)}
          <div data-testid="squad-row" class="card" style="cursor:pointer;border-color:{selectedSquad?.id===s.id?'var(--color-primary-500)':'var(--surface-border)'}" onclick={() => selectSquad(s)}>
            <div style="display:flex;justify-content:space-between">
              <strong>{s.name}</strong>
              <button class="btn btn-danger btn-sm" onclick={(e) => { e.stopPropagation(); handleDelete(s.id); }}>✕</button>
            </div>
            {#if s.description}<p style="font-size:var(--text-sm);color:var(--text-muted)">{s.description}</p>{/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>

  {#if selectedSquad}
    <div>
      <h2 style="font-size:var(--text-xl);font-weight:600;margin-bottom:var(--space-4)">{selectedSquad.name}</h2>
      <div style="display:flex;gap:var(--space-2);margin-bottom:var(--space-4)">
        <select class="input" name="member_id" data-testid="select-add-member" bind:value={addMemberId}>
          <option value="">Adicionar membro...</option>
          {#each notInSquad as m (m.id)}<option value={m.id}>{m.name}</option>{/each}
        </select>
        <button class="btn btn-primary" data-testid="btn-add-member" onclick={handleAddMember}>Adicionar Membro</button>
      </div>
      <div style="display:flex;flex-direction:column;gap:var(--space-2)">
        {#each squadMembers as m (m.id)}
          <div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:var(--space-3)">
            <span>{m.name}</span>
            <button class="btn btn-secondary btn-sm" onclick={() => handleRemoveMember(m.id)}>Remover</button>
          </div>
        {/each}
        {#if squadMembers.length === 0}<p style="color:var(--text-muted)">Nenhum membro neste time.</p>{/if}
      </div>
    </div>
  {/if}
</div>

{#if showModal}
  <div style="position:fixed;inset:0;background:rgb(0 0 0/0.5);display:flex;align-items:center;justify-content:center;z-index:50">
    <div class="card" role="dialog" aria-modal="true" style="width:360px">
      <h2 style="font-size:var(--text-lg);font-weight:600;margin-bottom:var(--space-4)">Novo Time</h2>
      <div class="form-group" style="margin-bottom:var(--space-4)"><label for="squad-name">Nome *</label><input id="squad-name" name="name" class="input" bind:value={newName} /></div>
      <div style="display:flex;gap:var(--space-3);justify-content:flex-end">
        <button class="btn btn-secondary" onclick={() => showModal = false}>Cancelar</button>
        <button class="btn btn-primary" data-testid="btn-save-squad" onclick={handleCreate}>Salvar</button>
      </div>
    </div>
  </div>
{/if}
