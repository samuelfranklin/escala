<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers } from '$lib/api/members';
  import { getCouples, createCouple, deleteCouple } from '$lib/api/couples';
  import type { Member, Couple } from '$lib/types';
  import * as Select from '$lib/components/ui/select/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import Icon from '@iconify/svelte';

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
  <h1 class="text-2xl font-heading font-bold mb-2">Restrições de Casais</h1>
  <p class="text-muted-foreground mb-6">Casais cadastrados são sempre escalados juntos no mesmo evento.</p>

  <div class="flex gap-3 mb-6 flex-wrap items-end">
    <div class="flex flex-col gap-1.5">
      <Label>Membro A</Label>
      <Select.Root type="single" onValueChange={(v: any) => memberA = v}>
        <Select.Trigger class="w-[200px]">
          {members.find(m => m.id === memberA)?.name ?? 'Selecionar...'}
        </Select.Trigger>
        <Select.Content>
          {#each members as m (m.id)}
            <Select.Item value={m.id}>{m.name}</Select.Item>
          {/each}
        </Select.Content>
      </Select.Root>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label>Membro B</Label>
      <Select.Root type="single" onValueChange={(v: any) => memberB = v}>
        <Select.Trigger class="w-[200px]">
          {members.find(m => m.id === memberB)?.name ?? 'Selecionar...'}
        </Select.Trigger>
        <Select.Content>
          {#each members as m (m.id)}
            <Select.Item value={m.id}>{m.name}</Select.Item>
          {/each}
        </Select.Content>
      </Select.Root>
    </div>
    <Button onclick={handleCreate} class="mb-0.5">
      <Icon icon="lucide:plus" class="size-4 mr-1" /> Adicionar Restrição
    </Button>
  </div>

  <div class="flex flex-col gap-2 max-w-[500px]">
    {#each couples as c (c.id)}
      <div class="rounded-lg border bg-card flex justify-between items-center p-3 shadow-sm">
        <div class="flex items-center gap-2 text-sm">
          <Icon icon="lucide:heart" class="size-4 text-rose-400" />
          <span>{getName(c.member_a_id)}</span>
          <span class="text-muted-foreground">e</span>
          <span>{getName(c.member_b_id)}</span>
        </div>
        <Button variant="ghost" size="icon" class="size-7 text-muted-foreground hover:text-destructive"
          onclick={() => deleteCouple(c.id).then(() => getCouples().then(r => couples = r))}>
          <Icon icon="lucide:x" class="size-3.5" />
        </Button>
      </div>
    {/each}
    {#if couples.length === 0}
      <p class="text-sm text-muted-foreground mt-2">Nenhuma restrição registrada.</p>
    {/if}
  </div>
</div>
