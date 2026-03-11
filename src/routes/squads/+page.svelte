<script lang="ts">
  import { onMount } from 'svelte';
  import { getSquads, createSquad, deleteSquad, getSquadMembers, addMemberToSquad, removeMemberFromSquad } from '$lib/api/squads';
  import { getMembers } from '$lib/api/members';
  import { toast } from '$lib/stores/toast';
  import type { Squad, Member } from '$lib/types';
  import * as Dialog from '$lib/components/ui/dialog/index.js';
  import * as Select from '$lib/components/ui/select/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import Icon from '@iconify/svelte';

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
      <h1 class="text-2xl font-heading font-bold">Times</h1>
      <Button data-testid="btn-new-squad" onclick={() => showModal = true}>
        <Icon icon="lucide:plus" class="size-4 mr-1" /> Novo Time
      </Button>
    </div>
    {#if loading}
      <div class="flex flex-col gap-2">
        {#each [1,2,3] as _}
          <div class="h-14 rounded-lg bg-muted animate-pulse"></div>
        {/each}
      </div>
    {:else}
      <div class="flex flex-col gap-2">
        {#each squads as s (s.id)}
          <div
            data-testid="squad-row"
            class="rounded-lg border bg-card p-3 cursor-pointer transition-all hover:bg-accent {selectedSquad?.id===s.id ? 'ring-2 ring-primary' : ''}"
            onclick={() => selectSquad(s)}
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === 'Enter' && selectSquad(s)}
          >
            <div class="flex justify-between items-center">
              <strong class="text-sm">{s.name}</strong>
              <Button variant="ghost" size="icon" class="size-7 text-muted-foreground hover:text-destructive"
                onclick={(e: Event) => { e.stopPropagation(); handleDelete(s.id); }}>
                <Icon icon="lucide:x" class="size-3.5" />
              </Button>
            </div>
            {#if s.description}<p class="text-xs text-muted-foreground mt-0.5">{s.description}</p>{/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>

  {#if selectedSquad}
    <div>
      <h2 class="text-xl font-heading font-semibold mb-4">{selectedSquad.name}</h2>
      <div class="flex gap-2 mb-4">
        <Select.Root type="single" onValueChange={(v: any) => addMemberId = v}>
          <Select.Trigger class="flex-1" data-testid="select-add-member">
            {notInSquad.find(m => m.id === addMemberId)?.name ?? 'Adicionar membro...'}
          </Select.Trigger>
          <Select.Content>
            {#each notInSquad as m (m.id)}
              <Select.Item value={m.id}>{m.name}</Select.Item>
            {/each}
          </Select.Content>
        </Select.Root>
        <Button data-testid="btn-add-member" onclick={handleAddMember}>Adicionar</Button>
      </div>
      <div class="flex flex-col gap-2">
        {#each squadMembers as m (m.id)}
          <div class="rounded-lg border bg-card flex justify-between items-center p-3">
            <span class="text-sm">{m.name}</span>
            <Button variant="outline" size="sm" onclick={() => handleRemoveMember(m.id)}>Remover</Button>
          </div>
        {/each}
        {#if squadMembers.length === 0}
          <p class="text-sm text-muted-foreground">Nenhum membro neste time.</p>
        {/if}
      </div>
    </div>
  {/if}
</div>

<Dialog.Root bind:open={showModal}>
  <Dialog.Content class="sm:max-w-[380px]">
    <Dialog.Header>
      <Dialog.Title class="font-heading">Novo Time</Dialog.Title>
    </Dialog.Header>
    <div class="flex flex-col gap-1.5 py-2">
      <Label for="squad-name">Nome *</Label>
      <Input id="squad-name" name="name" bind:value={newName} />
    </div>
    <Dialog.Footer>
      <Button variant="outline" onclick={() => showModal = false}>Cancelar</Button>
      <Button data-testid="btn-save-squad" onclick={handleCreate}>Salvar</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
