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
  <h1 class="text-2xl font-bold mb-6">Restrições de Casais</h1>
  <p class="text-slate-500 mb-6">Casais não são escalados juntos no mesmo evento.</p>
  <div class="flex gap-3 mb-6">
    <select class="input max-w-[200px]" bind:value={memberA}>
      <option value="">Membro A...</option>
      {#each members as m (m.id)}<option value={m.id}>{m.name}</option>{/each}
    </select>
    <select class="input max-w-[200px]" bind:value={memberB}>
      <option value="">Membro B...</option>
      {#each members as m (m.id)}<option value={m.id}>{m.name}</option>{/each}
    </select>
    <button class="btn btn-primary" onclick={handleCreate}>Adicionar Restrição</button>
  </div>
  <div class="flex flex-col gap-2">
    {#each couples as c (c.id)}
      <div class="card flex justify-between items-center">
        <span>{getName(c.member_a_id)} 💑 {getName(c.member_b_id)}</span>
        <button class="btn btn-danger btn-sm" onclick={() => deleteCouple(c.id).then(() => getCouples().then(r => couples = r))}>✕</button>
      </div>
    {/each}
  </div>
</div>
