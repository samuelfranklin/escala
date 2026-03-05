# TASK-009 — Shell da Aplicação (Layout + Navegação)

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-008 (design system)  
**Estimativa:** M

---

## Descrição

Implementar o shell permanente da aplicação: `Sidebar` com navegação entre rotas, `Header` com breadcrumb e toggle de tema, e o layout responsivo que envolve todas as páginas. O shell deve usar exclusivamente os tokens CSS definidos na TASK-008 e o `themeStore` já implementado.

---

## Escopo

### 1. Roteamento — `src/lib/stores/router.ts`

Sem SvelteKit (app Tauri puro). Implementar roteamento via store:

```typescript
import { writable, derived } from 'svelte/store';

export type Route =
  | 'dashboard'
  | 'members'
  | 'squads'
  | 'events'
  | 'schedule'
  | 'couples'
  | 'availability'
  | 'preferences';

export interface RouteConfig {
  id: Route;
  label: string;
  icon: string;       // nome do ícone lucide
  shortcut: string;   // ex: 'Ctrl+1'
  group: 'overview' | 'records' | 'schedule' | 'settings';
}

export const currentRoute = writable<Route>('dashboard');

export const routeConfig: RouteConfig[] = [
  { id: 'dashboard',    label: 'Dashboard',      icon: 'LayoutDashboard', shortcut: 'Ctrl+1', group: 'overview'  },
  { id: 'members',      label: 'Membros',         icon: 'Users',           shortcut: 'Ctrl+2', group: 'records'   },
  { id: 'squads',       label: 'Times',           icon: 'Layers',          shortcut: 'Ctrl+3', group: 'records'   },
  { id: 'events',       label: 'Eventos',         icon: 'Calendar',        shortcut: 'Ctrl+4', group: 'records'   },
  { id: 'schedule',     label: 'Gerar Escala',    icon: 'ClipboardList',   shortcut: 'Ctrl+5', group: 'schedule'  },
  { id: 'couples',      label: 'Casais',          icon: 'Heart',           shortcut: 'Ctrl+6', group: 'schedule'  },
  { id: 'availability', label: 'Disponibilidade', icon: 'Clock',           shortcut: 'Ctrl+7', group: 'settings'  },
  { id: 'preferences',  label: 'Preferências',    icon: 'Settings',        shortcut: '',       group: 'settings'  },
];

export const currentRouteConfig = derived(
  currentRoute,
  ($route) => routeConfig.find((r) => r.id === $route)!,
);

export function navigate(route: Route) {
  currentRoute.set(route);
}
```

---

### 2. Layout Raiz — `src/routes/+layout.svelte`

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { themeStore } from '$lib/stores/ui';
  import Shell from '$lib/components/layout/Shell.svelte';
  import Toast from '$lib/components/ui/Toast.svelte';

  onMount(() => themeStore.init());
</script>

<Shell>
  <slot />
</Shell>
<Toast />
```

---

### 3. `Shell.svelte` — `src/lib/components/layout/Shell.svelte`

Estrutura DOM:

```
<div class="shell">
  <Sidebar />
  <div class="main-area">
    <Header />
    <main class="content" id="main-content">
      <slot />
    </main>
  </div>
</div>
```

CSS:
```css
.shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  height: 100vh;
  overflow: hidden;
  background: var(--surface-bg);
}
.main-area {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}
```

- Sidebar fixa à esquerda, sempre visível (app desktop)
- `<main id="main-content">` com `tabindex="-1"` para skip-link

---

### 4. `Sidebar.svelte` — `src/lib/components/layout/Sidebar.svelte`

Estrutura:
```
<aside role="navigation" aria-label="Navegação principal">
  ├── Logo + nome "Escala Mídia"
  ├── <nav>
  │   ├── Grupo "Visão Geral" → NavItem (Dashboard)
  │   ├── Grupo "Cadastros" → NavItem ×3
  │   ├── Grupo "Escala" → NavItem ×2
  │   └── Grupo "Configurações" → NavItem ×2
  └── Rodapé da sidebar
      ├── Toggle de tema (ícone ☀/🌙)
      └── Versão do app
```

**`NavItem.svelte`** (sub-componente):
| Prop | Tipo |
|---|---|
| `route` | `RouteConfig` |
| `active` | `boolean` |

- `<button>` (não `<a>`) pois não há URLs reais
- `aria-current="page"` quando `active`
- Tooltip com atalho de teclado (`title` + `data-shortcut`)
- Ícone lucide 18px + label texto

**Atalhos de teclado globais:**
```typescript
// Registrar em onMount do Shell
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key >= '1' && e.key <= '7') {
    e.preventDefault();
    navigate(routeByIndex[Number(e.key) - 1]);
  }
});
```

**Skip link:**
```html
<a href="#main-content" class="skip-link">Pular para o conteúdo</a>
```
(visível apenas no focus, posicionado acima da sidebar)

---

### 5. `Header.svelte` — `src/lib/components/layout/Header.svelte`

Estrutura:
```
<header>
  ├── Breadcrumb: "Escala Mídia > {NomeDaTela}"
  └── Ações do header (slot para botões contextuais por página)
</header>
```

| Prop | Tipo |
|---|---|
| `title` | `string` (derivado do `currentRoute`) |

- `<nav aria-label="Breadcrumb">` com `<ol>` e `<li>`
- Slot `actions` à direita para botões contextuais (ex: "+ Membro")
- Altura fixa: `var(--header-height)` (52px)
- Borda inferior: `1px solid var(--surface-border)`

---

### 6. Roteador de Páginas — `src/routes/+page.svelte`

```svelte
<script lang="ts">
  import { currentRoute } from '$lib/stores/router';
  import DashboardPage     from './dashboard/+page.svelte';
  import MembersPage       from './members/+page.svelte';
  // ... demais imports lazy via await import()
</script>

{#if $currentRoute === 'dashboard'}
  <DashboardPage />
{:else if $currentRoute === 'members'}
  <MembersPage />
{/if}
<!-- ... -->
```

Alternativa: usar `svelte-spa-router` se aprovado pelo tech lead (registrar decisão como ADR).

---

### 7. Página Dashboard — `src/routes/dashboard/+page.svelte`

Placeholder funcional com:
- Título "Dashboard"
- 4 `KpiCard` components: Total Membros, Times Ativos, Eventos, Próxima Escala
- `KpiCard.svelte`: número grande (`--text-3xl`), label (`--text-sm`), cor de destaque

---

## Critérios de Aceite

- [ ] Shell exibe sidebar (220px) + header (52px) + área de conteúdo scrollável
- [ ] Navegação via clique em `NavItem` altera `currentRoute` e renderiza a página correta
- [ ] `NavItem` ativo tem `aria-current="page"` e estilo visual distinto
- [ ] Atalhos `Ctrl+1` a `Ctrl+7` navegam para as rotas correspondentes
- [ ] Skip link "Pular para o conteúdo" aparece no foco e leva ao `<main>`
- [ ] Header exibe breadcrumb correto para cada rota
- [ ] Toggle de tema na sidebar alterna entre dark/light sem FOUC
- [ ] Sidebar usa `var(--surface-sidebar)` (#1a1f2e) em ambos os temas
- [ ] Todos os tokens usados são do design system — zero valores hardcoded
- [ ] Testes de componente (Vitest) com cobertura ≥ 75% para Shell, Sidebar, Header
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Acessível: `role="navigation"`, `aria-label`, foco gerenciado na troca de rota, skip link

---

## Notas Técnicas

- **Svelte 5**: usar `$derived()` para `currentRouteConfig`; `$effect()` para registrar/desregistrar listeners de teclado
- **Sem SvelteKit server**: não usar `load()`, `+page.server.ts` ou qualquer recurso SSR — app é 100% client-side Tauri
- **Lazy loading de páginas**: usar `await import()` dinâmico para não carregar todas as páginas no bundle inicial; envolver com `{#await}` + fallback `<Spinner>`
- **Sidebar sempre visível**: app é desktop-only (1200px+ por definição do spec); não implementar colapso mobile
- **lucide-svelte**: importar cada ícone individualmente no `NavItem` baseado na prop `icon` — considerar um mapa de ícones para evitar switch gigante
- **Foco na troca de rota**: ao navegar, mover o foco para o `<main>` via `document.getElementById('main-content')?.focus()`

---

## Arquivos a Criar / Modificar

```
src/
├── routes/
│   ├── +layout.svelte              ← inicializa themeStore, monta Shell
│   ├── +page.svelte                ← roteador de páginas
│   └── dashboard/
│       └── +page.svelte            ← placeholder com KpiCards
└── lib/
    ├── stores/
    │   └── router.ts               ← currentRoute, routeConfig, navigate()
    └── components/
        └── layout/
            ├── Shell.svelte
            ├── Shell.test.ts
            ├── Sidebar.svelte
            ├── Sidebar.test.ts
            ├── NavItem.svelte
            ├── NavItem.test.ts
            ├── Header.svelte
            ├── Header.test.ts
            └── KpiCard.svelte
```

---

## Progresso

- [ ] `router.ts` — store + `routeConfig` + `navigate()`
- [ ] `Shell.svelte` — grid layout + slot
- [ ] `Sidebar.svelte` — logo, grupos de navegação, rodapé
- [ ] `NavItem.svelte` — ativo, aria, ícone
- [ ] Atalhos de teclado `Ctrl+1..7` registrados
- [ ] Skip link implementado
- [ ] `Header.svelte` — breadcrumb + slot actions
- [ ] Roteador de páginas em `+page.svelte`
- [ ] Dashboard placeholder com `KpiCard`
- [ ] Toggle de tema funcional na sidebar
- [ ] Testes Shell + Sidebar + Header
- [ ] `tsc --noEmit` sem erros
- [ ] `vitest --coverage` ≥ 75%
