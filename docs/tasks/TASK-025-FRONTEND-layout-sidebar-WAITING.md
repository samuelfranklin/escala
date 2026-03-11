# TASK-025 — Frontend: Layout Shell com Sidebar shadcn

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P0 (bloqueante — todas as páginas dependem do layout)  
**Depende de:** TASK-024  
**Estimativa:** M (2–4h)

## Descrição

Reconstruir o `src/routes/+layout.svelte` usando o componente `<Sidebar>` do shadcn-svelte e criar o novo `src/lib/components/AppSidebar.svelte`.

- Substituir o `<aside>` manual + grid layout por `<Sidebar.Provider>` + `<Sidebar.Root collapsible="icon">`
- Substituir `ToastContainer.svelte` por `<Toaster>` do sonner
- Substituir emojis de navegação por ícones Lucide via `@iconify/svelte`
- Inicializar `addCollection()` do Iconify no script do layout
- A sidebar deve colapsar para ícones (collapsible="icon") e expandir ao hover/click

## Critérios de Aceite

- [ ] Sidebar renderiza com todos os 7 itens de navegação (Dashboard, Membros, Times, Eventos, Escala, Disponibilidade, Casais)
- [ ] Cada item usa ícone Lucide correto (sem emojis)
- [ ] Active state detectado corretamente via `$page.url.pathname`
- [ ] Sidebar colapsa para ícones ao pressionar trigger ou `Ctrl+B`
- [ ] Toasts funcionam via `svelte-sonner` (`toast.success`, `toast.error`, etc.)
- [ ] `ToastContainer.svelte` não é mais importado no layout
- [ ] `{@render children?.()}` (Svelte 5 snippets) usado em vez de `<slot />`
- [ ] `pnpm dev` sem erros TypeScript

## Notas Técnicas

### Ícones por rota

| Rota | Ícone Lucide |
|---|---|
| `/dashboard` | `lucide:layout-dashboard` |
| `/members` | `lucide:users` |
| `/squads` | `lucide:layers` |
| `/events` | `lucide:calendar` |
| `/schedule` | `lucide:clipboard-list` |
| `/availability` | `lucide:calendar-check` |
| `/couples` | `lucide:heart` |

### Estrutura de AppSidebar.svelte

```svelte
<Sidebar.Root collapsible="icon">
  <Sidebar.Header>
    <!-- Logo Escala Mídia -->
  </Sidebar.Header>
  <Sidebar.Content>
    <Sidebar.Group>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each navItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton isActive={$page.url.pathname.startsWith(item.href)}>
                {#snippet child({ props })}
                  <a href={item.href} {...props}>
                    <Icon icon={item.icon} />
                    <span>{item.label}</span>
                  </a>
                {/snippet}
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>
  </Sidebar.Content>
  <Sidebar.Rail />
</Sidebar.Root>
```

### Estrutura de +layout.svelte

```svelte
<Sidebar.Provider>
  <AppSidebar />
  <Sidebar.Inset>
    <header class="flex h-12 items-center border-b px-4">
      <Sidebar.Trigger />
    </header>
    <main class="p-8 overflow-y-auto" id="main">
      {@render children?.()}
    </main>
  </Sidebar.Inset>
</Sidebar.Provider>
<Toaster />
```

### Importar Iconify + addCollection no layout

```svelte
<script lang="ts">
  import { addCollection } from '@iconify/svelte';
  import lucideIcons from '@iconify-json/lucide/icons.json';
  addCollection(lucideIcons); // registro único, offline
  // ...
</script>
```

### Referências

- [SPEC-LAYOUT.md](../specs/screens/SPEC-LAYOUT.md) — spec detalhada
- [PDR-SHADCN-001.md](../pdrs/PDR-SHADCN-001.md) — padrões de código

## Progresso

- [ ] Criar `src/lib/components/AppSidebar.svelte`
- [ ] Reescrever `src/routes/+layout.svelte`
- [ ] Adicionar `addCollection(lucideData)` no script do layout
- [ ] Substituir `<slot />` por `{@render children?.()}`
- [ ] Substituir `<ToastContainer />` por `<Toaster />`
- [ ] Testar colapso da sidebar (Ctrl+B / botão trigger)
- [ ] Verificar active state em todas as rotas
- [ ] Commit: `feat(ui): layout shell com shadcn Sidebar (#TASK-025)`
