# TASK-012 — Página de Times (Squads)

**Domínio:** FRONTEND  
**Status:** DONE  
**Prioridade:** P1  
**Depende de:** TASK-008 (design system), TASK-009 (shell), TASK-010 (API layer), TASK-003 (backend squads)  
**Estimativa:** M

---

## Descrição

Implementar a página de gerenciamento de times (squads): lista de squads com composição de membros, criação e edição de times, e a interface para adicionar/remover membros de um squad. A composição de cada squad é central para o algoritmo de geração de escala.

---

## Layout de Referência

```
┌─ Times ─────────────────────────────────────── [+ Novo Time] ─┐
│ ┌─────────────────────────┐  ┌────────────────────────────────┐│
│ │ 🎬 Câmera          4 👥 │  │ 🎬 Câmera                      ││
│ │ Equipe de filmagem      │  │ ─────────────────────────────  ││
│ │                         │  │ Membros (4)        [+ Adicionar]││
│ │ 🎛 Áudio           3 👥 │  │                                ││
│ │ Equipe de som           │  │ ► João Silva   👑 Líder   [✕] ││
│ │                         │  │   Ana Lima     🎓 Trainer  [✕] ││
│ │ 📡 Transmissão     2 👥 │  │   Pedro Costa  ✓ Membro   [✕] ││
│ │                         │  │   Maria Souza  ✓ Membro   [✕] ││
│ │ [✏] [🗑] por card        │  │                                ││
│ └─────────────────────────┘  │ [✏ Editar Time] [🗑 Excluir]   ││
│                               └────────────────────────────────┘│
└───────────────────────────────────────────────────────────────┘
```

---

## Escopo

### 1. Store de Squads — `src/lib/stores/squads.ts`

```typescript
interface SquadsState {
  items:          Squad[];
  memberships:    Record<string, Member[]>;  // squadId → membros
  loading:        boolean;
  loadingMembers: Record<string, boolean>;
  error:          string | null;
}

function createSquadsStore() {
  // Operações:
  // load()                              → carrega todos os squads
  // loadMembers(squadId)                → carrega membros de um squad específico
  // create(dto)                         → cria squad + adiciona à lista
  // update(id, dto)                     → atualiza squad
  // delete(id)                          → remove squad
  // addMember(squadId, memberId)        → adiciona membro + atualiza memberships
  // removeMember(squadId, memberId)     → remove membro + atualiza memberships
}

export const squadsStore = createSquadsStore();
```

**`memberships`**: cache local `Record<squadId, Member[]>`. Carregar sob demanda ao selecionar um squad, não no load inicial.

---

### 2. Componentes da Página

#### `src/routes/squads/+page.svelte`

**Estado local:**
```typescript
let selectedSquadId = $state<string | null>(null);
let showCreateModal = $state(false);
let editingSquad    = $state<Squad | null>(null);
let squadToDelete   = $state<Squad | null>(null);
let showAddMember   = $state(false);

const selectedSquad   = $derived($squadsStore.items.find(s => s.id === selectedSquadId) ?? null);
const selectedMembers = $derived(selectedSquadId ? ($squadsStore.memberships[selectedSquadId] ?? []) : []);
```

- Chamar `squadsStore.load()` no `onMount`
- Ao selecionar um squad, chamar `squadsStore.loadMembers(squadId)` se não estiver em cache

---

#### `SquadCard.svelte`

| Prop | Tipo |
|---|---|
| `squad` | `Squad` |
| `memberCount` | `number` |
| `selected` | `boolean` |
| `onselect` | `() => void` |
| `onedit` | `() => void` |
| `ondelete` | `() => void` |

- Card com `var(--surface-card)` + borda `var(--surface-border)`
- Card selecionado: borda `var(--color-primary-500)`, fundo `var(--surface-elevated)`
- Ícone genérico de time (ou inicial do nome em círculo colorido)
- Contagem de membros com ícone `Users`
- Botões Editar / Excluir no hover ou sempre visíveis (avaliar UX)
- `role="button"`, `aria-pressed={selected}`, `aria-label="Selecionar time {squad.name}"`

---

#### `SquadMemberList.svelte`

| Prop | Tipo |
|---|---|
| `squad` | `Squad \| null` |
| `members` | `Member[]` |
| `loading` | `boolean` |
| `onaddmember` | `() => void` |
| `onremovemember` | `(memberId: string) => void` |

- Quando `squad === null`: `<EmptyState>` "Selecione um time"
- Quando `loading`: spinner centralizado
- Lista de membros com nome, `<Badge>` de patente e botão ✕ para remover
- Botão "+ Adicionar Membro" no topo da lista
- Confirmação inline ao remover: "Remover {nome} de {squad.name}?"
- `EmptyState` quando squad não tem membros (CTA "+ Adicionar")

---

#### `SquadModal.svelte`

| Prop | Tipo |
|---|---|
| `open` | `boolean` |
| `squad` | `Squad \| null` (null = criar) |
| `onclose` | `() => void` |
| `onsaved` | `(squad: Squad) => void` |

Campos:
| Campo | Validação |
|---|---|
| Nome* | Obrigatório, único (validar no submit via erro de `Conflict` do backend) |
| Descrição | Opcional, max 200 chars |

---

#### `AddMemberToSquadModal.svelte`

| Prop | Tipo |
|---|---|
| `open` | `boolean` |
| `squad` | `Squad` |
| `currentMembers` | `Member[]` |
| `onclose` | `() => void` |
| `onadded` | `(member: Member) => void` |

- `<Select searchable>` com lista de **todos os membros ativos** não pertencentes ao squad
- Filtrar do `membersStore` os que já são membros do squad atual
- Submit chama `squadsApi.addMember()` + `onadded()`

---

### 3. Visualização de Composição

Ao selecionar um squad, o painel direito deve mostrar:
- Nome e descrição do squad
- Contagem: "X membros" 
- Lista de membros com patente e botão remover
- Distribuição por patente: mini-gráfico de barras CSS (sem biblioteca)
  - Ex: "Líder: 1 | Trainer: 1 | Membro: 2"
- Ações: Editar time, Excluir time

---

## Critérios de Aceite

- [ ] Lista de squads exibe cards com nome, descrição e contagem de membros
- [ ] Selecionar um card carrega e exibe a composição do squad no painel direito
- [ ] Membros são carregados sob demanda (não no load inicial da página)
- [ ] Botão "+ Novo Time" abre modal de criação; squad aparece na lista após criação
- [ ] Editar squad atualiza nome/descrição na lista e no painel
- [ ] Excluir squad exibe `ConfirmDialog`; remove da lista com toast
- [ ] "+ Adicionar Membro" abre modal com Select buscável de membros disponíveis
- [ ] Remover membro do squad exibe confirmação inline e atualiza a lista
- [ ] Erro de nome duplicado (`Conflict`) exibido no campo do formulário
- [ ] `EmptyState` quando não há squads; `EmptyState` quando squad não tem membros
- [ ] Testes de componente com cobertura ≥ 75%
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Acessível: cards com `aria-pressed`, listas com `role`, foco gerenciado em modais

---

## Notas Técnicas

- **Cache de membros**: `squadsStore.memberships` persiste durante a sessão; invalidar ao adicionar/remover membro do squad; não re-fetch ao re-selecionar o mesmo squad se já em cache
- **Membros disponíveis no AddModal**: derivar de `membersStore.items` (deve estar carregado da página de membros ou ser carregado no mount desta página) filtrando os que já pertencem ao squad
- **Svelte 5**: usar `$derived.by()` para computações mais complexas (ex: membros disponíveis com filtro)
- **Confirmação inline de remoção**: implementar com estado local `removingMemberId: string | null` — sem modal completo, apenas linha expandida com "Confirmar remoção?"

---

## Arquivos a Criar

```
src/
├── lib/
│   └── stores/
│       └── squads.ts
└── routes/
    └── squads/
        ├── +page.svelte
        ├── +page.test.ts
        ├── SquadCard.svelte
        ├── SquadCard.test.ts
        ├── SquadMemberList.svelte
        ├── SquadMemberList.test.ts
        ├── SquadModal.svelte
        ├── SquadModal.test.ts
        ├── AddMemberToSquadModal.svelte
        └── AddMemberToSquadModal.test.ts
```

---

## Progresso

- [ ] `stores/squads.ts` — load, loadMembers, create, update, delete, addMember, removeMember
- [ ] `SquadCard.svelte` + testes
- [ ] `SquadMemberList.svelte` + testes
- [ ] `SquadModal.svelte` + testes
- [ ] `AddMemberToSquadModal.svelte` + testes
- [ ] `+page.svelte` — integração completa + testes
- [ ] `tsc --noEmit` sem erros
- [ ] `vitest --coverage` ≥ 75%
