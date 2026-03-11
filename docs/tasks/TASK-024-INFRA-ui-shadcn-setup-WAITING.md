# TASK-024 — Infra: Setup shadcn-svelte + Fontes + Iconify

**Domínio:** INFRA  
**Status:** WAITING  
**Prioridade:** P0 (bloqueante — todas as demais tasks de UI dependem desta)  
**Depende de:** nenhuma  
**Estimativa:** M (2–4h)

## Descrição

Instalar e configurar toda a infraestrutura de UI antes de tocar em qualquer componente ou página:

1. Criar `components.json` (config do shadcn-svelte CLI)
2. Instalar dependências de produção e dev
3. Criar `src/lib/utils.ts` com o helper `cn()`
4. Atualizar `src/app.css`: importar fontes via `@fontsource`, migrar CSS vars para o sistema shadcn (oklch) com `@theme inline`
5. Rodar `shadcn-svelte add` para todos os componentes necessários
6. Verificar que `pnpm dev` compila sem erros

**Escopo**: APENAS infraestrutura — nenhuma página ou layout é alterado nesta task.

## Critérios de Aceite

- [ ] `components.json` presente na raiz com `tailwind.css = "src/app.css"` e `tailwind.config = ""`
- [ ] `src/lib/utils.ts` exporta `cn()` usando `clsx` + `tailwind-merge`
- [ ] `src/app.css` importa Poppins e Montserrat via `@fontsource`, define `@theme inline` com vars oklch shadcn, e define CSS vars das sidebar
- [ ] `src/lib/components/ui/button/index.js` existe (criado pelo CLI do shadcn)
- [ ] Todos os componentes necessários instalados: button, card, badge, input, label, select, dialog, sonner, sidebar, checkbox, separator
- [ ] `@iconify/svelte` e `@iconify-json/lucide` instalados como devDependencies
- [ ] `@fontsource/poppins` e `@fontsource/montserrat` instalados
- [ ] `pnpm dev` compila sem erros TypeScript nem de bundler

## Notas Técnicas

### Dependências a instalar

```bash
# Produção
pnpm add bits-ui clsx tailwind-merge tailwind-variants svelte-sonner

# Dev
pnpm add -D @iconify/svelte @iconify-json/lucide @fontsource/poppins @fontsource/montserrat
```

### components.json (Tailwind v4 — campo config vazio)

```json
{
  "$schema": "https://shadcn-svelte.com/schema.json",
  "style": "default",
  "tailwind": {
    "config": "",
    "css": "src/app.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "$lib/components",
    "utils": "$lib/utils",
    "ui": "$lib/components/ui",
    "lib": "$lib",
    "hooks": "$lib/hooks"
  }
}
```

### shadcn-svelte add (com components.json presente, não é interativo)

```bash
pnpm dlx shadcn-svelte@latest add button card badge input label select dialog sonner sidebar checkbox separator
```

### Fontes — importar pesos necessários apenas

```css
/* Poppins: headings */
@import "@fontsource/poppins/400.css";
@import "@fontsource/poppins/500.css";
@import "@fontsource/poppins/600.css";
@import "@fontsource/poppins/700.css";

/* Montserrat: body */
@import "@fontsource/montserrat/400.css";
@import "@fontsource/montserrat/500.css";
@import "@fontsource/montserrat/600.css";
```

### CSS vars shadcn — usar oklch (não HSL nem hex)

Ver PDR-SHADCN-001 para a lista completa de variáveis `--background`, `--foreground`, `--primary`, `--sidebar`, etc.

### Referências

- [PDR-SHADCN-001](../pdrs/PDR-SHADCN-001.md) — decisões técnicas e exemplos de código completos
- [shadcn-svelte SvelteKit docs](https://www.shadcn-svelte.com/docs/installation/sveltekit)
- [Tailwind v4 migration](https://www.shadcn-svelte.com/docs/migration/tailwind-v4)

## Progresso

- [ ] Criar `components.json` na raiz do projeto
- [ ] Instalar dependências de produção (`bits-ui`, `clsx`, `tailwind-merge`, `tailwind-variants`, `svelte-sonner`)
- [ ] Instalar dependências de dev (`@iconify/svelte`, `@iconify-json/lucide`, `@fontsource/poppins`, `@fontsource/montserrat`)
- [ ] Criar `src/lib/utils.ts` com `cn()`
- [ ] Atualizar `src/app.css` (fontes + @theme inline + CSS vars shadcn + sidebar vars)
- [ ] Rodar `pnpm dlx shadcn-svelte@latest add [componentes]`
- [ ] Verificar `pnpm dev` sem erros
- [ ] Commit: `chore(ui): setup shadcn-svelte infra (#TASK-024)`
