# SPEC-LAYOUT — Migração do Shell de Layout para shadcn-svelte Sidebar

**Arquivo alvo:** `src/routes/+layout.svelte`  
**Novo componente:** `src/lib/components/AppSidebar.svelte`  
**Status:** WAITING  
**Depende de:** TASK-024 (infra shadcn instalada)  
**Task de implementação:** TASK-025-FRONTEND-shadcn-layout-shell

---

## Descrição

Substituir o layout de grid manual com `<aside>` fixo e emoji-icons por um layout completo usando `<Sidebar.Provider>` + `<Sidebar.Root collapsible="icon">` do shadcn-svelte. O sidebar deve suportar colapso para modo "icon-only". O `<ToastContainer>` customizado é substituído pelo `<Toaster />` do `sonner` (já incluído no shadcn).

A `<slot />` do Svelte 4 é substituída por `{@render children()}` (Svelte 5 snippets).

---

## Componentes shadcn a instalar

```bash
pnpm dlx shadcn-svelte@latest add sidebar sonner
```

| Componente | Import |
|---|---|
| `Sidebar.*` | `import * as Sidebar from "$lib/components/ui/sidebar/index.js"` |
| `Toaster` | `import { Toaster } from "$lib/components/ui/sonner/index.js"` |
| `Icon` | `import { Icon } from "@iconify/svelte"` |

---

## O que NÃO muda

| Item | Razão |
|---|---|
| Todo o bloco `<script lang="ts">` | Lógica de navegação permanece igual |
| Array `navItems` com `href` e `label` | Apenas `icon` muda de emoji para string lucide |
| Lógica de `$page.url.pathname.startsWith(item.href)` | Permanece para detecção de rota ativa |
| Atributo `aria-current="page"` no link ativo | Acessibilidade mantida |
| Import de `../app.css` | Permanece no layout |

---

## Mapeamento de alterações

| Atual | Novo |
|---|---|
| `<div class="grid grid-cols-[var(--sidebar-width)_1fr]">` | `<Sidebar.Provider>` wrapping tudo |
| `<aside class="bg-[var(--surface-sidebar)]...">` | `<Sidebar.Root collapsible="icon">` dentro de `AppSidebar.svelte` |
| `<div class="flex items-center gap-3 px-4 py-6...">` logo area | `<Sidebar.Header>` com `<Icon icon="lucide:clapperboard" />` + texto |
| `<nav class="flex flex-col py-4 px-2 gap-1">` | `<Sidebar.Content>` → `<Sidebar.Group>` → `<Sidebar.Menu>` |
| `<a ...>` nav item com emoji `item.icon` | `<Sidebar.MenuItem>` → `<Sidebar.MenuButton>` → `{#snippet child({props})}<a>` |
| `item.icon` como emoji (`◉`, `👥`, etc.) | `item.icon` como string Lucide (`"lucide:layout-dashboard"`, etc.) |
| `<main class="p-8 overflow-y-auto">` | `<Sidebar.Inset>` com `<main>` interno |
| `<slot />` | `{@render children()}` |
| `<ToastContainer />` | `<Toaster />` do sonner |

### Mapeamento de ícones de navegação

| Rota | Emoji atual | Lucide novo |
|---|---|---|
| `/dashboard` | `◉` | `"lucide:layout-dashboard"` |
| `/members` | `👥` | `"lucide:users"` |
| `/squads` | `🏷️` | `"lucide:layers"` |
| `/events` | `📅` | `"lucide:calendar"` |
| `/schedule` | `📋` | `"lucide:clipboard-list"` |
| `/availability` | `🗓️` | `"lucide:calendar-check"` |
| `/couples` | `💑` | `"lucide:heart"` |

---

## Código de referência

### `src/routes/+layout.svelte` (após migração)

```svelte
<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';
  import AppSidebar from '$lib/components/AppSidebar.svelte';
  import * as Sidebar from '$lib/components/ui/sidebar/index.js';
  import { Toaster } from '$lib/components/ui/sonner/index.js';

  // INALTERADO: mesma definição de navItems, apenas icon atualizado para string lucide
  const navItems = [
    { href: '/dashboard',    label: 'Dashboard',      icon: 'lucide:layout-dashboard' },
    { href: '/members',      label: 'Membros',         icon: 'lucide:users' },
    { href: '/squads',       label: 'Times',           icon: 'lucide:layers' },
    { href: '/events',       label: 'Eventos',         icon: 'lucide:calendar' },
    { href: '/schedule',     label: 'Escala',          icon: 'lucide:clipboard-list' },
    { href: '/availability', label: 'Disponibilidade', icon: 'lucide:calendar-check' },
    { href: '/couples',      label: 'Casais',          icon: 'lucide:heart' },
  ];

  let { children } = $props();
</script>

<Sidebar.Provider>
  <AppSidebar {navItems} />
  <Sidebar.Inset>
    <header class="flex h-14 items-center gap-2 border-b px-4">
      <Sidebar.Trigger class="-ml-1" />
    </header>
    <main class="p-8 overflow-y-auto" id="main">
      {@render children()}
    </main>
  </Sidebar.Inset>
</Sidebar.Provider>

<Toaster richColors position="bottom-right" />
```

### `src/lib/components/AppSidebar.svelte` (novo arquivo)

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import { Icon } from '@iconify/svelte';
  import * as Sidebar from '$lib/components/ui/sidebar/index.js';

  let { navItems }: { navItems: { href: string; label: string; icon: string }[] } = $props();
</script>

<Sidebar.Root collapsible="icon">
  <Sidebar.Header>
    <div class="flex items-center gap-2 px-1 py-1">
      <Icon icon="lucide:clapperboard" class="size-5 shrink-0" />
      <span class="font-bold text-sm truncate">Escala Mídia</span>
    </div>
  </Sidebar.Header>

  <Sidebar.Content>
    <Sidebar.Group>
      <Sidebar.Menu>
        {#each navItems as item (item.href)}
          <Sidebar.MenuItem>
            <Sidebar.MenuButton
              isActive={$page.url.pathname.startsWith(item.href)}
              tooltip={item.label}
            >
              {#snippet child({ props })}
                <a href={item.href} {...props} aria-current={$page.url.pathname.startsWith(item.href) ? 'page' : undefined}>
                  <Icon icon={item.icon} class="size-4" />
                  <span>{item.label}</span>
                </a>
              {/snippet}
            </Sidebar.MenuButton>
          </Sidebar.MenuItem>
        {/each}
      </Sidebar.Menu>
    </Sidebar.Group>
  </Sidebar.Content>
</Sidebar.Root>
```

---

## Checklist de implementação

- [ ] Instalar componentes `sidebar` e `sonner` via CLI shadcn-svelte
- [ ] Criar `src/lib/components/AppSidebar.svelte` com estrutura `<Sidebar.Root collapsible="icon">`
- [ ] Atualizar `+layout.svelte`: substituir grid/aside por `<Sidebar.Provider>` + `<Sidebar.Inset>`
- [ ] Substituir `<slot />` por `{@render children()}` (Svelte 5)
- [ ] Substituir emojis no `navItems.icon` pelas strings Lucide correspondentes
- [ ] Substituir `<ToastContainer />` por `<Toaster richColors position="bottom-right" />`
- [ ] Importar `Toaster` de `$lib/components/ui/sonner/index.js` (não de `svelte-sonner` diretamente)
- [ ] Verificar que `aria-current="page"` permanece no link ativo
- [ ] Testar colapso do sidebar (modo icon-only) em janela estreita
- [ ] `pnpm typecheck` sem erros
- [ ] `pnpm dev` — sidebar funcional com navegação entre todas as rotas
- [ ] E2E: testes existentes não quebram (navegação ainda usa os mesmos `href`)
