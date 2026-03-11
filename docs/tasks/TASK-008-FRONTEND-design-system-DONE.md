# TASK-008 — Setup do Design System

**Domínio:** FRONTEND  
**Status:** DONE  
**Prioridade:** P0  
**Depende de:** TASK-001 (scaffold Tauri + Svelte)  
**Estimativa:** M

---

## Descrição

Implementar a fundação visual do app **Escala Mídia**: CSS custom properties (tokens), utilitários globais e a biblioteca de componentes UI primitivos reutilizáveis em Svelte 5.

Esta task **bloqueia todas as demais tasks de frontend**. Nenhuma página ou shell deve ser construída antes que os tokens e componentes primitivos estejam testados e aprovados.

---

## Escopo

### 1. Tokens CSS — `src/app.css`

Implementar exatamente a paleta definida na spec §8:

```css
:root {
  /* Primária — azul */
  --color-primary-50:  #eef2ff;
  --color-primary-100: #e0e7ff;
  --color-primary-400: #818cf8;
  --color-primary-500: #4f7ef8;   /* brand principal */
  --color-primary-600: #3b6ef0;
  --color-primary-900: #1e2a5e;

  /* Superfícies (dark — padrão do app) */
  --surface-bg:        #0f1117;
  --surface-sidebar:   #1a1f2e;
  --surface-card:      #1e2438;
  --surface-elevated:  #252b40;
  --surface-border:    #2d3552;

  /* Textos */
  --text-primary:   #e8eaf6;
  --text-secondary: #8892b0;
  --text-muted:     #4a5568;

  /* Feedback */
  --color-success: #4ade80;
  --color-warning: #fbbf24;
  --color-error:   #f87171;
  --color-info:    #60a5fa;

  /* Patentes/Ranks */
  --rank-leader:   #fbbf24;
  --rank-trainer:  #818cf8;
  --rank-member:   #4ade80;
  --rank-recruit:  #9ca3af;

  /* Tipografia */
  --text-xs:   11px;
  --text-sm:   13px;
  --text-base: 15px;
  --text-lg:   17px;
  --text-xl:   20px;
  --text-2xl:  24px;
  --text-3xl:  30px;

  /* Pesos tipográficos */
  --font-normal:    400;
  --font-medium:    500;
  --font-semibold:  600;
  --font-bold:      700;

  /* Espaçamento (escala 4px) */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Bordas */
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:   12px;
  --radius-full: 9999px;

  /* Sombras */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);

  /* Transições */
  --transition-fast:   100ms ease;
  --transition-normal: 200ms ease;
  --transition-slow:   300ms ease;

  /* Layout */
  --sidebar-width:    220px;
  --header-height:    52px;
  --min-click-target: 36px;
}

[data-theme="light"] {
  --surface-bg:       #f8fafc;
  --surface-sidebar:  #1a1f2e; /* sidebar sempre escura */
  --surface-card:     #ffffff;
  --surface-elevated: #f1f5f9;
  --surface-border:   #e2e8f0;
  --text-primary:     #0f172a;
  --text-secondary:   #475569;
  --text-muted:       #94a3b8;
}

/* Redução de movimento */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Fonte:** Instalar `@fontsource/inter`; importar pesos 400, 500, 600, 700 no topo do `app.css`; aplicar `font-family: 'Inter', sans-serif` no `body`.

---

### 2. Store de Tema — `src/lib/stores/ui.ts`

```typescript
import { writable } from 'svelte/store';
import { Store } from '@tauri-apps/plugin-store';

export type Theme = 'dark' | 'light';

function createThemeStore() {
  const { subscribe, set, update } = writable<Theme>('dark');

  return {
    subscribe,

    /** Chamado em onMount do +layout.svelte */
    init: async () => {
      const store = await Store.load('preferences.json');
      const saved = await store.get<Theme>('theme');
      const preferred = window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'dark';
      const theme = saved ?? preferred;
      document.documentElement.setAttribute('data-theme', theme);
      set(theme);
    },

    toggle: async () => {
      update((current) => {
        const next: Theme = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        Store.load('preferences.json').then((s) => s.set('theme', next));
        return next;
      });
    },
  };
}

export const themeStore = createThemeStore();
export const sidebarCollapsed = writable<boolean>(false);
```

Regras:
- Atribuir `data-theme` no `<html>` **antes do primeiro paint** — evitar FOUC com script inline em `app.html`
- Fallback: `prefers-color-scheme` quando não há preferência salva
- Padrão do app: **dark**

---

### 3. Componentes UI Primitivos — `src/lib/components/ui/`

#### `Button.svelte`
| Prop | Tipo | Padrão |
|---|---|---|
| `variant` | `'primary' \| 'secondary' \| 'ghost' \| 'danger' \| 'icon'` | `'primary'` |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` |
| `disabled` | `boolean` | `false` |
| `loading` | `boolean` | `false` |
| `type` | `'button' \| 'submit' \| 'reset'` | `'button'` |

- Quando `loading=true`: renderizar `<Spinner>` inline, `pointer-events: none`, `aria-busy="true"`
- Target mínimo 36×36px (`sm`), 44×44px (`md`/`lg`)
- `aria-disabled` quando `disabled`; não usar `disabled` nativo junto com `loading` (mantém foco)

#### `Input.svelte`
| Prop | Tipo | Padrão |
|---|---|---|
| `value` | `string` | `''` |
| `label` | `string` | — |
| `placeholder` | `string` | — |
| `error` | `string \| undefined` | — |
| `disabled` | `boolean` | `false` |
| `icon` | `Component \| undefined` | — |
| `type` | `HTMLInputTypeAttribute` | `'text'` |
| `id` | `string` | auto-gerado (`crypto.randomUUID()`) |

- `<label for={id}>` sempre associado
- Mensagem de erro: `<span role="alert">` abaixo do campo
- Ícone renderizado à esquerda com padding ajustado automaticamente
- Estado de foco: outline com `--color-primary-500`

#### `Select.svelte`
| Prop | Tipo | Padrão |
|---|---|---|
| `value` | `string` | `''` |
| `options` | `Array<{ value: string; label: string }>` | `[]` |
| `label` | `string` | — |
| `placeholder` | `string` | `'Selecionar...'` |
| `error` | `string \| undefined` | — |
| `disabled` | `boolean` | `false` |
| `searchable` | `boolean` | `false` |

- Versão `searchable`: dropdown customizado com `<input>` de filtro interno
- Navegação: `ArrowUp/Down` move highlight, `Enter` seleciona, `Escape` fecha
- ARIA: `role="combobox"`, `aria-expanded`, `aria-haspopup="listbox"`, `aria-activedescendant`
- Opções: `role="option"`, `aria-selected`

#### `Modal.svelte`
| Prop | Tipo | Padrão |
|---|---|---|
| `open` | `boolean` | `false` |
| `title` | `string` | — |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` |
| `onclose` | `() => void` | — |

- Larguras: `sm`=400px, `md`=600px, `lg`=800px
- Focus trap: aplicar `inert` no elemento irmão do modal enquanto aberto
- Fechar: `Escape`, clique no backdrop semitransparente, botão ✕ no cabeçalho
- ARIA: `role="dialog"`, `aria-modal="true"`, `aria-labelledby={titleId}`
- Animação de entrada/saída (respeitando `prefers-reduced-motion`)
- Renderizado via `mount()` no `document.body` para isolamento de z-index

#### `Badge.svelte`
| Prop | Tipo |
|---|---|
| `variant` | `'leader' \| 'trainer' \| 'member' \| 'recruit' \| 'fixed' \| 'seasonal' \| 'special' \| 'success' \| 'warning' \| 'error' \| 'info'` |
| `label` | `string` |

- Cores de patente via `--rank-leader`, `--rank-trainer`, `--rank-member`, `--rank-recruit`
- Cores de tipo de evento: `fixed`→info, `seasonal`→warning, `special`→primary
- `role="status"` para leitores de tela

#### `Spinner.svelte`
| Prop | Tipo | Padrão |
|---|---|---|
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` |
| `label` | `string` | `'Carregando...'` |

- SVG com animação `stroke-dashoffset` ou rotação; `role="status"`, `aria-label={label}`
- Tamanhos: `sm`=16px, `md`=24px, `lg`=40px
- `@media (prefers-reduced-motion: reduce)`: sem animação, exibir ponto estático

#### `Toast.svelte` + `toast.store.ts`

Store:
```typescript
interface ToastItem {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  duration?: number; // ms — padrão 4000
}
export const toastStore = /* writable array com push/dismiss */;
```

- Container fixo `position: fixed; bottom: var(--space-6); right: var(--space-6)`
- `aria-live="polite"` no container; `aria-live="assertive"` para `type='error'`
- Auto-dismiss com `setTimeout`; botão ✕ para dismiss manual
- Animação de slide-in/out (respeitando `prefers-reduced-motion`)

#### `EmptyState.svelte`
| Prop | Tipo |
|---|---|
| `icon` | `Component` (lucide) |
| `title` | `string` |
| `description` | `string \| undefined` |

- Slot padrão: botão CTA centralizado abaixo da descrição
- Ícone: 48px, cor `--text-muted`

---

### 4. Barrel Export — `src/lib/components/ui/index.ts`

```typescript
export { default as Button }     from './Button.svelte';
export { default as Input }      from './Input.svelte';
export { default as Select }     from './Select.svelte';
export { default as Modal }      from './Modal.svelte';
export { default as Badge }      from './Badge.svelte';
export { default as Spinner }    from './Spinner.svelte';
export { default as Toast }      from './Toast.svelte';
export { default as EmptyState } from './EmptyState.svelte';
export { toastStore }            from './toast.store.ts';
```

---

## Critérios de Aceite

- [ ] `src/app.css` contém todos os tokens da spec §8 (cores, tipografia, espaçamento, sombras, transições, layout)
- [ ] `[data-theme="light"]` sobrescreve corretamente superfícies e textos sem recarregar
- [ ] Sem FOUC: `data-theme` aplicado antes do primeiro paint via script inline em `app.html`
- [ ] `themeStore.init()` lê `preferences.json`; fallback para `prefers-color-scheme`
- [ ] `themeStore.toggle()` alterna tema e persiste via `tauri-plugin-store`
- [ ] `Button` renderiza as 5 variantes e 3 tamanhos corretamente
- [ ] `Button` com `loading=true` exibe `Spinner`, bloqueia cliques e anuncia `aria-busy`
- [ ] `Input` exibe label vinculada, estado de erro com `role="alert"`, e ícone opcional
- [ ] `Select` básico funciona; versão `searchable` filtra e navega por teclado
- [ ] `Modal` aplica focus trap com `inert`; fecha via Escape, backdrop e botão ✕
- [ ] `Badge` renderiza todas as variantes com as cores corretas de `--rank-*`
- [ ] `Spinner` não anima quando `prefers-reduced-motion: reduce`
- [ ] `Toast` acumula notificações, auto-dismiss, erros com `aria-live="assertive"`
- [ ] Testes de componente (Vitest + `@testing-library/svelte`) com cobertura ≥ 75%
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Acessível: labels em todos os controles, foco navegável por teclado, contraste WCAG AA

---

## Notas Técnicas

- **Svelte 5 runes**: usar `$props()`, `$state()`, `$derived()`, `$effect()` — não usar a API legada `export let`
- **Focus trap**: implementar com o atributo `inert` nativo (Tauri v2 usa Chromium moderno) — sem biblioteca externa
- **Portal**: usar `mount(Modal, { target: document.body, props })` do Svelte 5 para isolar o Modal do fluxo DOM
- **Tokens sempre**: nunca hardcodar cores ou espaçamentos nos componentes — sempre `var(--token)`
- **@fontsource/inter**: importar somente pesos 400, 500, 600, 700 (`@fontsource/inter/400.css` etc.)
- **lucide-svelte**: importar ícones individualmente — `import { Plus } from 'lucide-svelte'`
- **Mocking Tauri em testes**: `vi.mock('@tauri-apps/api/core')` e `vi.mock('@tauri-apps/plugin-store')` no `vitest.setup.ts`
- **Snapshot tests**: usar apenas para componentes puramente estáticos (Badge, EmptyState); componentes interativos devem ter testes comportamentais

---

## Arquivos a Criar / Modificar

```
src/
├── app.css                              ← tokens globais + reset
├── app.html                             ← script anti-FOUC inline
└── lib/
    ├── stores/
    │   └── ui.ts                        ← themeStore + sidebarCollapsed
    └── components/
        └── ui/
            ├── index.ts                 ← barrel export
            ├── Button.svelte
            ├── Button.test.ts
            ├── Input.svelte
            ├── Input.test.ts
            ├── Select.svelte
            ├── Select.test.ts
            ├── Modal.svelte
            ├── Modal.test.ts
            ├── Badge.svelte
            ├── Badge.test.ts
            ├── Spinner.svelte
            ├── Spinner.test.ts
            ├── Toast.svelte
            ├── toast.store.ts
            ├── Toast.test.ts
            ├── EmptyState.svelte
            └── EmptyState.test.ts
```

---

## Progresso

- [ ] `app.css` com todos os tokens implementados
- [ ] Fonte Inter configurada (pesos 400/500/600/700)
- [ ] Script anti-FOUC em `app.html`
- [ ] `themeStore` (init + toggle + persistência)
- [ ] `sidebarCollapsed` store
- [ ] `Button` — implementação + testes
- [ ] `Input` — implementação + testes
- [ ] `Select` básico — implementação + testes
- [ ] `Select` searchable — implementação + testes
- [ ] `Modal` com focus trap — implementação + testes
- [ ] `Badge` — implementação + testes
- [ ] `Spinner` — implementação + testes
- [ ] `Toast` + `toastStore` — implementação + testes
- [ ] `EmptyState` — implementação + testes
- [ ] Barrel `ui/index.ts` completo
- [ ] `tsc --noEmit` sem erros
- [ ] `vitest --coverage` ≥ 75%
