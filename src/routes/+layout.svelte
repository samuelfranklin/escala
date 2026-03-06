<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';
  import ToastContainer from '$lib/components/ui/ToastContainer.svelte';

  const navItems = [
    { href: '/dashboard',     label: 'Dashboard',       icon: '◉' },
    { href: '/members',       label: 'Membros',          icon: '👥' },
    { href: '/squads',        label: 'Times',            icon: '🏷️' },
    { href: '/events',        label: 'Eventos',          icon: '📅' },
    { href: '/schedule',      label: 'Escala',           icon: '📋' },
    { href: '/availability',  label: 'Disponibilidade',  icon: '🗓️' },
    { href: '/couples',       label: 'Casais',           icon: '💑' },
  ];
</script>

<div class="grid grid-cols-[var(--sidebar-width)_1fr] min-h-screen">
  <aside class="bg-[var(--surface-sidebar)] text-white flex flex-col sticky top-0 h-screen overflow-y-auto">
    <div class="flex items-center gap-3 px-4 py-6 border-b border-white/10">
      <span class="text-xl">🎬</span>
      <span class="font-bold text-sm">Escala Mídia</span>
    </div>
    <nav class="flex flex-col py-4 px-2 gap-1" aria-label="Navegação principal">
      {#each navItems as item}
        <a
          href={item.href}
          class="flex items-center gap-3 px-3 py-2 rounded-md text-sm no-underline transition-all {$page.url.pathname.startsWith(item.href) ? 'bg-blue-600 text-white' : 'text-white/70 hover:bg-white/10 hover:text-white'}"
          aria-current={$page.url.pathname.startsWith(item.href) ? 'page' : undefined}
        >
          <span aria-hidden="true">{item.icon}</span>
          <span>{item.label}</span>
        </a>
      {/each}
    </nav>
  </aside>

  <main class="p-8 overflow-y-auto" id="main">
    <slot />
  </main>
</div>

<ToastContainer />
