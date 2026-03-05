# TASK-023 — Dashboard: KPIs Completos e Próximos Eventos

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P2 (normal — funcional mas sem valor agregado atualmente)  
**Depende de:** TASK-019, TASK-021 (toast), TASK-022 (schedule table)  
**Estimativa:** S (< 2h)

---

## Descrição

O dashboard atual exibe apenas três números (membros, times, eventos) sem contexto. A spec (§8) define **KPI cards** com número + label + indicadores, além de informações contextuais relevantes para o coordenador de mídia: próximo evento, membros recentemente escalados e alertas de configuração.

---

## Critérios de Aceite

### KPI Cards (linha superior)

- [ ] Card **Membros** — número total + sub-texto "N ativos"
- [ ] Card **Times** — número total + sub-texto "N configurados com membros"
- [ ] Card **Eventos** — número total + sub-texto "N este mês"
- [ ] Cards com largura igual em grid de 3 colunas (já existe, adaptar)
- [ ] Cada card tem ícone à esquerda: membros → `Users`, times → `Layers`, eventos → `Calendar`

### Seção "Próximo Evento"

- [ ] Buscar o evento com `event_date` mais próxima (hoje ou futura) dos eventos cadastrados
- [ ] Exibir: nome, data formatada (ex: "domingo, 8 de março de 2026"), tipo com badge
- [ ] Se o evento tiver squads configurados: exibir "✓ N times configurados" em verde
- [ ] Se o evento **não** tiver squads configurados: exibir alerta "⚠ Sem times configurados — [Configurar]" em amarelo, com link para `/events`
- [ ] Se não houver eventos futuros: EmptyState "Nenhum evento próximo. [+ Criar evento]"

### Seção "Alertas"

Lista de alertas automáticos (cards pequenos em amarelo/vermelho):

- [ ] **"N eventos sem times configurados"** → eventos com `event_squads` vazio. Link para `/events`
- [ ] **"N membros em nenhum time"** → membros ativos sem associação em `members_squads`. Link para `/squads`
- [ ] Se não houver alertas: mensagem "✓ Tudo configurado!" em verde

### Layout Geral

```
┌─ Dashboard ───────────────────────────────────────────────────┐
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                  │
│  │👥 Membros │  │🗂️ Times    │  │📅 Eventos │                  │
│  │    10     │  │    5      │  │    3      │                  │
│  │ 10 ativos │  │ 4 c/ mbrs │  │ 2 este mês│                  │
│  └───────────┘  └───────────┘  └───────────┘                  │
│                                                                │
│  ── Próximo Evento ──────────────────────────────────────      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Culto Domingo                                          │   │
│  │ domingo, 8 de março de 2026  [regular]                │   │
│  │ ⚠ Sem times configurados — [Configurar]               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ── Alertas ─────────────────────────────────────────────      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ ⚠ 2 eventos sem times configurados          [Corrigir] │   │
│  │ ⚠ 1 membro ativo sem time associado         [Corrigir] │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### Dados necessários

O dashboard precisa de dados que já existem via API:
- `getMembers()` → contar ativos
- `getSquads()` → contar; cruzar com `members_squads` para saber quais têm membros
- `getEvents()` → próximo evento + contar

Para "eventos sem times configurados" e "membros sem times", usar as APIs existentes e cruzar no frontend (sem novo command Tauri necessário, dado o volume pequeno de dados).

**Sequência de carregamento:**
```typescript
onMount(async () => {
  const [members, squads, events] = await Promise.all([
    getMembers(), getSquads(), getEvents()
  ]);
  // calcular KPIs e alertas localmente
});
```

### Formatação de Data em PT-BR

- [ ] Implementar `formatDateLong(isoDate: string): string` em `src/lib/utils/index.ts`:
  ```typescript
  export function formatDateLong(iso: string): string {
    return new Date(iso + 'T00:00:00').toLocaleDateString('pt-BR', {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
  }
  ```
- [ ] Testar com Vitest: `formatDateLong('2026-03-08')` → `'domingo, 8 de março de 2026'`

### Testes Vitest

- [ ] Lógica de "próximo evento" (pura, sem DOM):
  - `getNextEvent([...events], today)` retorna evento com menor `event_date >= today`
  - Lista vazia → `null`
  - Todos eventos passados → `null`
- [ ] Lógica de alertas:
  - `getEventsWithoutSquads(events, eventSquadsMap)` → lista de eventos sem squads configurados

---

## Notas Técnicas

- A função `getNextEvent` deve receber `today` como parâmetro (não `Date.now()` internamente) para ser testável deterministicamente.
- Para verificar "membros sem times", cruzar `members` com `members_squads` retornados por `getSquadMembers` de cada squad — pode ser custoso se houver muitos squads. Alternativa: adicionar um command Tauri `get_members_without_squads` no futuro. Por ora, fazer o cruzamento client-side com os dados já carregados.
- Links de "Corrigir" / "Configurar" devem usar o roteamento existente (mudar a rota via `goto` do SvelteKit ou pelo store de rota atual).
