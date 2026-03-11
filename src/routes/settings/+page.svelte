<script lang="ts">
  import { onMount } from 'svelte';
  import { slide } from 'svelte/transition';
  import { settingsConfig, settingsLoading, settings } from '$lib/stores/settings';
  import { toast } from '$lib/stores/toast';
  import type { UpdateScheduleConfigDto } from '$lib/types';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Switch } from '$lib/components/ui/switch/index.js';
  import * as Card from '$lib/components/ui/card/index.js';
  import { Skeleton } from '$lib/components/ui/skeleton/index.js';

  let saving = $state(false);

  let applyMonthlyLimit = $state(true);
  let maxOccurrences = $state(2);
  let propagateCouples = $state(true);
  let applyHistoryScoring = $state(true);

  // config reativo via store
  let storeConfig = $state($settingsConfig);
  let storeLoading = $state($settingsLoading);

  // Atualiza estado local quando a store muda
  $effect(() => {
    const cfg = $settingsConfig;
    storeConfig = cfg;
    if (cfg) {
      applyMonthlyLimit   = cfg.apply_monthly_limit;
      maxOccurrences      = cfg.max_occurrences_per_month;
      propagateCouples    = cfg.propagate_couples;
      applyHistoryScoring = cfg.apply_history_scoring;
    }
  });

  $effect(() => {
    storeLoading = $settingsLoading;
  });

  const isDirty = $derived(
    storeConfig !== null && (
      applyMonthlyLimit   !== storeConfig.apply_monthly_limit   ||
      maxOccurrences      !== storeConfig.max_occurrences_per_month ||
      propagateCouples    !== storeConfig.propagate_couples      ||
      applyHistoryScoring !== storeConfig.apply_history_scoring
    )
  );

  onMount(() => settings.load().catch((e) => toast.error(e?.message || 'Erro ao carregar configurações')));

  async function handleSave() {
    saving = true;
    try {
      const dto: UpdateScheduleConfigDto = {
        apply_monthly_limit: applyMonthlyLimit,
        max_occurrences_per_month: maxOccurrences,
        propagate_couples: propagateCouples,
        apply_history_scoring: applyHistoryScoring,
      };
      await settings.save(dto);
      toast.success('Configurações salvas!');
    } catch (e: any) {
      toast.error(e.message || 'Erro ao salvar configurações');
    } finally {
      saving = false;
    }
  }
</script>

<div class="p-6 max-w-xl space-y-6">

  <!-- Cabeçalho -->
  <div>
    <h1 class="text-2xl font-semibold">Configurações</h1>
    <p class="text-muted-foreground text-sm mt-1">Regras de geração de escala</p>
  </div>

  {#if storeLoading && !storeConfig}
    <!-- Skeleton loading -->
    <div class="space-y-4">
      {#each [0, 1, 2] as _}
        <div class="border rounded-xl p-6 space-y-3">
          <div class="flex items-center justify-between">
            <Skeleton class="h-5 w-48" />
            <Skeleton class="h-5 w-8 rounded-full" />
          </div>
          <Skeleton class="h-4 w-full" />
          <Skeleton class="h-4 w-3/4" />
        </div>
      {/each}
    </div>
  {:else}
    <!-- Banner de alterações não salvas -->
    {#if isDirty}
      <div transition:slide={{ duration: 200 }} class="flex items-center gap-2 rounded-lg border border-yellow-400/60 bg-yellow-400/10 px-4 py-3 text-sm text-yellow-700 dark:text-yellow-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="size-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
        Você tem alterações não salvas
      </div>
    {/if}

    <div class="space-y-4">

      <!-- Card: Limite mensal -->
      <Card.Root>
        <Card.Header>
          <div class="flex items-center justify-between gap-4">
            <Label for="apply-monthly-limit" class="text-base font-medium cursor-pointer leading-snug">
              Limite de ocorrências por membro/mês
            </Label>
            <Switch id="apply-monthly-limit" bind:checked={applyMonthlyLimit} />
          </div>
        </Card.Header>
        <Card.Content class="space-y-4">
          <p class="text-muted-foreground text-sm">
            Impede que o mesmo membro seja escalado mais do que o número máximo de vezes no mesmo mês.
          </p>
          {#if applyMonthlyLimit}
            <div transition:slide={{ duration: 200 }} class="flex items-center gap-3 pt-1">
              <Label for="max-occurrences" class="text-sm whitespace-nowrap text-foreground">
                Máximo de ocorrências:
              </Label>
              <Input
                id="max-occurrences"
                type="number"
                min={1}
                max={10}
                class="w-20"
                bind:value={maxOccurrences}
              />
              <span class="text-sm text-muted-foreground">vezes/mês</span>
            </div>
          {/if}
        </Card.Content>
      </Card.Root>

      <!-- Card: Restrição de casais -->
      <Card.Root>
        <Card.Header>
          <div class="flex items-center justify-between gap-4">
            <Label for="propagate-couples" class="text-base font-medium cursor-pointer leading-snug">
              Restrição de casais
            </Label>
            <Switch id="propagate-couples" bind:checked={propagateCouples} />
          </div>
        </Card.Header>
        <Card.Content>
          <p class="text-muted-foreground text-sm">
            Membros cadastrados como casal não são escalados juntos no mesmo evento.
          </p>
        </Card.Content>
      </Card.Root>

      <!-- Card: Pontuação histórica -->
      <Card.Root>
        <Card.Header>
          <div class="flex items-center justify-between gap-4">
            <Label for="apply-history-scoring" class="text-base font-medium cursor-pointer leading-snug">
              Pontuação histórica
            </Label>
            <Switch id="apply-history-scoring" bind:checked={applyHistoryScoring} />
          </div>
        </Card.Header>
        <Card.Content>
          <p class="text-muted-foreground text-sm">
            Penaliza membros escalados recentemente, distribuindo melhor a carga entre o time.
          </p>
        </Card.Content>
      </Card.Root>

    </div>

    <div class="pt-2">
      <Button onclick={handleSave} disabled={!isDirty || saving}>
        {saving ? 'Salvando...' : 'Salvar configurações'}
      </Button>
    </div>
  {/if}
</div>
