# TASK-022 — Tela de Escala: Tabela por Squad × Data e Exportação CSV

**Domínio:** FRONTEND  
**Status:** WAITING  
**Prioridade:** P1 (alta — a tela de escala é a funcionalidade central do produto)  
**Depende de:** TASK-019 (event_squads config — sem isso generate_schedule falha), TASK-021 (toast)  
**Estimativa:** M (2–6h)

---

## Descrição

A tela de escala atual exibe os dados agrupados por squad em cards separados. A spec (§8, wireframe "Gerar Escala") define uma **tabela cruzada** Data × Squad com os nomes dos membros em cada célula. Além disso, faltam os botões de **Exportar CSV** e **Copiar** especificados.

---

## Critérios de Aceite

### Visualização — Tabela Cruzada

- [ ] Após gerar escala, exibir tabela no formato:

  | Data | Câmera | Transmissão | Áudio | ... |
  |---|---|---|---|---|
  | 08/03 | João · Ana | Pedro | Maria · Luiz | |
  | 15/03 | Carlos | João | Ana · Pedro | |

  (uma linha por data de evento, uma coluna por squad configurado)

- [ ] Cabeçalho de colunas fixo com nome dos squads
- [ ] Membros de cada célula separados por ` · ` (ponto mediano)
- [ ] Células vazias mostram `—` em `--text-muted`
- [ ] Tabela com scroll horizontal se houver muitos squads

**Nota:** A API atual retorna `ScheduleView` com uma lista plana de `entries` (cada entry tem `squad_id`, `squad_name`, `member_name`). O pivot deve ser feito no frontend.

Função de pivot a implementar em `src/lib/utils/index.ts`:
```typescript
export interface SchedulePivot {
  eventDate: string;       // ex: "2026-03-08"
  squads: Record<string, string[]>; // squad_name → [member_names]
}

export function pivotSchedule(view: ScheduleView): {
  columns: string[];        // nomes dos squads (ordem estável)
  rows: SchedulePivot[];    // uma por data
}
```

Como `ScheduleView` atual é para um único evento/data, adaptar para exibir a tabela mesmo com uma única linha (preparado para múltiplas datas futuras).

### Exportar CSV

- [ ] Botão "📤 Exportar CSV" disponível quando há escala gerada
- [ ] Gera arquivo `escala-{event_name}-{date}.csv` com o formato:

  ```
  Data,Câmera,Transmissão,Áudio
  08/03/2026,"João, Ana","Pedro","Maria, Luiz"
  ```

- [ ] Download via:
  ```typescript
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
  ```
  (não requer `tauri-plugin-fs` para CSV simples)

### Copiar para Área de Transferência

- [ ] Botão "📋 Copiar" gera texto formatado e chama `navigator.clipboard.writeText()`
  - Formato: texto tabulado legível para colar no WhatsApp/planilha
  ```
  Escala — Culto Domingo (08/03/2026)
  Câmera: João, Ana
  Transmissão: Pedro
  Áudio: Maria, Luiz
  ```
- [ ] Feedback via `toast.success('Copiado!')` após copiar

### Estado de Loading e Erros

- [ ] Botão "⚡ Gerar Escala" mostra spinner/texto "Gerando..." durante operação
- [ ] Erro de geração (ex: "Event has no squads configured") exibido via `toast.error(mensagem)`
- [ ] EmptyState quando nenhum evento selecionado: ícone `ClipboardList` + "Selecione um evento para ver ou gerar a escala."

### Wireframe de Referência (spec §8)

```
┌─ Escala ──────────────────────────────────────────────────────┐
│  Evento: [Culto Domingo — 08/03/2026  ▼]                      │
│  [⚡ Gerar Escala]  [Limpar]                                   │
│                                                                │
│ ┌──────────┬──────────────┬───────────┬──────────────────┐    │
│ │ Data     │ Câmera       │ Áudio     │ Transmissão      │    │
│ ├──────────┼──────────────┼───────────┼──────────────────┤    │
│ │ 08/03    │ João · Ana   │ Pedro     │ Maria · Luiz     │    │
│ └──────────┴──────────────┴───────────┴──────────────────┘    │
│                                                                │
│  [📋 Copiar]  [📤 Exportar CSV]                               │
└────────────────────────────────────────────────────────────── ┘
```

### Testes Vitest

- [ ] `pivotSchedule(view)` com entradas de 2 squads e 2 membros → 2 colunas, 1 linha, células corretas
- [ ] `pivotSchedule(view)` com entries vazia → `columns: [], rows: []`
- [ ] `generateCsv(pivot)` → string CSV bem formada (sem injeção via nomes com vírgulas)
- [ ] `generateCopyText(pivot, eventName)` → texto legível correto

---

## Notas Técnicas

- O modelo `ScheduleView` atual (retornado pelo backend) é para um único evento com uma única data. O pivot terá sempre uma linha, mas o componente deve ser escrito de forma que suporte múltiplas linhas no futuro (quando eventos recorrentes forem implementados).
- Para exportação PDF (mencionada na spec mas não obrigatória nessa task), deixar o botão desabilitado com `title="Em breve"` para não criar dívida de UX.
- Sanitizar nomes de membros no CSV: envolver em aspas duplas para lidar com vírgulas nos nomes.
- A função `pivotSchedule` deve ser testável sem Tauri — implementar como função pura em `utils/`.
