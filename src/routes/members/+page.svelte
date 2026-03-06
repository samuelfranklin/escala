<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers, createMember, updateMember, deleteMember } from '$lib/api/members';
  import { getSquads, getSquadMembers } from '$lib/api/squads';
  import { toast } from '$lib/stores/toast';
  import type { Member, CreateMemberDto, UpdateMemberDto, Squad } from '$lib/types';
  import { maskPhone } from '$lib/utils';
  import * as Dialog from '$lib/components/ui/dialog/index.js';
  import * as Select from '$lib/components/ui/select/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import Icon from '@iconify/svelte';

  const RANK_LABELS: Record<string, string> = { leader: 'Líder', trainer: 'Treinador', member: 'Membro', recruit: 'Recruta' };
  const RANK_COLORS: Record<string, string> = { leader: '#fbbf24', trainer: '#818cf8', member: '#4ade80', recruit: '#9ca3af' };

  let members = $state<Member[]>([]);
  let allSquads = $state<Squad[]>([]);
  let selectedMember = $state<Member | null>(null);
  let memberSquads = $state<Squad[]>([]);
  let loading = $state(true);
  let editing = $state(false);
  let showModal = $state(false);
  let search = $state('');

  let form = $state<CreateMemberDto>({ name: '', email: '', phone: '', instagram: '', rank: 'member' });
  let editForm = $state<UpdateMemberDto>({});

  const filtered = $derived(
    members.filter(m => m.name.toLowerCase().includes(search.toLowerCase()))
  );

  onMount(load);

  async function load() {
    loading = true;
    try { [members, allSquads] = await Promise.all([getMembers(), getSquads()]); }
    catch { toast.error('Erro ao carregar membros'); }
    finally { loading = false; }
  }

  async function selectMember(m: Member) {
    selectedMember = m;
    editing = false;
    // Buscar quais squads têm esse membro
    const results = await Promise.all(allSquads.map(s => getSquadMembers(s.id)));
    memberSquads = allSquads.filter((s, i) => results[i].some(sm => sm.id === m.id));
  }

  async function handleCreate() {
    if (!form.name.trim()) return;
    try {
      const created = await createMember({ ...form, phone: form.phone || undefined, email: form.email || undefined, instagram: form.instagram || undefined });
      toast.success('Membro criado com sucesso!');
      showModal = false;
      form = { name: '', email: '', phone: '', instagram: '', rank: 'member' };
      await load();
      await selectMember(created);
    } catch (e: any) { toast.error(e.message || 'Erro ao criar membro'); }
  }

  async function handleUpdate() {
    if (!selectedMember) return;
    try {
      const updated = await updateMember(selectedMember.id, editForm);
      toast.success('Membro atualizado!');
      editing = false;
      await load();
      selectedMember = updated;
    } catch (e: any) { toast.error(e.message || 'Erro ao atualizar'); }
  }

  async function handleDelete(id: string) {
    if (!confirm('Remover membro?')) return;
    try {
      await deleteMember(id);
      toast.success('Membro removido.');
      if (selectedMember?.id === id) selectedMember = null;
      await load();
    } catch (e: any) { toast.error(e.message || 'Erro ao remover'); }
  }

  function startEdit(m: Member) {
    editForm = { name: m.name, email: m.email ?? '', phone: m.phone ?? '', instagram: m.instagram ?? '', rank: m.rank };
    editing = true;
  }
</script>

<div data-testid="members-page" class="grid grid-cols-[360px_1fr] gap-6">
  <!-- Coluna esquerda: lista -->
  <div>
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-heading font-bold">Membros</h1>
      <Button data-testid="btn-new-member" onclick={() => showModal = true}>
        <Icon icon="lucide:plus" class="size-4 mr-1" /> Novo
      </Button>
    </div>

    <Input type="search" placeholder="Buscar membro..." bind:value={search} class="mb-3" />

    {#if loading}
      <div class="flex flex-col gap-2">
        {#each [1,2,3] as _}
          <div class="h-14 rounded-lg bg-muted animate-pulse"></div>
        {/each}
      </div>
    {:else if filtered.length === 0}
      <div class="text-center p-8 text-muted-foreground">
        <Icon icon="lucide:users" class="size-10 mx-auto mb-2 opacity-30" />
        <p class="mb-3">Nenhum membro encontrado.</p>
        <Button onclick={() => showModal = true}>
          <Icon icon="lucide:plus" class="size-4 mr-1" /> Novo Membro
        </Button>
      </div>
    {:else}
      <div class="flex flex-col gap-2">
        {#each filtered as m (m.id)}
          <div
            data-testid="member-row"
            class="rounded-lg border bg-card p-3 cursor-pointer transition-all hover:bg-accent {m.active ? '' : 'opacity-50'} {selectedMember?.id===m.id ? 'ring-2 ring-primary' : ''}"
            onclick={() => selectMember(m)}
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === 'Enter' && selectMember(m)}
          >
            <div class="flex justify-between items-center">
              <strong class="text-sm">{m.name}</strong>
              <span style="background:{RANK_COLORS[m.rank]}22;color:{RANK_COLORS[m.rank]};padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600">
                {RANK_LABELS[m.rank] ?? m.rank}
              </span>
            </div>
            {#if !m.active}<p class="text-xs text-destructive mt-0.5">Inativo</p>{/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Coluna direita: detalhe / edição -->
  {#if selectedMember}
    <div>
      {#if editing}
        <!-- Formulário de edição inline -->
        <h2 class="text-xl font-heading font-semibold mb-5">Editar Membro</h2>
        <div class="flex flex-col gap-4 max-w-[400px]">
          <div class="flex flex-col gap-1.5">
            <Label for="edit-name">Nome *</Label>
            <Input id="edit-name" bind:value={editForm.name} />
          </div>
          <div class="flex flex-col gap-1.5">
            <Label for="edit-email">Email</Label>
            <Input id="edit-email" type="email" bind:value={editForm.email} />
          </div>
          <div class="flex flex-col gap-1.5">
            <Label for="edit-phone">Telefone</Label>
            <Input id="edit-phone" placeholder="(11) 99999-9999"
              value={editForm.phone ?? ''}
              oninput={(e: Event) => { editForm.phone = maskPhone((e.target as HTMLInputElement).value); }} />
          </div>
          <div class="flex flex-col gap-1.5">
            <Label for="edit-ig">Instagram</Label>
            <Input id="edit-ig" placeholder="@usuario" bind:value={editForm.instagram} />
          </div>
          <div class="flex flex-col gap-1.5">
            <Label>Rank</Label>
            <Select.Root type="single" onValueChange={(v: any) => editForm.rank = v as typeof editForm.rank}>
              <Select.Trigger>
                {RANK_LABELS[editForm.rank ?? 'member'] ?? 'Selecionar rank'}
              </Select.Trigger>
              <Select.Content>
                <Select.Item value="recruit">Recruta</Select.Item>
                <Select.Item value="member">Membro</Select.Item>
                <Select.Item value="trainer">Treinador</Select.Item>
                <Select.Item value="leader">Líder</Select.Item>
              </Select.Content>
            </Select.Root>
          </div>
          <div class="flex gap-3 pt-1">
            <Button onclick={handleUpdate}>Salvar</Button>
            <Button variant="outline" onclick={() => editing = false}>Cancelar</Button>
          </div>
        </div>
      {:else}
        <!-- Painel de detalhes -->
        <div class="flex justify-between items-start mb-5">
          <div>
            <h2 class="text-xl font-heading font-bold">{selectedMember.name}</h2>
            <div class="flex items-center gap-2 mt-1.5">
              <span style="background:{RANK_COLORS[selectedMember.rank]}22;color:{RANK_COLORS[selectedMember.rank]};padding:3px 10px;border-radius:12px;font-size:0.875rem;font-weight:600">
                {RANK_LABELS[selectedMember.rank] ?? selectedMember.rank}
              </span>
              {#if !selectedMember.active}
                <Badge variant="destructive">Inativo</Badge>
              {/if}
            </div>
          </div>
          <div class="flex gap-2">
            <Button variant="outline" size="sm" onclick={() => startEdit(selectedMember!)}>
              <Icon icon="lucide:pencil" class="size-4 mr-1" /> Editar
            </Button>
            <Button variant="destructive" size="sm" onclick={() => handleDelete(selectedMember!.id)}>
              <Icon icon="lucide:trash-2" class="size-4 mr-1" /> Remover
            </Button>
          </div>
        </div>

        <div class="flex flex-col gap-2 mb-6">
          {#if selectedMember.phone}
            <p class="text-sm flex items-center gap-2">
              <Icon icon="lucide:phone" class="size-4 text-muted-foreground" />
              {selectedMember.phone}
            </p>
          {/if}
          {#if selectedMember.email}
            <p class="text-sm flex items-center gap-2">
              <Icon icon="lucide:mail" class="size-4 text-muted-foreground" />
              {selectedMember.email}
            </p>
          {/if}
          {#if selectedMember.instagram}
            <p class="text-sm flex items-center gap-2">
              <Icon icon="lucide:instagram" class="size-4 text-muted-foreground" />
              {selectedMember.instagram}
            </p>
          {/if}
        </div>

        <div>
          <p class="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-2">Times</p>
          {#if memberSquads.length === 0}
            <p class="text-sm text-muted-foreground">Sem times associados.</p>
          {:else}
            <div class="flex gap-2 flex-wrap">
              {#each memberSquads as sq (sq.id)}
                <Badge variant="secondary">{sq.name}</Badge>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {:else}
    <div class="flex items-center justify-center text-muted-foreground">
      <p>Selecione um membro para ver os detalhes.</p>
    </div>
  {/if}
</div>

<!-- Modal de criação -->
<Dialog.Root bind:open={showModal}>
  <Dialog.Content class="sm:max-w-[420px]">
    <Dialog.Header>
      <Dialog.Title class="font-heading">Novo Membro</Dialog.Title>
    </Dialog.Header>
    <div class="flex flex-col gap-4 py-2">
      <div class="flex flex-col gap-1.5">
        <Label for="name">Nome *</Label>
        <Input id="name" name="name" bind:value={form.name} />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="email">Email</Label>
        <Input id="email" type="email" bind:value={form.email} />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="phone">Telefone</Label>
        <Input id="phone" placeholder="(11) 99999-9999"
          value={form.phone}
          oninput={(e: Event) => { form.phone = maskPhone((e.target as HTMLInputElement).value); }} />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="instagram">Instagram</Label>
        <Input id="instagram" placeholder="@usuario" bind:value={form.instagram} />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label>Rank</Label>
        <Select.Root type="single" onValueChange={(v: any) => form.rank = v as typeof form.rank}>
          <Select.Trigger>
            {RANK_LABELS[form.rank ?? 'member'] ?? 'Selecionar rank'}
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="recruit">Recruta</Select.Item>
            <Select.Item value="member">Membro</Select.Item>
            <Select.Item value="trainer">Treinador</Select.Item>
            <Select.Item value="leader">Líder</Select.Item>
          </Select.Content>
        </Select.Root>
      </div>
    </div>
    <Dialog.Footer>
      <Button variant="outline" onclick={() => showModal = false}>Cancelar</Button>
      <Button data-testid="btn-save-member" onclick={handleCreate}>Salvar</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>

