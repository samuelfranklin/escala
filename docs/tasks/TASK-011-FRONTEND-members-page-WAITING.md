# TASK-011 — Página de Membros

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1  
**Depende de:** TASK-008 (design system), TASK-009 (shell), TASK-010 (API layer), TASK-002 (backend members)  
**Estimativa:** L

---

## Descrição

Implementar a página completa de gerenciamento de membros: lista paginada e buscável com painel de detalhes lateral, modal de cadastro/edição, confirmação de exclusão, e feedback visual de loading e erro. Deve seguir o wireframe de "painel duplo" definido na spec §8.

---

## Wireframe de Referência (spec §8)

```
┌─ Membros ─────────────────────────── [🔍 Buscar] [+ Membro] ─┐
│ ┌─────────────────────────────────┐ ┌───────────────────────┐ │
│ │ Nome          Patente   Times   │ │ João Silva            │ │
│ │ ─────────────────────────────  │ │ ● Leader              │ │
│ │ ► João Silva  👑 Líder   2      │ │                       │ │
│ │   Ana Lima    🎓 Trainer  1     │ │ 📞 (11) 99999-9999    │ │
│ │   Pedro Costa ✓ Membro  3      │ │ ✉  joao@email.com     │ │
│ │   ...                          │ │ 📷 @joaosilva         │ │
│ │                                │ │                       │ │
│ │ [< Anterior]  Página 1/3  [>]  │ │ Times: [Câmera] [Áudio]│ │
│ └─────────────────────────────── ┘ │ [✏ Editar] [🗑 Remover]│ │
│                                    └───────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

---

## Escopo

### 1. Store de Membros — `src/lib/stores/members.ts`

```typescript
import { writable, derived } from 'svelte/store';
import { membersApi } from '$lib/api/members';
import { toastStore } from '$lib/components/ui';
import type { Member, CreateMemberDto, UpdateMemberDto } from '$lib/types';

interface MembersState {
  items:   Member[];
  loading: boolean;
  error:   string | null;
}

function createMembersStore() {
  const { subscribe, update, set } = writable<MembersState>({
    items:   [],
    loading: false,
    error:   null,
  });

  return {
    subscribe,

    load: async () => {
      update((s) => ({ ...s, loading: true, error: null }));
      const result = await membersApi.getAll();
      if (result.ok) {
        update((s) => ({ ...s, items: result.data, loading: false }));
      } else {
        update((s) => ({ ...s, error: result.error.message, loading: false }));
        toastStore.error(result.error.message);
      }
    },

    create: async (dto: CreateMemberDto): Promise<Member | null> => {
      const result = await membersApi.create(dto);
      if (result.ok) {
        update((s) => ({ ...s, items: [...s.items, result.data] }));
        toastStore.success('Membro criado com sucesso');
        return result.data;
      }
      toastStore.error(result.error.message);
      return null;
    },

    update: async (id: string, dto: UpdateMemberDto): Promise<Member | null> => {
      const result = await membersApi.update(id, dto);
      if (result.ok) {
        update((s) => ({
          ...s,
          items: s.items.map((m) => (m.id === id ? result.data : m)),
        }));
        toastStore.success('Membro atualizado');
        return result.data;
      }
      toastStore.error(result.error.message);
      return null;
    },

    delete: async (id: string): Promise<boolean> => {
      const result = await membersApi.delete(id);
      if (result.ok) {
        update((s) => ({ ...s, items: s.items.filter((m) => m.id !== id) }));
        toastStore.success('Membro removido');
        return true;
      }
      toastStore.error(result.error.message);
      return false;
    },
  };
}

export const membersStore = createMembersStore();
```

---

### 2. Componentes da Página

#### `src/routes/members/+page.svelte`

**Responsabilidades:**
- Chamar `membersStore.load()` no `onMount`
- Gerenciar estado local: `searchQuery`, `currentPage`, `selectedMemberId`, `showCreateModal`, `showEditModal`, `memberToDelete`
- Layout de painel duplo (lista + detalhes) com CSS Grid

**Estrutura:**
```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { membersStore } from '$lib/stores/members';
  import MemberList    from './MemberList.svelte';
  import MemberDetail  from './MemberDetail.svelte';
  import MemberModal   from './MemberModal.svelte';
  import DeleteConfirm from '$lib/components/ui/ConfirmDialog.svelte';
  // ...

  let searchQuery     = $state('');
  let currentPage     = $state(1);
  let selectedId      = $state<string | null>(null);
  let showModal       = $state(false);
  let editingMember   = $state<Member | null>(null);
  let memberToDelete  = $state<Member | null>(null);

  const PAGE_SIZE = 20;

  const filtered = $derived(
    $membersStore.items.filter((m) =>
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.email?.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  const paginated = $derived(
    filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
  );

  const totalPages = $derived(Math.ceil(filtered.length / PAGE_SIZE));
  const selected   = $derived($membersStore.items.find((m) => m.id === selectedId) ?? null);

  onMount(() => membersStore.load());
</script>
```

---

#### `MemberList.svelte`

| Prop | Tipo |
|---|---|
| `members` | `Member[]` |
| `selectedId` | `string \| null` |
| `loading` | `boolean` |
| `onselect` | `(id: string) => void` |

- Tabela com colunas: **Nome**, **Patente** (`<Badge>`), **Times** (count), **Ativo**
- Linha selecionada: `aria-selected`, estilo de destaque
- Estado vazio: `<EmptyState icon={Users} title="Nenhum membro encontrado" />`
- Estado loading: skeleton de 5 linhas (animação shimmer via CSS)
- Ordenação por coluna (Nome, Patente) com indicador visual ↑↓

#### `MemberDetail.svelte`

| Prop | Tipo |
|---|---|
| `member` | `Member \| null` |
| `onedit` | `(member: Member) => void` |
| `ondelete` | `(member: Member) => void` |

- Quando `member === null`: `<EmptyState>` "Selecione um membro"
- Exibir: nome, `<Badge>` de patente, email, telefone, instagram
- Times do membro: chips com nomes dos squads (buscar via `squadsApi.getAll()` + filter)
- Botões Editar e Remover no rodapé do painel
- Exibir data de cadastro formatada

#### `MemberModal.svelte`

| Prop | Tipo |
|---|---|
| `open` | `boolean` |
| `member` | `Member \| null` (null = criar, não-null = editar) |
| `onclose` | `() => void` |
| `onsaved` | `(member: Member) => void` |

Campos do formulário:
| Campo | Componente | Validação |
|---|---|---|
| Nome* | `<Input>` | Obrigatório, min 2 chars |
| Email | `<Input type="email">` | Formato de email se preenchido |
| Telefone | `<Input>` | Formato `(XX) XXXXX-XXXX` se preenchido |
| Instagram | `<Input>` | Remove `@` automático |
| Patente | `<Select>` | Opções: leader/trainer/member/recruit |
| Ativo | `<input type="checkbox">` | Apenas no modo edição |

- Validação inline (sem submit): mostrar erros em cada campo
- Botão "Salvar" com `loading=true` durante `create`/`update`
- Título dinâmico: "Novo Membro" ou "Editar — {nome}"
- Fechar limpa o formulário

#### `ConfirmDialog.svelte` (genérico, em `src/lib/components/ui/`)

| Prop | Tipo |
|---|---|
| `open` | `boolean` |
| `title` | `string` |
| `description` | `string` |
| `confirmLabel` | `string` |
| `variant` | `'danger' \| 'warning'` |
| `loading` | `boolean` |
| `onconfirm` | `() => void` |
| `oncancel` | `() => void` |

- Modal `size="sm"` com dois botões: cancelar (ghost) e confirmar (danger/warning)
- `aria-describedby` apontando para o texto de descrição

---

### 3. Paginação

**`Pagination.svelte`** (genérico em `src/lib/components/ui/`):
| Prop | Tipo |
|---|---|
| `currentPage` | `number` |
| `totalPages` | `number` |
| `onchange` | `(page: number) => void` |

- Botões Anterior / Próximo
- Exibir "Página X de Y" e "N resultados"
- Desabilitar botões nos limites
- Atalhos: `←`/`→` quando a tabela está focada

---

### 4. Busca com Debounce

```typescript
// Debounce de 300ms no input de busca
// Resetar para página 1 ao buscar
// Limpar seleção se o membro selecionado não estiver no filtro atual
```

---

## Critérios de Aceite

- [ ] Lista exibe todos os membros com nome, badge de patente, contagem de times e status ativo
- [ ] Busca filtra em tempo real (debounce 300ms) por nome e email
- [ ] Paginação funciona: 20 itens por página, botões anterior/próximo, indicador de página
- [ ] Clicar em um membro exibe seu detalhe no painel direito
- [ ] Painel de detalhe mostra nome, patente, contatos, times associados
- [ ] Botão "+ Membro" abre modal de criação; salvar adiciona à lista sem recarregar
- [ ] Botão "Editar" no detalhe abre modal com campos pré-preenchidos; salvar atualiza a lista
- [ ] Botão "Remover" exibe `ConfirmDialog`; confirmar remove da lista com toast de sucesso
- [ ] Estado de loading (skeleton) exibido enquanto `membersStore.load()` pendente
- [ ] Erros da API exibidos via toast; formulário exibe erros de validação inline
- [ ] `EmptyState` exibido quando lista vazia ou busca sem resultados
- [ ] Testes de componente (Vitest) com cobertura ≥ 75%
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Acessível: tabela com `role="grid"`, `aria-selected`, foco gerenciado ao abrir/fechar modal

---

## Notas Técnicas

- **Svelte 5 runes**: estado local com `$state()`, derivados com `$derived()`, efeitos com `$effect()`
- **Painel duplo**: usar `display: grid; grid-template-columns: 1fr 320px` no layout da página
- **Skeleton loading**: implementar com CSS `@keyframes shimmer` e divs com largura variada — não usar biblioteca
- **Formatação de telefone**: função pura em `src/lib/utils/format.ts` — reutilizável em outras páginas
- **Times no detalhe**: buscar a lista de squads do store (quando TASK-012 existir) ou via `squadsApi.getAll()` — cachear para não re-fetch a cada seleção
- **Otimismo**: não implementar updates otimistas nesta task — aguardar confirmação do backend antes de atualizar a lista

---

## Arquivos a Criar

```
src/
├── lib/
│   ├── stores/
│   │   └── members.ts
│   ├── utils/
│   │   └── format.ts               ← formatPhone, formatDate, formatInstagram
│   └── components/
│       └── ui/
│           ├── ConfirmDialog.svelte
│           ├── ConfirmDialog.test.ts
│           ├── Pagination.svelte
│           └── Pagination.test.ts
└── routes/
    └── members/
        ├── +page.svelte
        ├── +page.test.ts
        ├── MemberList.svelte
        ├── MemberList.test.ts
        ├── MemberDetail.svelte
        ├── MemberDetail.test.ts
        ├── MemberModal.svelte
        └── MemberModal.test.ts
```

---

## Progresso

- [ ] `stores/members.ts` — load, create, update, delete
- [ ] `utils/format.ts` — formatPhone, formatDate, formatInstagram
- [ ] `ConfirmDialog.svelte` + testes
- [ ] `Pagination.svelte` + testes
- [ ] `MemberList.svelte` + testes (inclui skeleton + empty state)
- [ ] `MemberDetail.svelte` + testes
- [ ] `MemberModal.svelte` + validação + testes
- [ ] `+page.svelte` — integração completa + testes
- [ ] `tsc --noEmit` sem erros
- [ ] `vitest --coverage` ≥ 75%
