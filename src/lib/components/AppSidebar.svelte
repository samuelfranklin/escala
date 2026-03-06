<script lang="ts">
	import { page } from '$app/stores';
	import Icon from '@iconify/svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';

	const navItems = [
		{ href: '/dashboard',    label: 'Dashboard',       icon: 'lucide:layout-dashboard' },
		{ href: '/members',      label: 'Membros',          icon: 'lucide:users' },
		{ href: '/squads',       label: 'Times',            icon: 'lucide:layers' },
		{ href: '/events',       label: 'Eventos',          icon: 'lucide:calendar' },
		{ href: '/schedule',     label: 'Escala',           icon: 'lucide:clipboard-list' },
		{ href: '/availability', label: 'Disponibilidade',  icon: 'lucide:calendar-check' },
		{ href: '/couples',      label: 'Casais',           icon: 'lucide:heart' },
	];
</script>

<Sidebar.Root collapsible="icon">
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg" class="pointer-events-none">
					<div class="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground shrink-0">
						<Icon icon="lucide:clapperboard" class="size-4" />
					</div>
					<div class="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
						<span class="font-heading truncate font-semibold">Escala Mídia</span>
						<span class="truncate text-xs text-muted-foreground">Gestão de escala</span>
					</div>
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>

	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each navItems as item (item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton
								isActive={$page.url.pathname.startsWith(item.href)}
								tooltip={item.label}
							>
								{#snippet child({ props }: { props: Record<string, unknown> })}
									<a href={item.href} {...props}>
										<Icon icon={item.icon} />
										<span>{item.label}</span>
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Content>

	<Sidebar.Rail />
</Sidebar.Root>
