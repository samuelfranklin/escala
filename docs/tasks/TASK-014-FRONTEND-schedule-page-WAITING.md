# TASK-014 — Página de Escala (Geração e Visualização)

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-008 (design system), TASK-009 (shell), TASK-010 (API layer), TASK-005 (backend schedule), TASK-011 (members), TASK-012 (squads), TASK-013 (events)  
**Estimativa:** L

---

## Descrição

Implementar a página de geração e visualização de escalas: seleção de evento e datas, botão "Gerar Escala" com estado de loading, tabela de resultado (Squad × Data × Membros) e ações de exportação (CSV e PDF). Esta é a funcionalidade central do produto.

---

## Wireframe de Referência (spec §8)

```
┌─ Gerar Escala ───────────────────────────────────────────────┐
│  Evento: [Culto Dominical          ▼]  Período: [março 2024] │
│  Datas:  ☑ 03/03  ☑ 10/03  ☑ 17/03  ☑ 24/03  ☑ 31/03      │
│  [⚡ Gerar Escala]                                            │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ Data    │ Câmera          │ Áudio       │ Transmissão  │   │
│ │ 03/03   │ João · Ana      │ Pedro       │ Maria · Luiz │   │
│ │ 10/03   │ Carlos · Rita   │ João        │ Ana · Pedro  │   │
│ │ ...                                                     │   │
│ └────────────────────────────────────────────────────────┘   │
│  [📋 Copiar] [📤 Exportar CSV] [📤 Exportar PDF]              │
└──────────────────────────────────────────────────────────────┘
```

---

## Escopo

### 1. Store de Escala — `src/lib/stores/schedule.ts`

```typescript
interface ScheduleState {
  /** Escala atualmente exibida */
  current:    ScheduleView[] | null;
  /** ID da escala gerada (para exportar) */
  scheduleId: string | null;
  generating: boolean;
  exporting:  boolean;
  error:      string | null;
}

function createScheduleStore() {
  const { subscribe, update, set } = writable<ScheduleState>({
    current:    null,
    scheduleId: null,
    generating: false,
    exporting:  false,
    error:      null,
  });

  return {
    subscribe,

    generate: async (dto: GenerateScheduleDto): Promise<boolean> => {
      update((s) => ({ ...s, generating: true, error: null, current: null }));
      const result = await scheduleApi.generate(dto);
      if (result.ok) {
        const view = buildScheduleView(result.data);  // montar ScheduleView[]
        update((s) => ({
          ...s,
          generating: false,
          current: view,
          scheduleId: result.data[0]?.schedule.id ?? null,
        }));
        return true;
      }
      update((s) => ({ ...s, generating: false, error: result.error.message }));
      toastStore.error(result.error.message);
      return false;
    },

    exportCsv: async (scheduleId: string) => { /* ... */ },
    exportPdf: async (scheduleId: string) => { /* ... */ },

    clear: () => set({ current: null, scheduleId: null, generating: false, exporting: false, error: null }),
  };
}

export const scheduleStore = createScheduleStore();

/** Monta ScheduleView[] a partir dos ScheduleResult[] retornados pelo backend */
function buildScheduleView(results: ScheduleResult[]): ScheduleView[] {
  // Enriquecer com nomes de squads e membros (buscando dos stores)
  // Agrupar por data
}
```

---

### 2. Componentes da Página

#### `src/routes/schedule/+page.svelte`

```svelte
<script lang="ts">
  import { eventsStore }   from '$lib/stores/events';
  import { scheduleStore } from '$lib/stores/schedule';
  import EventSelector     from './EventSelector.svelte';
  import DatePicker        from './DatePicker.svelte';
  import ScheduleTable     from './ScheduleTable.svelte';
  import ExportActions     from './ExportActions.svelte';

  let selectedEventId = $state<string | null>(null);
  let selectedDates   = $state<string[]>([]);       // ISO dates selecionadas
  let viewMonth       = $state(new Date());          // mês sendo visualizado

  const selectedEvent = $derived(
    $eventsStore.items.find(e => e.id === selectedEventId) ?? null
  );

  // Gerar datas sugeridas baseado no tipo do evento
  const suggestedDates = $derived(
    selectedEvent ? computeSuggestedDates(selectedEvent, viewMonth) : []
  );

  async function handleGenerate() {
    if (!selectedEventId || selectedDates.length === 0) return;
    await scheduleStore.generate({ event_id: selectedEventId, dates: selectedDates });
  }
</script>
```

---

#### `EventSelector.svelte`

| Prop | Tipo |
|---|---|
| `events` | `Event[]` |
| `value` | `string \| null` |
| `onchange` | `(eventId: string) => void` |
| `loading` | `boolean` |

- `<Select searchable>` com lista de eventos ativos
- Exibir nome + tipo de evento no label da opção
- Ao mudar evento, limpar datas selecionadas e escala atual

---

#### `DatePicker.svelte`

| Prop | Tipo |
|---|---|
| `event` | `Event \| null` |
| `selected` | `string[]` |
| `viewMonth` | `Date` |
| `onchange` | `(dates: string[]) => void` |
| `onmonthchange` | `(month: Date) => void` |

**Comportamento por tipo de evento:**

- **`fixed`** (ex: todo domingo): auto-sugerir todas as ocorrências do dia no mês selecionado; checkboxes pré-marcados; permite desmarcar individualmente
- **`seasonal`/`special`**: exibir apenas a data do evento como checkbox único; ou permitir seleção manual em calendário simplificado

**Layout:**
```
Período: [< março 2024 >]
Datas disponíveis:
  ☑ Dom, 03/03    ☑ Dom, 10/03    ☑ Dom, 17/03
  ☑ Dom, 24/03    ☑ Dom, 31/03

[Marcar todos]  [Desmarcar todos]
```

- `<input type="checkbox">` para cada data
- Label com data formatada em pt-BR (ex: "Dom, 03/03")
- Botões "Marcar todos" e "Desmarcar todos"
- Navegação de mês: `<` e `>` alteram `viewMonth`
- Quando nenhuma data selecionada: botão Gerar desabilitado

---

#### `ScheduleTable.svelte`

| Prop | Tipo |
|---|---|
| `schedule` | `ScheduleView[] \| null` |
| `loading` | `boolean` |
| `error` | `string \| null` |

**Estados:**

1. **Inicial (null)**: `<EmptyState icon={ClipboardList} title="Selecione um evento e gere a escala" />`
2. **Gerando**: spinner centralizado com texto "Gerando escala..." + barra de progresso indeterminada
3. **Erro**: `<EmptyState>` com mensagem de erro e botão "Tentar novamente"
4. **Com dados**: tabela conforme wireframe

**Estrutura da tabela:**

```
┌──────────┬─────────────────┬─────────────┬────────────────┐
│  Data    │  Câmera (1-3)   │  Áudio (1)  │  Transmissão   │
├──────────┼─────────────────┼─────────────┼────────────────┤
│ 03/03    │ João Silva      │ Pedro Costa │ Maria · Luiz   │
│          │ Ana Lima        │             │                │
├──────────┼─────────────────┼─────────────┼────────────────┤
│ 10/03    │ Carlos · Rita   │ João        │ Ana · Pedro    │
└──────────┴─────────────────┴─────────────┴────────────────┘
```

- Colunas dinâmicas: uma por squad configurado no evento
- Cabeçalho de squad: nome + "(min-max)" em `--text-xs`
- Células: lista de membros separados por ponto médio `·`
- `role="table"`, `role="columnheader"`, `role="row"`, `role="cell"`
- Linhas alternadas via CSS (`nth-child`) para leitura mais fácil

---

#### `ExportActions.svelte`

| Prop | Tipo |
|---|---|
| `scheduleId` | `string \| null` |
| `schedule` | `ScheduleView[] \| null` |
| `exporting` | `boolean` |
| `onexportcsv` | `() => void` |
| `onexportpdf` | `() => void` |
| `oncopy` | `() => void` |

- Botão "📋 Copiar": copia texto formatado para clipboard (sem salvar arquivo)
- Botão "📤 Exportar CSV": chama `scheduleApi.exportCsv()` → salva via `tauri-plugin-dialog` + `tauri-plugin-fs`
- Botão "📤 Exportar PDF": chama `scheduleApi.exportPdf()` → salva via dialog nativo
- Todos os botões desabilitados quando `schedule === null`
- Botões CSV/PDF com `loading=true` durante `exporting`

**Formato do texto para copiar:**
```
ESCALA — Culto Dominical — março/2024

03/03:
  Câmera: João Silva, Ana Lima
  Áudio: Pedro Costa
  Transmissão: Maria Souza, Luiz Santos

10/03:
  ...
```

---

### 3. Lógica de Datas Sugeridas

```typescript
// src/lib/utils/dates.ts
import type { Event, Weekday } from '$lib/types';

const WEEKDAY_INDEX: Record<Weekday, number> = {
  sunday: 0, monday: 1, tuesday: 2, wednesday: 3,
  thursday: 4, friday: 5, saturday: 6,
};

/**
 * Retorna todas as ocorrências de um evento 'fixed' no mês dado.
 * Ex: todos os domingos de março → ['2024-03-03', '2024-03-10', ...]
 */
export function computeSuggestedDates(event: Event, month: Date): string[] {
  if (event.event_type === 'fixed' && event.weekday) {
    const target = WEEKDAY_INDEX[event.weekday];
    const dates: string[] = [];
    const d = new Date(month.getFullYear(), month.getMonth(), 1);
    while (d.getMonth() === month.getMonth()) {
      if (d.getDay() === target) dates.push(d.toISOString().slice(0, 10));
      d.setDate(d.getDate() + 1);
    }
    return dates;
  }
  if (event.date) return [event.date];
  return [];
}
```

---

## Critérios de Aceite

- [ ] Dropdown de eventos lista apenas eventos ativos
- [ ] Ao selecionar evento `fixed`, datas do mês corrente são auto-sugeridas e pré-marcadas
- [ ] Seletor de mês (< >) atualiza as datas sugeridas
- [ ] "Marcar todos" / "Desmarcar todos" funcionam corretamente
- [ ] Botão "Gerar Escala" desabilitado sem evento selecionado ou sem datas
- [ ] Durante geração: spinner visível, botão com `loading=true`, tabela não exibida
- [ ] Escala gerada renderizada em tabela com colunas por squad e linhas por data
- [ ] Número de membros por célula respeita `min_members`/`max_members` configurados
- [ ] Botão "Copiar" copia texto formatado para clipboard
- [ ] Exportar CSV/PDF abre dialog nativo de salvar arquivo
- [ ] Estado de loading durante exportação; toast de sucesso/erro
- [ ] `EmptyState` no estado inicial e em caso de erro
- [ ] Testes de componente com cobertura ≥ 75% (incluindo lógica de datas)
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Acessível: tabela com roles corretos, loading anunciado via `aria-live`

---

## Notas Técnicas

- **`buildScheduleView`**: enriquecer os IDs retornados pelo backend com nomes — buscar de `membersStore` e `squadsStore` localmente (evitar N+1 requests)
- **Timeout de geração**: o algoritmo pode levar alguns segundos para muitos eventos; mostrar feedback de progresso indeterminado; não definir timeout no frontend
- **Exportar**: `scheduleApi.exportCsv()` retorna string com conteúdo do CSV; usar `tauri-plugin-dialog` para `save()` e `tauri-plugin-fs` para `writeTextFile()`; toda essa lógica fica em `ExportActions.svelte`
- **Copiar para clipboard**: usar `navigator.clipboard.writeText()` — disponível em WebView do Tauri
- **Geração idempotente**: o backend cria uma nova escala a cada chamada; não implementar deduplicação no frontend nesta task
- **`computeSuggestedDates`**: cobrir com testes unitários (função pura, sem dependência de API)

---

## Arquivos a Criar

```
src/
├── lib/
│   ├── stores/
│   │   └── schedule.ts
│   └── utils/
│       └── dates.ts                    ← computeSuggestedDates + helpers
└── routes/
    └── schedule/
        ├── +page.svelte
        ├── +page.test.ts
        ├── EventSelector.svelte
        ├── EventSelector.test.ts
        ├── DatePicker.svelte
        ├── DatePicker.test.ts
        ├── ScheduleTable.svelte
        ├── ScheduleTable.test.ts
        ├── ExportActions.svelte
        └── ExportActions.test.ts
```

---

## Progresso

- [ ] `utils/dates.ts` — `computeSuggestedDates` + testes unitários
- [ ] `stores/schedule.ts` — generate, exportCsv, exportPdf, clear
- [ ] `EventSelector.svelte` + testes
- [ ] `DatePicker.svelte` (sugestão automática + navegação de mês) + testes
- [ ] `ScheduleTable.svelte` (estados: inicial, loading, erro, dados) + testes
- [ ] `ExportActions.svelte` (copiar, CSV, PDF) + testes
- [ ] `+page.svelte` — integração completa + testes
- [ ] `tsc --noEmit` sem erros
- [ ] `vitest --coverage` ≥ 75%
