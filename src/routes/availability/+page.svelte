<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers } from '$lib/api/members';
  import { getAvailability, createAvailability, deleteAvailability } from '$lib/api/availability';
  import type { Member, Availability } from '$lib/types';
  import * as Select from '$lib/components/ui/select/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import Icon from '@iconify/svelte';

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
  <h1 class="text-2xl font-heading font-bold mb-6">Disponibilidade</h1>

  <div class="flex flex-col gap-1.5 mb-6 max-w-[280px]">
    <Label>Membro</Label>
    <Select.Root type="single" onValueChange={(v: any) => { selectedMemberId = v; loadAvailability(); }}>
      <Select.Trigger>
        {members.find(m => m.id === selectedMemberId)?.name ?? 'Selecione um membro...'}
      </Select.Trigger>
      <Select.Content>
        {#each members as m (m.id)}
          <Select.Item value={m.id}>{m.name}</Select.Item>
        {/each}
      </Select.Content>
    </Select.Root>
  </div>

  {#if selectedMemberId}
    <div class="flex gap-3 mb-5 flex-wrap items-end">
      <div class="flex flex-col gap-1.5">
        <Label for="avail-date">Data</Label>
        <Input id="avail-date" class="max-w-[180px]" type="date" bind:value={newDate} />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="avail-reason">Motivo (opcional)</Label>
        <Input id="avail-reason" class="max-w-[220px]" placeholder="Ex: viagem, compromisso..." bind:value={newReason} />
      </div>
      <Button onclick={handleAdd}>
        <Icon icon="lucide:plus" class="size-4 mr-1" /> Adicionar
      </Button>
    </div>

    <div class="flex flex-col gap-2 max-w-[600px]">
      {#each availability as a (a.id)}
        <div class="rounded-lg border bg-card flex justify-between items-center p-3 shadow-sm">
          <div class="flex items-center gap-2 text-sm">
            <Icon icon="lucide:calendar-x" class="size-4 text-muted-foreground" />
            <span>{a.unavailable_date}</span>
            {#if a.reason}<span class="text-muted-foreground">— {a.reason}</span>{/if}
          </div>
          <Button variant="ghost" size="icon" class="size-7 text-muted-foreground hover:text-destructive"
            onclick={() => deleteAvailability(a.id).then(loadAvailability)}>
            <Icon icon="lucide:x" class="size-3.5" />
          </Button>
        </div>
      {/each}
      {#if availability.length === 0}
        <p class="text-sm text-muted-foreground mt-2">Nenhuma indisponibilidade registrada.</p>
      {/if}
    </div>
  {/if}
</div>
