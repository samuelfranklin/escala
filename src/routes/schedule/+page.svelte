<script lang="ts">
  import { onMount } from 'svelte';
  import { getMonthSchedule, generateMonthSchedule, clearMonthSchedule } from '$lib/api/schedule';
  import { toast } from '$lib/stores/toast';
  import type { MonthScheduleView, OccurrenceSchedule } from '$lib/types';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import Icon from '@iconify/svelte';

  // Mês atual como padrão (formato YYYY-MM)
  const today = new Date();
  const defaultMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;

  let selectedMonth = $state(defaultMonth);
  let monthSchedule = $state<MonthScheduleView | null>(null);
  let loading = $state(false);
  let generating = $state(false);

  onMount(() => loadMonth());

  async function loadMonth() {
    if (!selectedMonth) return;
    loading = true;
    try { monthSchedule = await getMonthSchedule(selectedMonth); }
    catch (e: any) { toast.error(e.message || 'Erro ao carregar escala'); }
    finally { loading = false; }
  }

  async function handleGenerate() {
    if (!selectedMonth) return;
    generating = true;
    try {
      monthSchedule = await generateMonthSchedule(selectedMonth);
      toast.success('Escala do mês gerada!');
    } catch (e: any) {
      toast.error(e.message || 'Erro ao gerar escala');
      // Sincroniza o estado com o DB: com a correção two-phase, a escala anterior
      // foi preservada; sem ela, mostra o estado real (evita dados fantasma no frontend).
      await loadMonth();
    } finally {
      generating = false;
    }
  }

  async function handleClear() {
    if (!selectedMonth || !confirm('Limpar escala do mês inteiro?')) return;
    await clearMonthSchedule(selectedMonth);
    monthSchedule = { month: selectedMonth, occurrences: [] };
    toast.success('Escala limpa.');
  }

  // Agrupa ocorrências por evento (mantendo ordem cronológica das datas)
  const groupedByEvent = $derived(() => {
    if (!monthSchedule || !monthSchedule.occurrences.length) return [];
    const map = new Map<string, { name: string; occurrences: OccurrenceSchedule[] }>();
    for (const occ of monthSchedule.occurrences) {
      if (!map.has(occ.event_id)) {
        map.set(occ.event_id, { name: occ.event_name, occurrences: [] });
      }
      map.get(occ.event_id)!.occurrences.push(occ);
    }
    return [...map.values()];
  });

  /** Para um grupo de ocorrências de um evento, constrói a tabela:
   *  cells[squad_name][occurrence_date] = memberNames[] */
  function buildEventPivot(occurrences: OccurrenceSchedule[]) {
    const dates = occurrences.map(o => o.occurrence_date);
    const squadsSet = new Set<string>();
    for (const occ of occurrences) {
      for (const e of occ.entries) squadsSet.add(e.squad_name);
    }
    const squads = [...squadsSet].sort();
    const cells: Record<string, Record<string, string[]>> = {};
    for (const sq of squads) {
      cells[sq] = {};
      for (const occ of occurrences) {
        cells[sq][occ.occurrence_date] = occ.entries
          .filter(e => e.squad_name === sq)
          .map(e => e.member_name);
      }
    }
    return { dates, squads, cells };
  }

  function fmtDate(iso: string) {
    const [, m, d] = iso.split('-');
    return `${d}/${m}`;
  }

  function fmtMonthTitle(ym: string) {
    const [y, m] = ym.split('-');
    const names = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                   'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
    return `${names[parseInt(m) - 1]} ${y}`;
  }

  const hasSchedule = $derived(() =>
    !!monthSchedule && monthSchedule.occurrences.length > 0
  );

  function handleExportCsv() {
    if (!monthSchedule) return;
    const lines: string[] = [`"Evento","Data","Time","Membros"`];
    for (const occ of monthSchedule.occurrences) {
      const squadsInOcc: Record<string, string[]> = {};
      for (const e of occ.entries) {
        (squadsInOcc[e.squad_name] ??= []).push(e.member_name);
      }
      for (const [sq, members] of Object.entries(squadsInOcc)) {
        const escape = (s: string) => `"${s.replace(/"/g, '""')}"`;
        lines.push([escape(occ.event_name), escape(fmtDate(occ.occurrence_date)), escape(sq), escape(members.join(', '))].join(','));
      }
    }
    const csv = lines.join('\r\n');
    const name = fmtMonthTitle(selectedMonth).replace(' ', '-').toLowerCase();
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `escala-${name}.csv`; a.click();
    URL.revokeObjectURL(url);
  }

  async function handleCopy() {
    if (!monthSchedule) return;
    const lines: string[] = [`📅 Escala — ${fmtMonthTitle(selectedMonth)}`, ''];
    for (const group of groupedByEvent()) {
      lines.push(`=== ${group.name} ===`);
      for (const occ of group.occurrences) {
        const d = new Date(occ.occurrence_date + 'T12:00:00');
        const weekday = d.toLocaleDateString('pt-BR', { weekday: 'long' });
        lines.push(`  ${fmtDate(occ.occurrence_date)} (${weekday})`);
        const squadsInOcc: Record<string, string[]> = {};
        for (const e of occ.entries) (squadsInOcc[e.squad_name] ??= []).push(e.member_name);
        for (const [sq, members] of Object.entries(squadsInOcc)) {
          lines.push(`    ${sq}: ${members.join(', ')}`);
        }
      }
      lines.push('');
    }
    await navigator.clipboard.writeText(lines.join('\n'));
    toast.success('Copiado!');
  }
</script>

<div data-testid="schedule-page">
  <h1 class="text-2xl font-heading font-bold mb-6">Escala</h1>

  <!-- Controles -->
  <div class="flex gap-3 items-end flex-wrap mb-6">
    <div class="flex flex-col gap-1.5">
      <Label for="month-select">Mês</Label>
      <Input id="month-select" class="min-w-[160px]" type="month" bind:value={selectedMonth}
        onchange={loadMonth} />
    </div>
    <Button data-testid="btn-generate-schedule"
      onclick={handleGenerate} disabled={!selectedMonth || generating}>
      <Icon icon="lucide:zap" class="size-4 mr-1.5" />
      {generating ? 'Gerando...' : 'Gerar Escala do Mês'}
    </Button>
    {#if hasSchedule()}
      <Button variant="outline" onclick={handleClear}>
        <Icon icon="lucide:trash-2" class="size-4 mr-1.5" /> Limpar Mês
      </Button>
    {/if}
  </div>

  {#if loading}
    <div class="flex flex-col gap-4">
      {#each [1,2] as _}
        <div class="h-32 rounded-xl bg-muted animate-pulse"></div>
      {/each}
    </div>

  {:else if !hasSchedule()}
    <div class="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
      <Icon icon="lucide:clipboard-list" class="size-12 opacity-30" />
      <p class="text-sm">
        Nenhuma escala para {fmtMonthTitle(selectedMonth)}. Clique em "Gerar Escala do Mês".
      </p>
    </div>

  {:else}
    <h2 class="text-xl font-heading font-bold mb-6">
      {fmtMonthTitle(selectedMonth)}
      <span class="text-sm font-normal text-muted-foreground ml-3">
        {monthSchedule!.occurrences.length} {monthSchedule!.occurrences.length === 1 ? 'ocorrência' : 'ocorrências'}
      </span>
    </h2>

    {#each groupedByEvent() as group}
      {@const pivot = buildEventPivot(group.occurrences)}
      <div class="rounded-xl border bg-card p-4 mb-6 shadow-sm">
        <h3 class="text-base font-heading font-bold mb-4">{group.name}</h3>
        <div class="overflow-x-auto">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th class="px-3 py-2 text-left bg-muted/60 border border-border font-semibold whitespace-nowrap min-w-[120px]">Time</th>
                {#each pivot.dates as date}
                  <th class="px-3 py-2 text-left bg-muted/60 border border-border font-semibold whitespace-nowrap">
                    {fmtDate(date)}
                  </th>
                {/each}
              </tr>
            </thead>
            <tbody>
              {#each pivot.squads as squad}
                <tr>
                  <td class="px-3 py-2 border border-border font-semibold bg-muted/30 whitespace-nowrap">{squad}</td>
                  {#each pivot.dates as date}
                    <td class="px-3 py-2 border border-border">
                      {#if pivot.cells[squad][date]?.length}
                        {pivot.cells[squad][date].join(' · ')}
                      {:else}
                        <span class="text-muted-foreground">—</span>
                      {/if}
                    </td>
                  {/each}
                </tr>
              {/each}
              {#if pivot.squads.length === 0}
                <tr>
                  <td colspan={pivot.dates.length + 1} class="px-3 py-3 border border-border text-muted-foreground text-center">
                    Nenhuma alocação registrada
                  </td>
                </tr>
              {/if}
            </tbody>
          </table>
        </div>
      </div>
    {/each}

    <div class="flex gap-3 flex-wrap">
      <Button variant="outline" data-testid="btn-copy-schedule" onclick={handleCopy}>
        <Icon icon="lucide:copy" class="size-4 mr-1.5" /> Copiar Mês
      </Button>
      <Button variant="outline" data-testid="btn-export-csv" onclick={handleExportCsv}>
        <Icon icon="lucide:download" class="size-4 mr-1.5" /> Exportar CSV
      </Button>
    </div>
  {/if}
</div>

