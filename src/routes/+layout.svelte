<script lang="ts">
  import '../app.css';
  import { addCollection } from '@iconify/svelte/dist/Icon.svelte';
  import lucideIcons from '@iconify-json/lucide/icons.json';
  import * as Sidebar from '$lib/components/ui/sidebar/index.js';
  import { Toaster } from '$lib/components/ui/sonner/index.js';
  import AppSidebar from '$lib/components/AppSidebar.svelte';
  import { ModeWatcher } from 'mode-watcher';

  addCollection(lucideIcons);

  let { children } = $props();
</script>

<ModeWatcher />
<Sidebar.Provider>
  <AppSidebar />
  <Sidebar.Inset>
    <header class="flex h-12 shrink-0 items-center gap-2 border-b px-4">
      <Sidebar.Trigger class="-ml-1" />
    </header>
    <main class="flex-1 overflow-y-auto p-8" id="main">
      {@render children?.()}
    </main>
  </Sidebar.Inset>
</Sidebar.Provider>
<Toaster />
