# TASK-013 — Página de Eventos

**Domínio:** FRONTEND  
**Status:** DONE  
**Prioridade:** P1  
**Depende de:** TASK-008 (design system), TASK-009 (shell), TASK-010 (API layer), TASK-004 (backend events)  
**Estimativa:** M

---

## Descrição

Implementar a página de gerenciamento de eventos: lista de eventos com filtros, cadastro/edição de evento (incluindo tipo fixo/sazonal/especial), configuração de quais squads participam com mínimo/máximo de membros, e controle de status ativo/inativo.

Os eventos são a entrada principal do algoritmo de geração de escala — a configuração correta de `event_squads` é crítica para o funcionamento do sistema.

---

## Layout de Referência

```
┌─ Eventos ──────────────────── [Filtro: Todos ▼] [+ Novo Evento] ─┐
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Nome              Tipo       Dia/Data    Hora   Status       │  │
│  │ ─────────────────────────────────────────────────────────── │  │
│  │ Culto Dominical   [fixo]     Domingo     09:00  ● Ativo      │  │
│  │ Quarta de Louvor  [fixo]     Quarta      19:30  ● Ativo      │  │
│  │ Páscoa 2024       [sazonal]  31/03/2024  09:00  ● Ativo      │  │
│  │ Evento Especial   [especial] 15/06/2024  18:00  ○ Inativo    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  [Evento selecionado — painel de detalhes abaixo ou lateral]       │
│  Times configurados: Câmera (1-3) | Áudio (1-2) | Transmissão (1-2)│
└───────────────────────────────────────────────────────────────────┘
```

---

## Escopo

### 1. Store de Eventos — `src/lib/stores/events.ts`

```typescript
interface EventsState {
  items:       Event[];
  eventSquads: Record<string, EventSquad[]>;  // eventId → configuração de squads
  loading:     boolean;
  error:       string | null;
}

function createEventsStore() {
  // Operações:
  // load()                            → carrega todos os eventos
  // loadEventSquads(eventId)          → carrega configuração de squads do evento
  // create(dto)                       → cria evento
  // update(id, dto)                   → atualiza evento
  // delete(id)                        → remove evento
  // setEventSquad(dto)                → define min/max para um squad num evento
  // removeEventSquad(eventId, squadId)→ remove squad de um evento
}

export const eventsStore = createEventsStore();
```

---

### 2. Componentes da Página

#### `src/routes/events/+page.svelte`

**Estado local:**
```typescript
let filterType    = $state<EventType | 'all'>('all');
let filterActive  = $state<boolean | 'all'>('all');
let selectedId    = $state<string | null>(null);
let showModal     = $state(false);
let editingEvent  = $state<Event | null>(null);
let eventToDelete = $state<Event | null>(null);

const filtered = $derived(
  $eventsStore.items
    .filter(e => filterType === 'all' || e.event_type === filterType)
    .filter(e => filterActive === 'all' || e.active === filterActive)
);

const selected = $derived($eventsStore.items.find(e => e.id === selectedId) ?? null);
```

---

#### `EventTable.svelte`

| Prop | Tipo |
|---|---|
| `events` | `Event[]` |
| `selectedId` | `string \| null` |
| `loading` | `boolean` |
| `onselect` | `(id: string) => void` |
| `onedit` | `(event: Event) => void` |
| `ondelete` | `(event: Event) => void` |
| `ontoggleactive` | `(event: Event) => void` |

Colunas:
- **Nome**: texto
- **Tipo**: `<Badge>` com variante `fixed`/`seasonal`/`special`
- **Dia/Data**: para `fixed` → nome do dia da semana; para outros → data formatada (dd/MM/yyyy)
- **Hora**: formato HH:MM
- **Times**: lista de badges dos squads configurados (buscar de `eventSquads`)
- **Status**: badge "Ativo"/"Inativo" + botão toggle rápido
- **Ações**: ícones Editar e Excluir

**`EventTypeBadge.svelte`** (sub-componente ou variante de `Badge`):
- `fixed` → azul info ("Fixo")
- `seasonal` → amarelo warning ("Sazonal")
- `special` → roxo primary ("Especial")

---

#### `EventModal.svelte`

| Prop | Tipo |
|---|---|
| `open` | `boolean` |
| `event` | `Event \| null` |
| `onclose` | `() => void` |
| `onsaved` | `(event: Event) => void` |

**Campos — Step 1: Informações Básicas**

| Campo | Componente | Validação | Condição |
|---|---|---|---|
| Nome* | `<Input>` | Obrigatório, min 3 chars | — |
| Tipo* | `<Select>` | Obrigatório | — |
| Dia da semana* | `<Select>` | Obrigatório | `type === 'fixed'` |
| Data* | `<Input type="date">` | Obrigatório, no futuro | `type !== 'fixed'` |
| Horário | `<Input type="time">` | Formato HH:MM | — |
| Descrição | `<textarea>` | Max 300 chars | — |
| Ativo | `<input type="checkbox">` | — | Apenas edição |

- Formulário de 1 passo (não usar wizard para simplicidade)
- Campos condicionais surgem/somem com `{#if}` baseado no tipo selecionado

---

#### `EventSquadConfig.svelte`

| Prop | Tipo |
|---|---|
| `event` | `Event` |
| `eventSquads` | `EventSquad[]` |
| `allSquads` | `Squad[]` |
| `loading` | `boolean` |
| `onchange` | `(dto: SetEventSquadDto) => void` |
| `onremove` | `(squadId: string) => void` |

**Exibição:**
- Lista dos squads já configurados para o evento
- Cada item: nome do squad + inputs numéricos `min` e `max` membros + botão remover
- `<Select>` para adicionar novo squad (apenas squads não configurados)
- Validação: `min ≥ 1`, `max ≥ min`, `max ≤ total membros do squad`

**Localização:** Painel de detalhes abaixo da tabela, ou aba "Times" dentro do `EventModal` no modo edição (decidir UX e documentar).

---

### 3. Filtros da Página

```
[Tipo: Todos | Fixo | Sazonal | Especial]  [Status: Todos | Ativo | Inativo]
```

- Implementar como grupo de botões toggle (radio group)
- `role="radiogroup"`, `role="radio"`, `aria-checked`
- Manter estado nos stores de UI ou estado local da página

---

### 4. Formatação de Datas e Dias

```typescript
// src/lib/utils/format.ts (estender da TASK-011)

const WEEKDAY_LABELS: Record<Weekday, string> = {
  sunday:    'Domingo',
  monday:    'Segunda-feira',
  tuesday:   'Terça-feira',
  wednesday: 'Quarta-feira',
  thursday:  'Quinta-feira',
  friday:    'Sexta-feira',
  saturday:  'Sábado',
};

export function formatEventDate(event: Event): string {
  if (event.event_type === 'fixed') {
    return WEEKDAY_LABELS[event.weekday!] ?? '—';
  }
  return event.date ? formatDate(event.date) : '—';
}
```

---

## Critérios de Aceite

- [ ] Tabela exibe todos os eventos com tipo, dia/data, hora, times e status
- [ ] `Badge` de tipo correto para `fixed`/`seasonal`/`special`
- [ ] Filtros por tipo e status funcionam em combinação
- [ ] Selecionar evento exibe painel de configuração de squads
- [ ] Modal de criação: campos condicionais surgem corretamente por tipo
- [ ] Criação de evento `fixed` requer dia da semana; `seasonal`/`special` requer data
- [ ] Modal de edição pré-preenche todos os campos, incluindo tipo
- [ ] `EventSquadConfig` permite adicionar squad com min/max; remover squad
- [ ] Toggle de status ativo/inativo funciona diretamente na tabela sem abrir modal
- [ ] `ConfirmDialog` ao excluir evento (aviso: excluir evento remove escalas vinculadas)
- [ ] Testes de componente com cobertura ≥ 75%
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Acessível: filtros com `role="radiogroup"`, tabela navegável por teclado

---

## Notas Técnicas

- **Campos condicionais no modal**: usar `$effect()` para resetar `weekday`/`date` ao trocar o tipo de evento; evitar enviar campos irrelevantes no DTO
- **EventSquadConfig inline vs modal**: preferir exibição inline no painel de detalhes; se o modal ficar muito grande (> 600px de conteúdo), extrair para aba ou modal separado
- **Toggle de status**: chamar `eventsApi.update(id, { active: !event.active })` diretamente, sem abrir o modal completo — atualizar o item na store otimisticamente e reverter em caso de erro
- **Squads no EventSquadConfig**: reutilizar `squadsStore` (carregado pela TASK-012) ou buscar via `squadsApi.getAll()` no mount desta página
- **Validação de min/max**: implementar no frontend antes de enviar ao backend; erro `Validation` do backend deve ser exibido no campo correspondente

---

## Arquivos a Criar

```
src/
├── lib/
│   └── stores/
│       └── events.ts
└── routes/
    └── events/
        ├── +page.svelte
        ├── +page.test.ts
        ├── EventTable.svelte
        ├── EventTable.test.ts
        ├── EventModal.svelte
        ├── EventModal.test.ts
        ├── EventSquadConfig.svelte
        └── EventSquadConfig.test.ts
```

---

## Progresso

- [ ] `stores/events.ts` — load, loadEventSquads, create, update, delete, setEventSquad, removeEventSquad
- [ ] `utils/format.ts` — formatEventDate, WEEKDAY_LABELS (estender existente)
- [ ] `EventTable.svelte` + testes
- [ ] `EventModal.svelte` (campos condicionais por tipo) + testes
- [ ] `EventSquadConfig.svelte` + testes
- [ ] Filtros por tipo/status + testes
- [ ] `+page.svelte` — integração completa + testes
- [ ] `tsc --noEmit` sem erros
- [ ] `vitest --coverage` ≥ 75%
