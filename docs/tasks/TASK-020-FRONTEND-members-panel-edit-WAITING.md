# TASK-020 — Tela de Membros: Painel Duplo, Edição e Rank Badge

**Domínio:** FRONTEND  
**Status:** DONE  
**Prioridade:** P1 (alta — tela principal do app está incompleta)  
**Depende de:** TASK-011 (members page base), TASK-019 (não bloqueia, mas fazer depois)  
**Estimativa:** M (2–6h)

---

## Descrição

A tela de Membros atual é uma lista simples com botão "Remover". A spec (§8) define um **painel duplo**: lista à esquerda + painel de detalhes/edição à direita. Além disso, faltam:

- Editar membro (o backend `update_member` existe, mas a UI não usa)
- Máscara de telefone no formato `(11) 99999-9999`
- Rank badge com cor correspondente (conforme design tokens)
- Exibir instagram e telefone na lista/detalhe
- Membro inativo visualmente distinto

---

## Critérios de Aceite

### Layout Painel Duplo

- [ ] Tela dividida em duas colunas: lista (esquerda, ~360px) + detalhe (direita, flex-fill)
- [ ] Clicar em um membro na lista seleciona-o e abre o painel de detalhes
- [ ] Membro selecionado tem borda destacada com `--color-primary-500`
- [ ] Em telas estreitas (< 700px), o painel de detalhes substitui a lista (navegação de volta)

### Lista de Membros (coluna esquerda)

- [ ] Cada item exibe: Nome + RankBadge + indicador de times (contador)
- [ ] Busca filtra por nome em tempo real (já existe, manter)
- [ ] Membros inativos aparecem com opacidade 50% e badge "Inativo"
- [ ] EmptyState quando sem resultados: ícone `Users` + texto "Nenhum membro cadastrado." + botão "+ Novo Membro"

### Painel de Detalhes (coluna direita)

- [ ] Exibe todos os campos do membro: nome, email, telefone (formatado), instagram, rank, status ativo/inativo
- [ ] Botão "Editar" abre modo de edição inline no próprio painel (ou reutiliza o modal)
- [ ] Botão "Remover" com confirmação (já existe, mover para cá)
- [ ] Seção "Times" lista os squads do membro como badges clicáveis
- [ ] Se sem times: texto "Sem times associados"

### Modal de Criação / Formulário de Edição

- [ ] Campo Telefone com máscara `(##) #####-####` aplicada via input handler:
  ```typescript
  function maskPhone(raw: string): string {
    const digits = raw.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 2)  return `(${digits}`;
    if (digits.length <= 7)  return `(${digits.slice(0,2)}) ${digits.slice(2)}`;
    return `(${digits.slice(0,2)}) ${digits.slice(2,7)}-${digits.slice(7)}`;
  }
  ```
  - A máscara é **apenas visual** — o valor armazenado pode conter a formatação (aceito pelo backend como `TEXT`)
- [ ] Campo Instagram com prefixo `@` visual (placeholder `@usuario`)
- [ ] Select de Rank com opções em PT-BR: Recruta / Membro / Treinador / Líder
- [ ] Ao editar, o formulário é pré-populado com os dados atuais do membro
- [ ] Edição chama `updateMember(id, dto)` via API layer
- [ ] Feedback de sucesso/erro (usar toasts da TASK-021 se disponível, senão erro inline)

### RankBadge — Cores conforme design tokens

| Rank | Cor | Token |
|---|---|---|
| `leader` | Dourado | `--rank-leader: #fbbf24` |
| `trainer` | Roxo | `--rank-trainer: #818cf8` |
| `member` | Verde | `--rank-member: #4ade80` |
| `recruit` | Cinza | `--rank-recruit: #9ca3af` |

Texto PT-BR: `leader` → "Líder", `trainer` → "Treinador", `member` → "Membro", `recruit` → "Recruta"

Implementar como componente reutilizável `src/lib/components/ui/RankBadge.svelte`:
```svelte
<script lang="ts">
  const { rank } = $props<{ rank: 'leader'|'trainer'|'member'|'recruit' }>();
  const labels = { leader: 'Líder', trainer: 'Treinador', member: 'Membro', recruit: 'Recruta' };
  const colors = { leader: '#fbbf24', trainer: '#818cf8', member: '#4ade80', recruit: '#9ca3af' };
</script>
<span style="background:{colors[rank]}22;color:{colors[rank]};padding:2px 8px;border-radius:12px;font-size:var(--text-xs);font-weight:600">
  {labels[rank]}
</span>
```

### Wireframe de Referência (spec §8)

```
┌─ Membros ─────────────────────────── [🔍 Buscar] [+ Membro] ─┐
│ ┌─────────────────────────────────┐ ┌───────────────────────┐ │
│ │ ► João Silva  👑 Líder   2 times│ │ João Silva            │ │
│ │   Ana Lima    🎓 Treinador 1    │ │ [👑 Líder]  ● Ativo   │ │
│ │   Pedro Costa ✓ Membro   3      │ │                       │ │
│ │   Maria (inativa — 50% opacity) │ │ 📞 (11) 99999-9999    │ │
│ │                                 │ │ ✉  joao@email.com     │ │
│ │                                 │ │ 📷 @joaosilva         │ │
│ │                                 │ │                       │ │
│ │                                 │ │ Times:                │ │
│ │                                 │ │ [Câmera] [Áudio]      │ │
│ │                                 │ │                       │ │
│ │                                 │ │ [✏ Editar] [🗑 Remover]│ │
│ └─────────────────────────────────┘ └───────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Notas Técnicas

- Buscar times do membro no painel de detalhes via `getSquadMembers` — mas invertido: chamar um novo helper ou filtrar `squads` comparando com `memberId`. Verificar se `getMemberSquads(memberId)` já existe na API layer; se não, adicionar.
- A máscara de telefone não deve ser um package externo — implementar a função pura `maskPhone` em `src/lib/utils/index.ts` e testá-la com Vitest.
- `updateMember` já existe em `src/lib/api/members.ts` (`invoke<Member>('update_member', { id, dto })`), basta conectar na UI.
- Testes Vitest obrigatórios:
  - `maskPhone('')` → `''`
  - `maskPhone('11999999999')` → `'(11) 99999-9999'`
  - `maskPhone('119')` → `'(11) 9'`
