<script lang="ts" module>
	import {
		Bell,
		BookOpen,
		CircleDollarSign,
		Clapperboard,
		Home,
		Info,
		LifeBuoy,
		Music2,
		Settings,
		TvIcon
	} from 'lucide-svelte';
	import { resolve } from '$app/paths';

	import { PUBLIC_VERSION } from '$env/static/public';

	const data = {
		navMain: [
			{
				title: 'Dashboard',
				url: resolve('/dashboard', {}),
				icon: Home,
				isActive: true
			},
			{
				title: 'TV',
				url: resolve('/dashboard/tv', {}),
				icon: TvIcon,
				isActive: true,
				items: [
					{
						title: 'Add a show',
						url: resolve('/dashboard/tv/add-show', {})
					},
					{
						title: 'Torrents',
						url: resolve('/dashboard/tv/torrents', {})
					},
					{
						title: 'Requests',
						url: resolve('/dashboard/tv/requests', {})
					}
				]
			},
			{
				title: 'Movies',
				url: resolve('/dashboard/movies', {}),
				icon: Clapperboard,
				isActive: true,
				items: [
					{
						title: 'Add a movie',
						url: resolve('/dashboard/movies/add-movie', {})
					},
					{
						title: 'Torrents',
						url: resolve('/dashboard/movies/torrents', {})
					},
					{
						title: 'Requests',
						url: resolve('/dashboard/movies/requests', {})
					}
				]
			},
			{
				title: 'Music',
				url: resolve('/dashboard/music', {}),
				icon: Music2,
				isActive: true,
				items: [
					{
						title: 'Add an artist',
						url: resolve('/dashboard/music/add-artist', {})
					},
					{
						title: 'Torrents',
						url: resolve('/dashboard/music/torrents', {})
					},
					{
						title: 'Requests',
						url: resolve('/dashboard/music/requests', {})
					}
				]
			},
			{
				title: 'Books',
				url: resolve('/dashboard/books', {}),
				icon: BookOpen,
				isActive: true,
				items: [
					{
						title: 'Add an author',
						url: resolve('/dashboard/books/add-author', {})
					},
					{
						title: 'Torrents',
						url: resolve('/dashboard/books/torrents', {})
					},
					{
						title: 'Requests',
						url: resolve('/dashboard/books/requests', {})
					}
				]
			}
		],
		navSecondary: [
			{
				title: 'Notifications',
				url: resolve('/dashboard/notifications', {}),
				icon: Bell
			},
			{
				title: 'Settings',
				url: resolve('/dashboard/settings', {}),
				icon: Settings
			},
			{
				title: 'Support',
				url: 'https://github.com/maxdorninger/MediaManager/issues',
				icon: LifeBuoy
			},
			{
				title: 'Donate',
				url: 'https://github.com/sponsors/maxdorninger',
				icon: CircleDollarSign
			},
			{
				title: 'About',
				url: resolve('/dashboard/about', {}),
				icon: Info
			}
		]
	};
</script>

<script lang="ts">
	import NavMain from '$lib/components/nav/nav-main.svelte';
	import NavSecondary from '$lib/components/nav/nav-secondary.svelte';
	import NavUser from '$lib/components/nav/nav-user.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar';
	import type { ComponentProps } from 'svelte';
	import logo from '$lib/images/logo.svg';

	let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root {...restProps} bind:ref variant="inset">
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					{#snippet child({ props })}
						<a href={resolve('/dashboard', {})} {...props}>
							<img class="size-12" src={logo} alt="Media Manager Logo" />
							<div class="grid flex-1 text-left text-sm leading-tight">
								<span class="truncate font-semibold">Media Manager</span>
								<span class="truncate text-xs">{PUBLIC_VERSION}</span>
							</div>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>
	<Sidebar.Content>
		<NavMain items={data.navMain} />
		<!--  <NavProjects projects={data.projects}/> -->
		<NavSecondary class="mt-auto" items={data.navSecondary} />
	</Sidebar.Content>
	<Sidebar.Footer>
		<NavUser />
	</Sidebar.Footer>
</Sidebar.Root>
