<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';

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

<div class="app-shell">
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="sidebar-logo">🎬</span>
      <span class="sidebar-title">Escala Mídia</span>
    </div>
    <nav class="sidebar-nav" aria-label="Navegação principal">
      {#each navItems as item}
        <a
          href={item.href}
          class="nav-item"
          class:active={$page.url.pathname.startsWith(item.href)}
          aria-current={$page.url.pathname.startsWith(item.href) ? 'page' : undefined}
        >
          <span class="nav-icon" aria-hidden="true">{item.icon}</span>
          <span class="nav-label">{item.label}</span>
        </a>
      {/each}
    </nav>
  </aside>

  <main class="main-content" id="main">
    <slot />
  </main>
</div>

<style>
  .app-shell {
    display: grid;
    grid-template-columns: var(--sidebar-width) 1fr;
    min-height: 100vh;
  }
  .sidebar {
    background: var(--surface-sidebar);
    color: var(--text-on-dark);
    display: flex; flex-direction: column;
    position: sticky; top: 0; height: 100vh;
    overflow-y: auto;
  }
  .sidebar-header {
    display: flex; align-items: center; gap: var(--space-3);
    padding: var(--space-6) var(--space-4);
    border-bottom: 1px solid rgb(255 255 255 / 0.1);
  }
  .sidebar-logo { font-size: var(--text-xl); }
  .sidebar-title { font-weight: 700; font-size: var(--text-sm); }
  .sidebar-nav { display: flex; flex-direction: column; padding: var(--space-4) var(--space-2); gap: var(--space-1); }
  .nav-item {
    display: flex; align-items: center; gap: var(--space-3);
    padding: var(--space-2) var(--space-3); border-radius: var(--radius-md);
    color: rgb(255 255 255 / 0.7); text-decoration: none;
    font-size: var(--text-sm); transition: all var(--transition-fast);
  }
  .nav-item:hover { background: rgb(255 255 255 / 0.1); color: #fff; }
  .nav-item.active { background: var(--color-primary-600); color: #fff; }
  .main-content { padding: var(--space-8); overflow-y: auto; }
</style>
