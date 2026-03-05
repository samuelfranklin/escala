<script lang="ts">
  import { onMount } from 'svelte';
  import { getEvents, createEvent, deleteEvent } from '$lib/api/events';
  import type { Event, CreateEventDto } from '$lib/types';

  let events = $state<Event[]>([]);
  let loading = $state(true);
  let showModal = $state(false);
  let form = $state<CreateEventDto>({ name: '', event_date: '', event_type: 'regular' });

  onMount(load);

  async function load() {
    loading = true;
    events = await getEvents();
    loading = false;
  }

  async function handleCreate() {
    if (!form.name.trim() || !form.event_date) return;
    await createEvent(form);
    showModal = false;
    form = { name: '', event_date: '', event_type: 'regular' };
    await load();
  }
</script>

<div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-6)">
    <h1 style="font-size:var(--text-2xl);font-weight:700">Eventos</h1>
    <button class="btn btn-primary" onclick={() => showModal = true}>+ Novo Evento</button>
  </div>
  {#if loading}<p>Carregando...</p>
  {:else}
    <div style="display:grid;gap:var(--space-3)">
      {#each events as e (e.id)}
        <div class="card" style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <strong>{e.name}</strong>
            <span class="badge badge-blue" style="margin-left:var(--space-2)">{e.event_type}</span>
            <p style="font-size:var(--text-sm);color:var(--text-muted)">{e.event_date}</p>
          </div>
          <button class="btn btn-danger btn-sm" onclick={() => deleteEvent(e.id).then(load)}>Remover</button>
        </div>
      {/each}
    </div>
  {/if}
</div>

{#if showModal}
  <div style="position:fixed;inset:0;background:rgb(0 0 0/0.5);display:flex;align-items:center;justify-content:center;z-index:50">
    <div class="card" style="width:400px">
      <h2 style="font-size:var(--text-lg);font-weight:600;margin-bottom:var(--space-4)">Novo Evento</h2>
      <div style="display:flex;flex-direction:column;gap:var(--space-3)">
        <div class="form-group"><label for="ev-name">Nome *</label><input id="ev-name" class="input" bind:value={form.name} /></div>
        <div class="form-group"><label for="ev-date">Data *</label><input id="ev-date" class="input" type="date" bind:value={form.event_date} /></div>
        <div class="form-group"><label for="ev-type">Tipo</label>
          <select id="ev-type" class="input" bind:value={form.event_type}>
            <option value="regular">Regular</option>
            <option value="special">Especial</option>
            <option value="training">Treinamento</option>
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
