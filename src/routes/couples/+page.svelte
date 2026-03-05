<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers } from '$lib/api/members';
  import { getCouples, createCouple, deleteCouple } from '$lib/api/couples';
  import type { Member, Couple } from '$lib/types';

  let members = $state<Member[]>([]);
  let couples = $state<Couple[]>([]);
  let memberA = $state('');
  let memberB = $state('');

  onMount(async () => {
    [members, couples] = await Promise.all([getMembers(), getCouples()]);
  });

  function getName(id: string) { return members.find(m => m.id === id)?.name ?? id; }

  async function handleCreate() {
    if (!memberA || !memberB || memberA === memberB) return;
    await createCouple({ member_a_id: memberA, member_b_id: memberB });
    memberA = ''; memberB = '';
    couples = await getCouples();
  }
</script>

<div>
  <h1 style="font-size:var(--text-2xl);font-weight:700;margin-bottom:var(--space-6)">Restrições de Casais</h1>
  <p style="color:var(--text-muted);margin-bottom:var(--space-6)">Casais não são escalados juntos no mesmo evento.</p>
  <div style="display:flex;gap:var(--space-3);margin-bottom:var(--space-6)">
    <select class="input" style="max-width:200px" bind:value={memberA}>
      <option value="">Membro A...</option>
      {#each members as m (m.id)}<option value={m.id}>{m.name}</option>{/each}
    </select>
    <select class="input" style="max-width:200px" bind:value={memberB}>
      <option value="">Membro B...</option>
      {#each members as m (m.id)}<option value={m.id}>{m.name}</option>{/each}
    </select>
    <button class="btn btn-primary" onclick={handleCreate}>Adicionar Restrição</button>
  </div>
  <div style="display:flex;flex-direction:column;gap:var(--space-2)">
    {#each couples as c (c.id)}
      <div class="card" style="display:flex;justify-content:space-between;align-items:center">
        <span>{getName(c.member_a_id)} 💑 {getName(c.member_b_id)}</span>
        <button class="btn btn-danger btn-sm" onclick={() => deleteCouple(c.id).then(() => getCouples().then(r => couples = r))}>✕</button>
      </div>
    {/each}
  </div>
</div>
