# TASK-024 — Infraestrutura UI: Instalação e Configuração do shadcn-svelte

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P0 (bloqueante — todas as tasks de redesign dependem desta)  
**Depende de:** nenhuma  
**Estimativa:** M (2–6h)

---

## Descrição

O projeto está migrando sua camada de UI de classes CSS customizadas (`.btn`, `.card`, `.badge`, `.input`) para o ecossistema **shadcn-svelte** com ícones offline via `@iconify/svelte` e tipografia profissional via `@fontsource`. Esta task instala e configura toda a infraestrutura necessária para as tasks de redesign subsequentes (TASK-025 a TASK-031).

É uma task de **pura infraestrutura** — nenhuma página ou componente de negócio é alterado aqui.

---

## Critérios de Aceite

### Instalação de dependências

- [ ] Executar `pnpm dlx shadcn-svelte@latest init` e confirmar geração de `components.json` na raiz do projeto
- [ ] Instalar `@iconify/svelte` e `@iconify-json/lucide` como dependências de produção:
  ```bash
  pnpm add @iconify/svelte @iconify-json/lucide
  ```
- [ ] Instalar fontes `@fontsource/poppins` e `@fontsource/montserrat`:
  ```bash
  pnpm add @fontsource/poppins @fontsource/montserrat
  ```

### Adição de componentes shadcn-svelte

- [ ] Executar o CLI para adicionar todos os componentes necessários de uma vez:
  ```bash
  pnpm dlx shadcn-svelte@latest add button card badge input select checkbox dialog sonner sidebar
  ```
- [ ] Confirmar que os arquivos foram gerados em `src/lib/components/ui/` (ou caminho configurado pelo `components.json`)
- [ ] Nenhum erro de TypeScript nos componentes gerados (`pnpm typecheck` passa)

### Configuração do `app.css`

- [ ] Importar as fontes no topo do `src/app.css`:
  ```css
  @import '@fontsource/poppins/400.css';
  @import '@fontsource/poppins/600.css';
  @import '@fontsource/poppins/700.css';
  @import '@fontsource/montserrat/400.css';
  @import '@fontsource/montserrat/500.css';
  @import '@fontsource/montserrat/600.css';
  ```
- [ ] Adicionar/substituir as CSS vars do shadcn em `:root` mantendo compatibilidade com tokens existentes:
  - Variáveis `--background`, `--foreground`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--input`, `--ring` conforme padrão oklch do shadcn-svelte
  - Variáveis de fonte: `--font-heading: 'Poppins', sans-serif` e `--font-body: 'Montserrat', sans-serif`
- [ ] Manter as variáveis de tokens existentes (`--color-primary-*`, `--surface-*`, etc.) para não quebrar componentes ainda não migrados
- [ ] Atualizar `--font-sans` para apontar para Montserrat

### Verificação de funcionamento

- [ ] `pnpm dev` inicia sem erros no console
- [ ] `pnpm typecheck` passa sem erros novos introduzidos por esta task
- [ ] `pnpm build` (Vite) conclui sem erros
- [ ] A aplicação carrega no browser/WebView com fontes Poppins/Montserrat visíveis

### `components.json` configurado corretamente

- [ ] `style` definido como `"default"` (ou `"new-york"` conforme PDR-SHADCN-001)
- [ ] `tailwind.config` apontando para o projeto
- [ ] `aliases.components` e `aliases.utils` refletindo a estrutura `src/lib/`

---

## Notas Técnicas

- **PDR de referência:** `docs/pdrs/PDR-SHADCN-001.md` — consultar antes de iniciar para confirmar versões e configurações escolhidas
- **Compatibilidade Tailwind v4:** o shadcn-svelte tem suporte a Tailwind v4 a partir da versão `2.x` — verificar a versão correta no PDR
- **Tauri + Vite:** o `@fontsource` é bundled pelo Vite, não requer acesso à rede em runtime, compatível com Tauri offline
- **`@iconify-json/lucide` como offline bundle:** instalar como produção, não devDependency, pois é necessário em runtime dentro do WebView Tauri
- **Não alterar** nenhum arquivo fora de `src/app.css`, `components.json` e `src/lib/components/ui/` gerados pelo CLI
- **Risco:** o CLI do shadcn-svelte pode sobrescrever `src/app.css` — inspecionar o diff antes de aceitar ou aplicar manualmente as CSS vars

---

## Progresso

- [ ] `pnpm dlx shadcn-svelte@latest init` executado e `components.json` gerado
- [ ] Dependências `@iconify/svelte`, `@iconify-json/lucide` instaladas
- [ ] Dependências `@fontsource/poppins`, `@fontsource/montserrat` instaladas
- [ ] Componentes shadcn adicionados via CLI (button, card, badge, input, select, checkbox, dialog, sonner, sidebar)
- [ ] `src/app.css` atualizado com imports de fontes e CSS vars shadcn
- [ ] Tokens existentes preservados
- [ ] `pnpm dev` funciona sem erros
- [ ] `pnpm typecheck` passa
