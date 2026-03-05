# TASK-015 — Páginas de Disponibilidade e Casais

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-008 (design system), TASK-009 (shell), TASK-010 (API layer), TASK-006 (backend availability + couples), TASK-011 (members)  
**Estimativa:** M

---

## Descrição

Implementar duas páginas de configuração que alimentam o algoritmo de geração de escala:

1. **Disponibilidade** (`/availability`): gerenciar períodos de indisponibilidade por membro — quando um membro não pode servir (viagem, férias, evento pessoal).
2. **Casais** (`/couples`): gerenciar restrições de casais — pares de membros que o algoritmo **sempre escala juntos** no mesmo evento (não podem ser separados).

---

## Escopo — Disponibilidade

### Layout de Referência

```
┌─ Disponibilidade ──────────────────────── [+ Registrar Indisponibilidade] ─┐
│  Membro: [Todos ▼]   Período: [Mar 2024 ▼]                                 │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Membro           Início      Fim          Motivo          Ações      │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ João Silva       01/03/2024  07/03/2024   Viagem          [🗑]       │   │
│  │ Ana Lima         15/03/2024  15/03/2024   Consulta médica [🗑]       │   │
│  │ Pedro Costa      20/03/2024  25/03/2024   —               [🗑]       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1. Store — `src/lib/stores/availability.ts`

```typescript
interface AvailabilityState {
  items:   Availability[];
  loading: boolean;
  error:   string | null;
}

function createAvailabilityStore() {
  // load()        → carrega todos os períodos de indisponibilidade
  // create(dto)   → registra novo período
  // delete(id)    → remove período
}

export const availabilityStore = createAvailabilityStore();
```

### 2. Componentes da Página — `src/routes/availability/`

#### `+page.svelte`

**Estado local:**
```typescript
let filterMemberId = $state<string | null>(null);  // null = todos
let filterMonth    = $state<string | null>(null);   // 'YYYY-MM' ou null = todos
let showModal      = $state(false);
let itemToDelete   = $state<Availability | null>(null);

const filtered = $derived(
  $availabilityStore.items
    .filter(a => filterMemberId === null || a.member_id === filterMemberId)
    .filter(a => filterMonth === null || a.start_date.startsWith(filterMonth))
    .sort((a, b) => a.start_date.localeCompare(b.start_date))
);
```

- Carregar `availabilityStore.load()` e `membersStore.load()` no `onMount`

#### `AvailabilityTable.svelte`

| Prop | Tipo |
|---|---|
| `items` | `Availability[]` |
| `members` | `Member[]` (lookup por `member_id`) |
| `loading` | `boolean` |
| `ondelete` | `(item: Availability) => void` |

Colunas: **Membro**, **Início**, **Fim**, **Duração** (N dias), **Motivo**, **Ações** (🗑)

- Datas formatadas em dd/MM/yyyy (pt-BR)
- Duração calculada: `differenceInDays(end, start) + 1` dias
- Membro: exibir nome buscando em `members` pelo `member_id`
- Ordenar por data de início (mais recentes primeiro)
- `EmptyState` quando sem registros

#### `AvailabilityModal.svelte`

| Prop | Tipo |
|---|---|
| `open` | `boolean` |
| `members` | `Member[]` |
| `onclose` | `() => void` |
| `onsaved` | `(item: Availability) => void` |

Campos:

| Campo | Componente | Validação |
|---|---|---|
| Membro* | `<Select searchable>` | Obrigatório |
| Data de início* | `<Input type="date">` | Obrigatório |
| Data de fim* | `<Input type="date">` | ≥ Data de início |
| Motivo | `<Input>` | Opcional, max 100 chars |

- Validação: data de fim não pode ser anterior à de início
- Ao submeter com sucesso: fechar modal e exibir toast "Indisponibilidade registrada"
- Não editar — apenas criar novo ou excluir; simplifica o fluxo

#### Filtros

```
[Membro: Todos ▼]  [Período: Todos | Este mês | Próximo mês | Mês específico]
```

- `<Select>` de membro: lista de membros ativos + opção "Todos"
- Seletor de período: mês/ano via `<Select>` com opções pré-definidas + "todos"

---

## Escopo — Casais

### Layout de Referência

```
┌─ Casais ──────────────────────────────────────── [+ Registrar Casal] ─┐
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ ┌──────────────┐  ┌──────────────┐  Desde        Ações         │   │
│  │ │ 👤 João Silva │❤️│ 👤 Ana Lima  │  Jan/2024     [🗑 Remover]  │   │
│  │ └──────────────┘  └──────────────┘                              │   │
│  │ ┌──────────────┐  ┌──────────────┐                              │   │
│  │ │ 👤 Carlos F.  │❤️│👤 Maria Souza│  Fev/2024     [🗑 Remover]  │   │
│  │ └──────────────┘  └──────────────┘                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ℹ️ Casais cadastrados são sempre escalados juntos no mesmo evento.      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Store — `src/lib/stores/couples.ts`

```typescript
interface CouplesState {
  items:   Couple[];
  loading: boolean;
  error:   string | null;
}

function createCouplesStore() {
  // load()      → carrega todos os casais
  // create(dto) → registra casal
  // delete(id)  → remove casal
}

export const couplesStore = createCouplesStore();
```

### 4. Componentes da Página — `src/routes/couples/`

#### `+page.svelte`

```typescript
let showModal      = $state(false);
let coupleToDelete = $state<Couple | null>(null);

// Enriquecer casais com nomes dos membros para exibição
const enrichedCouples = $derived(
  $couplesStore.items.map(couple => ({
    ...couple,
    memberA: $membersStore.items.find(m => m.id === couple.member_a_id),
    memberB: $membersStore.items.find(m => m.id === couple.member_b_id),
  }))
);
```

#### `CoupleCard.svelte`

| Prop | Tipo |
|---|---|
| `couple` | `Couple` |
| `memberA` | `Member \| undefined` |
| `memberB` | `Member \| undefined` |
| `ondelete` | `() => void` |

- Layout visual: dois chips de membro separados por ícone ❤ (`Heart` do lucide)
- Data de registro formatada
- Botão "Remover" com ícone `Trash2`
- `role="article"`, `aria-label="Casal: {nomeA} e {nomeB}"`

#### `CoupleModal.svelte`

| Prop | Tipo |
|---|---|
| `open` | `boolean` |
| `members` | `Member[]` |
| `existingCouples` | `Couple[]` |
| `onclose` | `() => void` |
| `onsaved` | `(couple: Couple) => void` |

Campos:

| Campo | Componente | Validação |
|---|---|---|
| Membro A* | `<Select searchable>` | Obrigatório; diferente de Membro B |
| Membro B* | `<Select searchable>` | Obrigatório; diferente de Membro A |

- Validar que o par não existe ainda (verificar `existingCouples` antes de submeter)
- Erro `Conflict` do backend exibido caso passe a validação frontend mas falhe no backend
- Membro A selecionado: remover Membro A das opções de Membro B (e vice-versa)
- Membros já em algum casal: destacar com aviso "(já em casal)" mas permitir selecionar

**Nota semântica**: A spec define casais como "*restrição de escalá-los juntos*" — **sempre juntos**, não separados. O texto da UI deve esclarecer isso: "Membros cadastrados como casal são sempre escalados juntos no mesmo serviço."

---

### 5. Banner Informativo

Em ambas as páginas, exibir um banner educativo:

**Disponibilidade:**
> ℹ️ Períodos registrados aqui são respeitados automaticamente na geração de escalas. O membro não será escalado em datas dentro deste período.

**Casais:**
> ❤️ Membros cadastrados como casal são sempre escalados juntos no mesmo evento. O algoritmo garante que ambos sirvam nas mesmas datas ou nenhum sirva.

```svelte
<!-- InfoBanner.svelte (componente genérico) -->
<div class="info-banner" role="note">
  <InfoIcon size={16} />
  <p><slot /></p>
</div>
```

---

## Critérios de Aceite — Disponibilidade

- [ ] Lista exibe todos os períodos com membro, datas, duração e motivo
- [ ] Filtro por membro funciona; filtro por período funciona; combinação funciona
- [ ] Botão "+ Registrar" abre modal com Select de membros buscável
- [ ] Validação: data fim ≥ data início; membro obrigatório; erro exibido inline
- [ ] Salvar registra no backend e adiciona à lista sem recarregar
- [ ] Excluir exibe `ConfirmDialog` e remove da lista com toast
- [ ] `EmptyState` quando sem registros; mensagem específica quando filtro ativo
- [ ] Banner informativo exibido no topo da página

## Critérios de Aceite — Casais

- [ ] Lista exibe todos os casais com nomes dos dois membros e data de registro
- [ ] Layout visual com dois chips + ❤ entre eles
- [ ] Botão "+ Registrar Casal" abre modal com dois Selects buscáveis
- [ ] Membro A não pode ser igual a Membro B (validação imediata)
- [ ] Par duplicado: erro de `Conflict` exibido (frontend + backend)
- [ ] Excluir casal exibe confirmação e remove da lista
- [ ] `EmptyState` quando sem casais cadastrados
- [ ] Banner informativo exibido no topo da página

## Critérios de Aceite — Gerais

- [ ] Testes de componente (Vitest) com cobertura ≥ 75% em ambas as páginas
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Acessível: `role="note"` no banner, `role="article"` nos cards de casal, labels em todos os selects

---

## Notas Técnicas

- **Membros necessários em ambas as páginas**: ambas dependem de `membersStore` já populado; chamar `membersStore.load()` no `onMount` se não carregado, ou verificar o estado antes de renderizar o Select
- **Sem edição de disponibilidade**: fluxo simplificado — criar e excluir; editar adicionaria complexidade sem ganho real (basta excluir e criar novo)
- **Sem edição de casal**: mesma lógica — excluir e criar novo
- **`InfoBanner.svelte`**: componente genérico, adicionar ao barrel `src/lib/components/ui/index.ts`; usar em ambas as páginas
- **Ordenação de casais**: ordenar por `created_at` descendente (mais recentes primeiro)
- **Datas no pt-BR**: usar `Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' })` para exibir "março de 2024"; função em `utils/format.ts`
- **`differenceInDays`**: implementar como função pura em `utils/dates.ts` sem instalar date-fns — usar aritmética simples com timestamps

---

## Arquivos a Criar

```
src/
├── lib/
│   ├── stores/
│   │   ├── availability.ts
│   │   └── couples.ts
│   └── components/
│       └── ui/
│           └── InfoBanner.svelte        ← novo componente genérico
└── routes/
    ├── availability/
    │   ├── +page.svelte
    │   ├── +page.test.ts
    │   ├── AvailabilityTable.svelte
    │   ├── AvailabilityTable.test.ts
    │   ├── AvailabilityModal.svelte
    │   └── AvailabilityModal.test.ts
    └── couples/
        ├── +page.svelte
        ├── +page.test.ts
        ├── CoupleCard.svelte
        ├── CoupleCard.test.ts
        ├── CoupleModal.svelte
        └── CoupleModal.test.ts
```

---

## Progresso

**Disponibilidade:**
- [ ] `stores/availability.ts` — load, create, delete
- [ ] `AvailabilityTable.svelte` + testes
- [ ] `AvailabilityModal.svelte` + validação + testes
- [ ] Filtros por membro e período + testes
- [ ] `availability/+page.svelte` — integração + testes

**Casais:**
- [ ] `stores/couples.ts` — load, create, delete
- [ ] `CoupleCard.svelte` + testes
- [ ] `CoupleModal.svelte` + validação (par único + membros distintos) + testes
- [ ] `couples/+page.svelte` — integração + testes

**Compartilhado:**
- [ ] `InfoBanner.svelte` adicionado ao barrel `ui/index.ts`
- [ ] `utils/dates.ts` — `differenceInDays` + helpers de mês
- [ ] `utils/format.ts` — formatação de mês/ano pt-BR
- [ ] `tsc --noEmit` sem erros
- [ ] `vitest --coverage` ≥ 75%
