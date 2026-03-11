# PDR-SHADCN-001 — Migração para shadcn-svelte

| Campo      | Valor                                     |
| ---------- | ----------------------------------------- |
| **Status** | ACCEPTED                                  |
| **Autor**  | Team                                      |
| **Data**   | 2026-03-05                                |
| **Tags**   | frontend, ui, design-system, tailwind, ux |

---

## 1. Contexto

O Escala Mídia nasceu com um design system caseiro: classes utilitárias Tailwind (`.btn`, `.card`, `.badge`, `.input`) definidas manualmente em `app.css`, modais implementados com `<div class="fixed inset-0 ...">` e toasts via uma store Svelte customizada (`$lib/stores/toast.ts` + `ToastContainer.svelte`). Ícones são emojis Unicode embutidos diretamente no markup.

Esse approach funcionou para o MVP mas apresenta limitações crescentes:

- **Acessibilidade**: modais sem foco trap, selects sem ARIA correto, ausência de `role`/`aria-*` em componentes interativos.
- **Manutenção**: cada nova tela precisa recriar padrões de modal, select, checkbox do zero.
- **Consistência visual**: sem tokens de cor unificados entre modo claro/escuro.
- **Ícones via emoji**: sem controle de tamanho consistente, renderização depende do sistema operacional.
- **Fontes via Google Fonts CDN**: viola a CSP `default-src 'self'` do Tauri.

A solução escolhida é migrar para **shadcn-svelte** — uma biblioteca "copy-paste" onde os componentes são copiados para dentro do projeto e ficam sob controle total da equipe — combinada com **fontes npm** e **ícones Iconify offline**.

---

## 2. Decisão

### 2.1 shadcn-svelte

Adotar [shadcn-svelte](https://www.shadcn-svelte.com/) como biblioteca de componentes UI principal.

**Por que shadcn-svelte e não outra opção?**

| Critério                       | shadcn-svelte | Skeleton UI | Flowbite Svelte | Melt UI (primitivos) |
| ------------------------------ | :-----------: | :---------: | :-------------: | :------------------: |
| Compatible Svelte 5 runes      |      ✅       |     ⚠️      |       ⚠️        |          ✅          |
| Tailwind v4 suporte            |      ✅       |     ❌      |       ❌        |   N/A (sem estilo)   |
| Componentes são SEUS (copy)    |      ✅       |     ❌      |       ❌        |          ❌          |
| Acessibilidade (Bits UI base)  |      ✅       |     ⚠️      |       ⚠️        |          ✅          |
| Sidebar component              |      ✅       |     ❌      |       ❌        |          ❌          |
| Sonner toast integrado         |      ✅       |     ❌      |       ❌        |          ❌          |

shadcn-svelte é construído sobre **Bits UI** (primitivos acessíveis) e gera código Svelte 5 nativo com runes. Os componentes são copiados para `src/lib/components/ui/` e podem ser modificados livremente.

### 2.2 Iconify + Lucide offline

Usar `@iconify/svelte` com a coleção `@iconify-json/lucide` instalada como devDependency. Os ícones são carregados via `addCollection()` no startup da aplicação — **zero requisição de rede, zero CDN**.

### 2.3 Fontes npm (@fontsource)

| Fonte          | Papel               | Package npm                   |
| -------------- | ------------------- | ----------------------------- |
| **Poppins**    | Headings (`h1`–`h4`) | `@fontsource/poppins`        |
| **Montserrat** | Body / UI text      | `@fontsource/montserrat`      |

Importados diretamente no `app.css` via `@import`. Sem Google Fonts, sem CDN — compatível com CSP `default-src 'self'`.

### 2.4 Variáveis CSS → tokens shadcn (oklch)

As variáveis atuais (`--color-primary-*`, `--color-neutral-*`) são substituídas pelo sistema de tokens do shadcn-svelte via bloco `@theme inline` em `app.css`. As cores usam o espaço `oklch()` conforme padrão shadcn + Tailwind v4.

### 2.5 Escopo da migração

| Escopo                         | Incluído? |
| ------------------------------ | :-------: |
| Componentes UI (`src/lib/components/`) | ✅ |
| Estilos (`app.css`)            | ✅        |
| Fontes e ícones                | ✅        |
| Lógica de negócio (`$lib/api`) | ❌        |
| Stores (`$lib/stores`)         | ❌*       |
| Types (`$lib/types`)           | ❌        |
| Backend Rust (`src-tauri/`)    | ❌        |
| Atributos `data-testid` E2E    | ✅ (preservar) |

> *`$lib/stores/toast.ts` pode ser removida após a migração para `svelte-sonner`, mas toda chamada existente `toast.success()` nas páginas permanece **sem alteração de API**.

---

## 3. Consequências

### 3.1 Positivas

- **Acessibilidade** nativa: Bits UI (base do shadcn-svelte) implementa ARIA, foco trap e keyboard navigation corretos.
- **Componentes owned**: qualquer customização diretamente nos arquivos em `src/lib/components/ui/`.
- **Dark mode** sem esforço: tokens `--background`/`--foreground` com `.dark` class.
- **Bundle de ícones** totalmente local — CSP preservada.
- **Fonte consistente** em todos os sistemas operacionais (Windows, macOS, Linux).
- **Sonner toast**: animações polidas, suporte a `promise()`, `error()`, `loading()` — mesma API da store atual.
- **`cn()` helper**: composição de classes com `clsx` + `tailwind-merge` elimina conflitos de classes Tailwind.

### 3.2 Negativas / Riscos

| Risco                                    | Mitigação                                                    |
| ---------------------------------------- | ------------------------------------------------------------ |
| Volume de componentes a migrar           | Migração incremental página por página, sem big-bang         |
| Select Svelte 5 sem `bind:value` nativo  | Padrão `onValueChange` documentado neste PDR (seção 7.4)     |
| Testes E2E quebrarem por seletores       | Preservar todos os `data-testid` nos componentes reconstruídos |
| Tailwind v4 sem `tailwind.config.js`     | Toda config via `@theme inline` em `app.css` (seção 5.2)    |
| Peso de fontes (múltiplos pesos)         | Importar apenas pesos 400, 500, 600, 700                     |

---

## 4. Instalação — Guia Completo

### 4.1 Dependências base

```bash
# shadcn-svelte CLI + dependências de runtime
pnpm add -D shadcn-svelte

# Utilitários usados pelo código gerado
pnpm add clsx tailwind-merge bits-ui

# Ícones offline
pnpm add @iconify/svelte
pnpm add -D @iconify-json/lucide

# Fontes npm
pnpm add @fontsource/poppins @fontsource/montserrat

# Toast (Sonner)
pnpm add svelte-sonner
```

### 4.2 Inicializar shadcn-svelte

```bash
pnpm dlx shadcn-svelte@latest init
```

O CLI irá perguntar sobre framework, path aliases e Tailwind version. Responda conforme abaixo ou use o `components.json` da seção 4.3 diretamente.

### 4.3 `components.json`

Crie (ou substitua) `components.json` na raiz do projeto:

```json
{
  "$schema": "https://shadcn-svelte.com/schema.json",
  "style": "default",
  "tailwind": {
    "config": "",
    "css": "src/app.css",
    "baseColor": "neutral",
    "cssVariables": true
  },
  "aliases": {
    "components": "$lib/components",
    "utils": "$lib/utils",
    "ui": "$lib/components/ui",
    "hooks": "$lib/hooks"
  },
  "typescript": true,
  "registry": "https://shadcn-svelte.com/registry"
}
```

> **`tailwind.config`** fica vazio porque Tailwind v4 não usa `tailwind.config.js`.

### 4.4 Adicionar todos os componentes necessários

```bash
pnpm dlx shadcn-svelte@latest add button
pnpm dlx shadcn-svelte@latest add card
pnpm dlx shadcn-svelte@latest add badge
pnpm dlx shadcn-svelte@latest add input
pnpm dlx shadcn-svelte@latest add label
pnpm dlx shadcn-svelte@latest add select
pnpm dlx shadcn-svelte@latest add checkbox
pnpm dlx shadcn-svelte@latest add dialog
pnpm dlx shadcn-svelte@latest add sidebar
pnpm dlx shadcn-svelte@latest add sonner
pnpm dlx shadcn-svelte@latest add separator
pnpm dlx shadcn-svelte@latest add tooltip
pnpm dlx shadcn-svelte@latest add table
pnpm dlx shadcn-svelte@latest add scroll-area
```

Cada comando copia os arquivos `.svelte` para `src/lib/components/ui/<component>/`.

---

## 5. Configuração de Estilos

### 5.1 Estrutura do `src/app.css`

```css
/* ═══════════════════════════════════════════════════════════
   1. Tailwind v4 base
   ═══════════════════════════════════════════════════════════ */
@import "tailwindcss";

/* ═══════════════════════════════════════════════════════════
   2. Fontes npm — apenas pesos utilizados
   ═══════════════════════════════════════════════════════════ */
@import "@fontsource/poppins/400.css";
@import "@fontsource/poppins/500.css";
@import "@fontsource/poppins/600.css";
@import "@fontsource/poppins/700.css";

@import "@fontsource/montserrat/400.css";
@import "@fontsource/montserrat/500.css";
@import "@fontsource/montserrat/600.css";

/* ═══════════════════════════════════════════════════════════
   3. shadcn-svelte — tokens de cor + tema
   ═══════════════════════════════════════════════════════════ */
@layer base {
  :root {
    --background:         0 0% 100%;
    --foreground:         240 10% 3.9%;
    --card:               0 0% 100%;
    --card-foreground:    240 10% 3.9%;
    --popover:            0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary:            240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --secondary:          240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted:              240 4.8% 95.9%;
    --muted-foreground:   240 3.8% 46.1%;
    --accent:             240 4.8% 95.9%;
    --accent-foreground:  240 5.9% 10%;
    --destructive:        0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border:             240 5.9% 90%;
    --input:              240 5.9% 90%;
    --ring:               240 5.9% 10%;
    --radius:             0.5rem;

    /* Sidebar */
    --sidebar-background:        240 5.9% 10%;
    --sidebar-foreground:        0 0% 98%;
    --sidebar-primary:           0 0% 98%;
    --sidebar-primary-foreground: 240 5.9% 10%;
    --sidebar-accent:            240 3.7% 15.9%;
    --sidebar-accent-foreground: 0 0% 98%;
    --sidebar-border:            240 3.7% 15.9%;
    --sidebar-ring:              217.2 91.2% 59.8%;
  }

  .dark {
    --background:         240 10% 3.9%;
    --foreground:         0 0% 98%;
    --card:               240 10% 3.9%;
    --card-foreground:    0 0% 98%;
    --popover:            240 10% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary:            0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --secondary:          240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted:              240 3.7% 15.9%;
    --muted-foreground:   240 5% 64.9%;
    --accent:             240 3.7% 15.9%;
    --accent-foreground:  0 0% 98%;
    --destructive:        0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border:             240 3.7% 15.9%;
    --input:              240 3.7% 15.9%;
    --ring:               240 4.9% 83.9%;
  }
}

/* ═══════════════════════════════════════════════════════════
   4. @theme inline — registra tokens como utilities Tailwind
   ═══════════════════════════════════════════════════════════ */
@theme inline {
  --color-background:          hsl(var(--background));
  --color-foreground:          hsl(var(--foreground));
  --color-card:                hsl(var(--card));
  --color-card-foreground:     hsl(var(--card-foreground));
  --color-popover:             hsl(var(--popover));
  --color-popover-foreground:  hsl(var(--popover-foreground));
  --color-primary:             hsl(var(--primary));
  --color-primary-foreground:  hsl(var(--primary-foreground));
  --color-secondary:           hsl(var(--secondary));
  --color-secondary-foreground: hsl(var(--secondary-foreground));
  --color-muted:               hsl(var(--muted));
  --color-muted-foreground:    hsl(var(--muted-foreground));
  --color-accent:              hsl(var(--accent));
  --color-accent-foreground:   hsl(var(--accent-foreground));
  --color-destructive:         hsl(var(--destructive));
  --color-destructive-foreground: hsl(var(--destructive-foreground));
  --color-border:              hsl(var(--border));
  --color-input:               hsl(var(--input));
  --color-ring:                hsl(var(--ring));

  /* Sidebar */
  --color-sidebar:                    hsl(var(--sidebar-background));
  --color-sidebar-foreground:         hsl(var(--sidebar-foreground));
  --color-sidebar-primary:            hsl(var(--sidebar-primary));
  --color-sidebar-primary-foreground: hsl(var(--sidebar-primary-foreground));
  --color-sidebar-accent:             hsl(var(--sidebar-accent));
  --color-sidebar-accent-foreground:  hsl(var(--sidebar-accent-foreground));
  --color-sidebar-border:             hsl(var(--sidebar-border));
  --color-sidebar-ring:               hsl(var(--sidebar-ring));

  /* Fontes */
  --font-heading: "Poppins", system-ui, sans-serif;
  --font-body:    "Montserrat", system-ui, sans-serif;
  --font-sans:    "Montserrat", system-ui, sans-serif;

  /* Border radius */
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}

/* ═══════════════════════════════════════════════════════════
   5. Base global
   ═══════════════════════════════════════════════════════════ */
@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground font-body;
  }

  h1, h2, h3, h4 {
    @apply font-heading;
  }
}
```

> **Nota Tailwind v4**: não existe `tailwind.config.js`. Todo o tema é configurado via `@theme inline`. As utilities `bg-primary`, `text-foreground`, `bg-sidebar`, etc. são geradas automaticamente a partir dos tokens registrados.

---

## 6. `src/lib/utils.ts`

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combina classes Tailwind resolvendo conflitos.
 * Usar em todos os componentes UI ao montar className.
 *
 * @example cn("px-4 py-2", isActive && "bg-primary", className)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

---

## 7. Configurações Adicionais

### 7.1 Iconify offline — `src/routes/+layout.svelte`

```svelte
<script lang="ts">
  import { addCollection } from "@iconify/svelte";
  import lucideIcons from "@iconify-json/lucide/icons.json";

  // Registra toda a coleção Lucide localmente — zero CDN
  addCollection(lucideIcons);

  let { children } = $props();
</script>

<!-- Toaster fora do conteúdo principal, mas dentro do layout -->
{@render children()}
```

**Uso de ícone em qualquer componente:**

```svelte
<script lang="ts">
  import { Icon } from "@iconify/svelte";
</script>

<!-- Substitui emojis como 👥 📅 🎬 -->
<Icon icon="lucide:users"     class="size-5" />
<Icon icon="lucide:calendar"  class="size-5" />
<Icon icon="lucide:clapperboard" class="size-5" />
<Icon icon="lucide:plus"      class="size-4" />
<Icon icon="lucide:pencil"    class="size-4" />
<Icon icon="lucide:trash-2"   class="size-4" />
```

> A coleção Lucide contém ~1500 ícones. O bundler (Vite) incluirá **apenas os ícones realmente importados** no bundle final graças ao tree-shaking, mas como usamos `addCollection` com o JSON completo, o bundle incluirá todos. Para projetos onde o tamanho importa, prefira importar ícones individualmente com `addIcon`.

### 7.2 Toaster — `src/routes/+layout.svelte` (completo)

```svelte
<script lang="ts">
  import { addCollection } from "@iconify/svelte";
  import lucideIcons from "@iconify-json/lucide/icons.json";
  import { Toaster } from "svelte-sonner";
  import Sidebar from "$lib/components/layout/Sidebar.svelte";

  addCollection(lucideIcons);

  let { children } = $props();
</script>

<div class="flex h-screen">
  <Sidebar />
  <main class="flex-1 overflow-auto">
    {@render children()}
  </main>
</div>

<!-- Toaster FORA do flex layout, renderizado no body -->
<Toaster richColors position="bottom-right" theme="light" />
```

### 7.3 Migração do Toast Store

A store customizada `$lib/stores/toast.ts` exportava `toast.success()`, `toast.error()`, `toast.info()`. A `svelte-sonner` expõe **exatamente a mesma API**:

```typescript
// ANTES — import mudava, API igual
import { toast } from "$lib/stores/toast";

// DEPOIS — apenas o import muda
import { toast } from "svelte-sonner";

// Chamadas nas páginas: ZERO mudança
toast.success("Membro criado com sucesso!");
toast.error("Erro ao salvar. Tente novamente.");
toast.promise(savePromise, {
  loading: "Salvando...",
  success: "Salvo!",
  error: "Erro ao salvar.",
});
```

**Passos de migração:**
1. Adicionar `<Toaster />` em `+layout.svelte` (seção 7.2).
2. Em cada arquivo que importa de `$lib/stores/toast`, substituir o import.
3. Remover `ToastContainer.svelte` e `$lib/stores/toast.ts`.

### 7.4 Select com Svelte 5 Runes

O componente `<Select.Root>` do shadcn-svelte não expõe `bind:value` nativo. O padrão correto com runes é usar a prop `value` + callback `onValueChange`:

```svelte
<script lang="ts">
  import * as Select from "$lib/components/ui/select";

  let form = $state({ rank: "member" });
</script>

<Select.Root
  type="single"
  value={form.rank}
  onValueChange={(v) => (form.rank = v)}
>
  <Select.Trigger class="w-full">
    <Select.Value placeholder="Selecione um cargo" />
  </Select.Trigger>
  <Select.Content>
    <Select.Item value="member">Membro</Select.Item>
    <Select.Item value="leader">Líder</Select.Item>
    <Select.Item value="coordinator">Coordenador</Select.Item>
  </Select.Content>
</Select.Root>
```

### 7.5 Dialog com estado controlado (Svelte 5)

```svelte
<script lang="ts">
  import * as Dialog from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";

  let open = $state(false);

  function handleSave() {
    // lógica de salvar...
    open = false; // fecha programaticamente
  }
</script>

<Button onclick={() => (open = true)}>Novo Membro</Button>

<Dialog.Root bind:open>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>Adicionar Membro</Dialog.Title>
      <Dialog.Description>Preencha os dados do novo membro.</Dialog.Description>
    </Dialog.Header>

    <!-- formulário aqui -->

    <Dialog.Footer>
      <Dialog.Close>
        <Button variant="outline">Cancelar</Button>
      </Dialog.Close>
      <Button onclick={handleSave}>Salvar</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
```

> **Atenção**: o botão Cancelar deve estar dentro de `<Dialog.Close>` para garantir o comportamento de fechar + acessibilidade (ESC key, click fora).

### 7.6 Sidebar com detecção de rota ativa

```svelte
<script lang="ts">
  import { page } from "$app/stores";
  import * as Sidebar from "$lib/components/ui/sidebar";
  import { Icon } from "@iconify/svelte";

  const navItems = [
    { href: "/members",  label: "Membros",    icon: "lucide:users"       },
    { href: "/squads",   label: "Times",       icon: "lucide:layers"      },
    { href: "/events",   label: "Eventos",     icon: "lucide:calendar"    },
    { href: "/schedule", label: "Escalas",     icon: "lucide:list-checks" },
  ];
</script>

<Sidebar.Provider>
  <Sidebar.Root collapsible="icon">
    <Sidebar.Content>
      <Sidebar.Menu>
        {#each navItems as item}
          <Sidebar.MenuItem>
            <Sidebar.MenuButton
              isActive={$page.url.pathname.startsWith(item.href)}
              href={item.href}
            >
              <Icon icon={item.icon} class="size-4" />
              <span class="group-data-[collapsible=icon]:hidden">
                {item.label}
              </span>
            </Sidebar.MenuButton>
          </Sidebar.MenuItem>
        {/each}
      </Sidebar.Menu>
    </Sidebar.Content>
  </Sidebar.Root>
</Sidebar.Provider>
```

### 7.7 Label + Input (formulários)

Sempre associar `<Label for="id">` + `<Input id="id">` com IDs explícitos para acessibilidade:

```svelte
<script lang="ts">
  import { Label } from "$lib/components/ui/label";
  import { Input } from "$lib/components/ui/input";
</script>

<div class="grid gap-2">
  <Label for="member-name">Nome completo</Label>
  <Input id="member-name" type="text" placeholder="Ex.: Ana Silva" />
</div>
```

---

## 8. Mapeamento de Componentes

Tabela completa de correspondência entre os padrões atuais e os componentes shadcn-svelte:

| Padrão atual                          | Componente shadcn-svelte                                   | Import                                      | Exemplo de uso                                               |
| ------------------------------------- | ---------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------ |
| `.btn .btn-primary`                   | `<Button variant="default">`                               | `$lib/components/ui/button`                 | `<Button>Salvar</Button>`                                    |
| `.btn .btn-secondary`                 | `<Button variant="outline">`                               | `$lib/components/ui/button`                 | `<Button variant="outline">Cancelar</Button>`                |
| `.btn .btn-danger`                    | `<Button variant="destructive">`                           | `$lib/components/ui/button`                 | `<Button variant="destructive">Excluir</Button>`             |
| `.btn-sm`                             | `<Button size="sm">`                                       | `$lib/components/ui/button`                 | `<Button size="sm">Ação</Button>`                            |
| `.card`                               | `<Card.Root>` + `<Card.Content>`                           | `$lib/components/ui/card`                   | `<Card.Root><Card.Content>...</Card.Content></Card.Root>`    |
| `.badge .badge-blue`                  | `<Badge variant="secondary">`                              | `$lib/components/ui/badge`                  | `<Badge variant="secondary">Confirmado</Badge>`              |
| `.badge .badge-green`                 | `<Badge variant="default">`                                | `$lib/components/ui/badge`                  | `<Badge>Ativo</Badge>`                                       |
| `.badge .badge-red`                   | `<Badge variant="destructive">`                            | `$lib/components/ui/badge`                  | `<Badge variant="destructive">Inativo</Badge>`               |
| `<input class="input">`               | `<Input>`                                                  | `$lib/components/ui/input`                  | `<Input type="text" placeholder="..." />`                    |
| `<input type="number" class="input">` | `<Input type="number">`                                    | `$lib/components/ui/input`                  | `<Input type="number" min="0" />`                            |
| `<select class="input">`              | `<Select.Root>` + `<Select.Trigger>` + `<Select.Content>` + `<Select.Item>` | `$lib/components/ui/select` | Ver seção 7.4                                   |
| `<input type="checkbox">`             | `<Checkbox>`                                               | `$lib/components/ui/checkbox`               | `<Checkbox bind:checked={val} />`                            |
| `<div class="fixed inset-0 ...">`     | `<Dialog.Root>` + `<Dialog.Content>` + `<Dialog.Header>` + `<Dialog.Footer>` + `<Dialog.Close>` | `$lib/components/ui/dialog` | Ver seção 7.5           |
| `<label>`                             | `<Label for="id">`                                         | `$lib/components/ui/label`                  | `<Label for="email">E-mail</Label>`                          |
| Sidebar nav customizada               | `<Sidebar.Provider>` + `<Sidebar.Root>` + `<Sidebar.Menu>` + `<Sidebar.MenuButton>` | `$lib/components/ui/sidebar` | Ver seção 7.6           |
| `ToastContainer.svelte` custom        | `<Toaster>` from `svelte-sonner`                           | `svelte-sonner`                             | `<Toaster richColors position="bottom-right" />`             |
| `toast.success()` custom store        | `toast.success()` from `svelte-sonner`                     | `svelte-sonner`                             | `toast.success("Membro salvo!")` — API idêntica              |
| Emoji `👥` `📅` `🎬` como ícone      | `<Icon icon="lucide:...">`                                 | `@iconify/svelte`                           | `<Icon icon="lucide:users" class="size-5" />`                |
| `<table>` raw                         | `<Table>` + `<Table.Header>` + `<Table.Body>` + `<Table.Row>` + `<Table.Cell>` | `$lib/components/ui/table` | Ver docs shadcn-svelte   |

---

## 9. Gotchas e Armadilhas Conhecidas

### 9.1 Sem `tailwind.config.js` no Tailwind v4

Tailwind v4 abandonou o arquivo de configuração JavaScript. **Toda** customização de tema (cores, fontes, espaçamentos) é feita via `@theme inline { }` no CSS. Não criar `tailwind.config.js` — isso causaria conflito.

### 9.2 Cores em oklch

shadcn-svelte usa `oklch()` para definir seus tokens de cor no CSS gerado. Ao customizar temas, usar `oklch()` em vez de `hsl()` ou hex. Ferramentas úteis: [oklch.com](https://oklch.com) e [Radix Colors](https://www.radix-ui.com/colors).

> Os valores neste PDR usam `hsl()` para compatibilidade com o tema padrão shadcn-svelte. Adaptar para `oklch()` ao criar temas customizados.

### 9.3 Select sem `bind:value` nativo

O `<Select.Root>` do shadcn-svelte (Bits UI) **não suporta** `bind:value` diretamente no Svelte 5 runes mode. Usar sempre o padrão `value={...} onValueChange={(v) => ...}` documentado na seção 7.4.

### 9.4 Dialog.Close obrigatório para botão Cancelar

Não use `onclick={() => (open = false)}` em botões de cancelar dentro de Dialog. Use o wrapper `<Dialog.Close>` que garante: fechar via ESC, click fora, ARIA correto e foco retornando ao trigger.

### 9.5 Sidebar collapsible e labels ocultas

Quando a sidebar está no modo `collapsible="icon"`, os labels ficam ocultos. Para texto que deve sumir nesse modo, usar a classe utilitária:

```svelte
<span class="group-data-[collapsible=icon]:hidden">Membros</span>
```

### 9.6 Preservar `data-testid` em todos os rebuilds

Os testes E2E em `tests/e2e/` usam seletores `data-testid`. **Qualquer componente reconstruído com shadcn-svelte DEVE manter o `data-testid` original** para não quebrar a suite de regressão. Exemplo:

```svelte
<!-- ANTES -->
<button class="btn btn-primary" data-testid="btn-add-member">Adicionar</button>

<!-- DEPOIS — mantém data-testid -->
<Button data-testid="btn-add-member">Adicionar</Button>
```

### 9.7 adapter-static SPA — sem prerender explícito

O projeto usa `@sveltejs/adapter-static` em modo SPA com `fallback: 'index.html'`. Não é necessário adicionar `export const prerender = false` em `+layout.ts` — o adapter já opera em modo SPA por padrão quando `fallback` está configurado.

### 9.8 Toaster fora do layout de conteúdo

O `<Toaster />` deve ser renderizado **fora** do `<div class="flex">` do layout principal para evitar que seja afetado por `overflow-hidden` ou z-index do sidebar. Colocá-lo como último elemento filho de `+layout.svelte`.

### 9.9 Evitar `mode-watcher` no contexto Tauri

A biblioteca `mode-watcher` detecta preferências do sistema via `window.matchMedia`. Em apps Tauri SPA onde o tema é controlado pelo app, é mais simples passar `theme="light"` ou `theme="dark"` diretamente ao `<Toaster>`:

```svelte
<!-- Sem mode-watcher -->
<Toaster theme="light" richColors position="bottom-right" />
```

### 9.10 Fontsource — importar apenas pesos necessários

Para manter o bundle pequeno, importar apenas os arquivos de peso efetivamente usados:

```css
/* ✅ Correto — apenas pesos usados */
@import "@fontsource/poppins/600.css";
@import "@fontsource/poppins/700.css";

/* ❌ Evitar — bundle desnecessariamente grande */
@import "@fontsource/poppins"; /* importa todos os pesos */
```

---

## 10. Estrutura de Arquivos Resultante

Após a migração completa, a estrutura de `src/lib/components/` será:

```
src/lib/
  utils.ts                         ← cn() helper
  components/
    ui/                            ← gerado pelo shadcn-svelte CLI (copy-paste)
      button/
        index.ts
      card/
        index.ts
      badge/
        index.ts
      input/
        index.ts
      label/
        index.ts
      select/
        index.ts
      checkbox/
        index.ts
      dialog/
        index.ts
      sidebar/
        index.ts
      sonner/
        index.ts
      table/
        index.ts
      separator/
        index.ts
      scroll-area/
        index.ts
      tooltip/
        index.ts
    layout/                        ← componentes de layout (Sidebar refatorada)
      Sidebar.svelte
      Header.svelte
    domain/                        ← componentes de domínio (Members, Squads, etc.)
      MemberCard.svelte
      SquadBadge.svelte
      ...
```

---

## 11. Critérios de Aceite da Migração

A migração de cada página/componente é considerada **concluída** quando:

- [ ] Todos os botões usam `<Button>` com variant correto
- [ ] Todos os inputs usam `<Input>` ou `<Select.Root>`
- [ ] Todos os modais usam `<Dialog.Root>` com foco trap funcional
- [ ] Sidebar usa `<Sidebar.Provider>` com `isActive` por pathname
- [ ] Emojis substituídos por `<Icon icon="lucide:...">` 
- [ ] `data-testid` preservados em todos os elementos interativos
- [ ] Suite E2E passa sem regressões (`pnpm test:e2e`)
- [ ] Fontes Poppins (headings) e Montserrat (body) visíveis em runtime
- [ ] Toaster Sonner funcional em substituição ao `ToastContainer`
- [ ] Sem chamadas externas de rede para fontes ou ícones (verificar DevTools)

---

## 12. Referências

| Recurso                              | URL                                                              |
| ------------------------------------ | ---------------------------------------------------------------- |
| shadcn-svelte docs                   | https://www.shadcn-svelte.com/docs                               |
| Bits UI (base acessível)             | https://bits-ui.com                                              |
| svelte-sonner                        | https://github.com/wobsoriano/svelte-sonner                      |
| @iconify/svelte                      | https://iconify.design/docs/icon-components/svelte/              |
| Lucide icon set                      | https://lucide.dev/icons/                                        |
| @fontsource/poppins                  | https://fontsource.org/fonts/poppins                             |
| @fontsource/montserrat               | https://fontsource.org/fonts/montserrat                          |
| Tailwind v4 — @theme                 | https://tailwindcss.com/docs/v4-upgrade                          |
| oklch color picker                   | https://oklch.com                                                |
| Tauri v2 capabilities / CSP          | `src-tauri/capabilities/` + `docs/pdrs/PDR-TAURI-001.md`        |
