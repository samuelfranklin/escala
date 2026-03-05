<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers, createMember, updateMember, deleteMember } from '$lib/api/members';
  import { getSquads, getSquadMembers } from '$lib/api/squads';
  import { toast } from '$lib/stores/toast';
  import type { Member, CreateMemberDto, UpdateMemberDto, Squad } from '$lib/types';
  import { maskPhone } from '$lib/utils';

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

<div style="display:grid;grid-template-columns:360px 1fr;gap:var(--space-6)">
  <!-- Coluna esquerda: lista -->
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)">
      <h1 style="font-size:var(--text-2xl);font-weight:700">Membros</h1>
      <button class="btn btn-primary" onclick={() => showModal = true}>+ Novo</button>
    </div>

    <input class="input" style="margin-bottom:var(--space-3)" type="search" placeholder="Buscar membro..." bind:value={search} />

    {#if loading}
      <p>Carregando...</p>
    {:else if filtered.length === 0}
      <div style="text-align:center;padding:var(--space-8);color:var(--text-muted)">
        <p style="font-size:var(--text-3xl);margin-bottom:var(--space-2)">👥</p>
        <p>Nenhum membro encontrado.</p>
        <button class="btn btn-primary" style="margin-top:var(--space-3)" onclick={() => showModal = true}>+ Novo Membro</button>
      </div>
    {:else}
      <div style="display:flex;flex-direction:column;gap:var(--space-2)">
        {#each filtered as m (m.id)}
          <div
            class="card"
            style="cursor:pointer;padding:var(--space-3);opacity:{m.active?1:0.5};border-color:{selectedMember?.id===m.id?'var(--color-primary-500)':'var(--surface-border)'}"
            onclick={() => selectMember(m)}
          >
            <div style="display:flex;justify-content:space-between;align-items:center">
              <strong style="font-size:var(--text-sm)">{m.name}</strong>
              <span style="background:{RANK_COLORS[m.rank]}22;color:{RANK_COLORS[m.rank]};padding:2px 8px;border-radius:12px;font-size:var(--text-xs);font-weight:600">
                {RANK_LABELS[m.rank] ?? m.rank}
              </span>
            </div>
            {#if !m.active}<p style="font-size:var(--text-xs);color:var(--color-danger-500);margin-top:2px">Inativo</p>{/if}
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
        <h2 style="font-size:var(--text-xl);font-weight:600;margin-bottom:var(--space-4)">Editar Membro</h2>
        <div style="display:flex;flex-direction:column;gap:var(--space-3);max-width:400px">
          <div class="form-group"><label for="edit-name">Nome *</label><input id="edit-name" class="input" bind:value={editForm.name} /></div>
          <div class="form-group"><label for="edit-email">Email</label><input id="edit-email" class="input" type="email" bind:value={editForm.email} /></div>
          <div class="form-group">
            <label for="edit-phone">Telefone</label>
            <input id="edit-phone" class="input" placeholder="(11) 99999-9999"
              value={editForm.phone ?? ''}
              oninput={(e) => { editForm.phone = maskPhone((e.target as HTMLInputElement).value); }} />
          </div>
          <div class="form-group"><label for="edit-ig">Instagram</label><input id="edit-ig" class="input" placeholder="@usuario" bind:value={editForm.instagram} /></div>
          <div class="form-group">
            <label for="edit-rank">Rank</label>
            <select id="edit-rank" class="input" bind:value={editForm.rank}>
              <option value="recruit">Recruta</option>
              <option value="member">Membro</option>
              <option value="trainer">Treinador</option>
              <option value="leader">Líder</option>
            </select>
          </div>
          <div style="display:flex;gap:var(--space-3)">
            <button class="btn btn-primary" onclick={handleUpdate}>Salvar</button>
            <button class="btn btn-secondary" onclick={() => editing = false}>Cancelar</button>
          </div>
        </div>
      {:else}
        <!-- Painel de detalhes -->
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:var(--space-4)">
          <div>
            <h2 style="font-size:var(--text-xl);font-weight:700">{selectedMember.name}</h2>
            <span style="background:{RANK_COLORS[selectedMember.rank]}22;color:{RANK_COLORS[selectedMember.rank]};padding:3px 10px;border-radius:12px;font-size:var(--text-sm);font-weight:600;display:inline-block;margin-top:var(--space-1)">
              {RANK_LABELS[selectedMember.rank] ?? selectedMember.rank}
            </span>
            {#if !selectedMember.active}
              <span class="badge badge-red" style="margin-left:var(--space-2)">Inativo</span>
            {/if}
          </div>
          <div style="display:flex;gap:var(--space-2)">
            <button class="btn btn-secondary btn-sm" onclick={() => startEdit(selectedMember!)}>✏ Editar</button>
            <button class="btn btn-danger btn-sm" onclick={() => handleDelete(selectedMember!.id)}>🗑 Remover</button>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:var(--space-2);margin-bottom:var(--space-6)">
          {#if selectedMember.phone}
            <p style="font-size:var(--text-sm)">📞 {selectedMember.phone}</p>
          {/if}
          {#if selectedMember.email}
            <p style="font-size:var(--text-sm)">✉ {selectedMember.email}</p>
          {/if}
          {#if selectedMember.instagram}
            <p style="font-size:var(--text-sm)">📷 {selectedMember.instagram}</p>
          {/if}
        </div>

        <div>
          <p style="font-size:var(--text-sm);font-weight:600;color:var(--text-muted);margin-bottom:var(--space-2)">TIMES</p>
          {#if memberSquads.length === 0}
            <p style="font-size:var(--text-sm);color:var(--text-muted)">Sem times associados.</p>
          {:else}
            <div style="display:flex;gap:var(--space-2);flex-wrap:wrap">
              {#each memberSquads as sq (sq.id)}
                <span class="badge badge-blue">{sq.name}</span>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {:else}
    <div style="display:flex;align-items:center;justify-content:center;color:var(--text-muted)">
      <p>Selecione um membro para ver os detalhes.</p>
    </div>
  {/if}
</div>

<!-- Modal de criação -->
{#if showModal}
  <div style="position:fixed;inset:0;background:rgb(0 0 0/0.5);display:flex;align-items:center;justify-content:center;z-index:50">
    <div class="card" style="width:400px">
      <h2 style="font-size:var(--text-lg);font-weight:600;margin-bottom:var(--space-4)">Novo Membro</h2>
      <div style="display:flex;flex-direction:column;gap:var(--space-3)">
        <div class="form-group"><label for="name">Nome *</label><input id="name" class="input" bind:value={form.name} /></div>
        <div class="form-group"><label for="email">Email</label><input id="email" class="input" type="email" bind:value={form.email} /></div>
        <div class="form-group">
          <label for="phone">Telefone</label>
          <input id="phone" class="input" placeholder="(11) 99999-9999"
            value={form.phone}
            oninput={(e) => { form.phone = maskPhone((e.target as HTMLInputElement).value); }} />
        </div>
        <div class="form-group"><label for="instagram">Instagram</label><input id="instagram" class="input" placeholder="@usuario" bind:value={form.instagram} /></div>
        <div class="form-group">
          <label for="rank">Rank</label>
          <select id="rank" class="input" bind:value={form.rank}>
            <option value="recruit">Recruta</option>
            <option value="member">Membro</option>
            <option value="trainer">Treinador</option>
            <option value="leader">Líder</option>
          </select>
        </div>
        <div style="display:flex;gap:var(--space-3);justify-content:flex-end">
          <button class="btn btn-secondary" onclick={() => showModal = false}>Cancelar</button>
          <button class="btn btn-primary" onclick={handleCreate}>Salvar</button>
        </div>
      </div>
    </div>
  </div>
{/if}


  let members = $state<Member[]>([]);
  let loading = $state(true);
  let search = $state('');
  let showModal = $state(false);
  let form = $state<CreateMemberDto>({ name: '', email: '', phone: '', instagram: '', rank: 'member' });

  const filtered = $derived(
    members.filter(m => m.name.toLowerCase().includes(search.toLowerCase()))
  );

  onMount(load);

  async function load() {
    loading = true;
    try { members = await getMembers(); }
    catch { toast.error('Erro ao carregar membros'); }
    finally { loading = false; }
  }

  async function handleCreate() {
    try {
      await createMember(form);
      toast.success('Membro criado com sucesso!');
      showModal = false;
      form = { name: '', email: '', phone: '', instagram: '', rank: 'member' };
      await load();
    } catch (e: any) { toast.error(e.message || 'Erro ao criar membro'); }
  }

  async function handleDelete(id: string) {
    if (!confirm('Remover membro?')) return;
    try { await deleteMember(id); toast.success('Membro removido.'); await load(); }
    catch (e: any) { toast.error(e.message || 'Erro ao remover'); }
  }
</script>

<div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-6)">
    <h1 style="font-size:var(--text-2xl);font-weight:700">Membros</h1>
    <button class="btn btn-primary" onclick={() => showModal = true}>+ Novo Membro</button>
  </div>

  <input class="input" style="max-width:300px;margin-bottom:var(--space-4)" type="search" placeholder="Buscar membro..." bind:value={search} />

  {#if loading}
    <p>Carregando...</p>
  {:else if filtered.length === 0}
    <p style="color:var(--text-muted)">Nenhum membro encontrado.</p>
  {:else}
    <div style="display:grid;gap:var(--space-3)">
      {#each filtered as m (m.id)}
        <div class="card" style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <strong>{m.name}</strong>
            <span class="badge badge-blue" style="margin-left:var(--space-2)">{m.rank}</span>
            {#if !m.active}<span class="badge badge-red" style="margin-left:var(--space-2)">Inativo</span>{/if}
            {#if m.email}<p style="font-size:var(--text-sm);color:var(--text-muted)">{m.email}</p>{/if}
          </div>
          <button class="btn btn-danger btn-sm" onclick={() => handleDelete(m.id)}>Remover</button>
        </div>
      {/each}
    </div>
  {/if}

  {#if showModal}
    <div style="position:fixed;inset:0;background:rgb(0 0 0/0.5);display:flex;align-items:center;justify-content:center;z-index:50">
      <div class="card" style="width:400px">
        <h2 style="font-size:var(--text-lg);font-weight:600;margin-bottom:var(--space-4)">Novo Membro</h2>
        <div style="display:flex;flex-direction:column;gap:var(--space-3)">
          <div class="form-group"><label for="name">Nome *</label><input id="name" class="input" bind:value={form.name} /></div>
          <div class="form-group"><label for="email">Email</label><input id="email" class="input" type="email" bind:value={form.email} /></div>
          <div class="form-group"><label for="phone">Telefone</label><input id="phone" class="input" bind:value={form.phone} /></div>
          <div class="form-group"><label for="instagram">Instagram</label><input id="instagram" class="input" bind:value={form.instagram} /></div>
          <div class="form-group">
            <label for="rank">Rank</label>
            <select id="rank" class="input" bind:value={form.rank}>
              <option value="recruit">Recruta</option>
              <option value="member">Membro</option>
              <option value="trainer">Treinador</option>
              <option value="leader">Líder</option>
            </select>
          </div>
          <div style="display:flex;gap:var(--space-3);justify-content:flex-end">
            <button class="btn btn-secondary" onclick={() => showModal = false}>Cancelar</button>
            <button class="btn btn-primary" onclick={handleCreate}>Salvar</button>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
