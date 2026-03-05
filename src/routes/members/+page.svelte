<script lang="ts">
  import { onMount } from 'svelte';
  import { getMembers, createMember, deleteMember } from '$lib/api/members';
  import { toast } from '$lib/stores/toast';
  import type { Member, CreateMemberDto } from '$lib/types';

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
