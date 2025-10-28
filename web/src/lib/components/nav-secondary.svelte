<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import type { ComponentProps } from 'svelte';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';
	import { toggleMode } from 'mode-watcher';

	let {
		ref = $bindable(null),
		items,
		...restProps
	}: {
		items: {
			title: string;
			url: string;
			// This should be `Component` after @lucide/svelte updates types
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			icon: any;
		}[];
	} & ComponentProps<typeof Sidebar.Group> = $props();
</script>

<Sidebar.Group {...restProps} bind:ref>
	<Sidebar.GroupContent>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="sm">
					{#snippet child({ props })}
						<div onclick={() => toggleMode()} {...props}>
							<Sun class="dark:hidden " />
							<span class="dark:hidden">Switch to dark mode</span>
							<Moon class="hidden dark:inline" />
							<span class="hidden dark:inline">Switch to light mode</span>
						</div>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>

			{#each items as item (item.title)}
				<Sidebar.MenuItem>
					<Sidebar.MenuButton size="sm">
						{#snippet child({ props })}
							<!-- eslint-disable svelte/no-navigation-without-resolve -->
							<a href={item.url} {...props}>
								<item.icon />
								<span>{item.title}</span>
							</a>
							<!-- eslint-enable svelte/no-navigation-without-resolve -->
						{/snippet}
					</Sidebar.MenuButton>
				</Sidebar.MenuItem>
			{/each}
		</Sidebar.Menu>
	</Sidebar.GroupContent>
</Sidebar.Group>
