<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import type { RichMovieTorrent } from '$lib/types';
	import { getFullyQualifiedMediaName } from '$lib/utils';
	import * as Accordion from '$lib/components/ui/accordion/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import TorrentTable from '$lib/components/torrent-table.svelte';
	import { onMount } from 'svelte';
	import { env } from '$env/dynamic/public';
	import { toast } from 'svelte-sonner';
	import { base } from '$app/paths';

	const apiUrl = env.PUBLIC_API_URL;
	let torrents: RichMovieTorrent[] = [];
	onMount(async () => {
		const res = await fetch(apiUrl + '/movies/torrents', {
			method: 'GET',
			credentials: 'include'
		});
		if (!res.ok) {
			toast.error('Failed to fetch torrents');
			throw new Error(`Failed to fetch torrents: ${res.status} ${res.statusText}`);
		}
		torrents = await res.json();
		console.log('got torrents: ', torrents);
	});
</script>

<svelte:head>
	<title>Movie Torrents - MediaManager</title>
	<meta content="View and manage movie torrent downloads in MediaManager" name="description" />
</svelte:head>

<header class="flex h-16 shrink-0 items-center gap-2">
	<div class="flex items-center gap-2 px-4">
		<Sidebar.Trigger class="-ml-1" />
		<Separator class="mr-2 h-4" orientation="vertical" />
		<Breadcrumb.Root>
			<Breadcrumb.List>
				<Breadcrumb.Item class="hidden md:block">
					<Breadcrumb.Link href="{base}/dashboard">MediaManager</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href="{base}/dashboard">Home</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href="{base}/dashboard/movies">Movies</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>Movie Torrents</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
		Movie Torrents
	</h1>
	<Accordion.Root class="w-full" type="single">
		{#each torrents as movie}
			<div class="p-6">
				<Card.Root>
					<Card.Header>
						<Card.Title>
							{getFullyQualifiedMediaName(movie)}
						</Card.Title>
					</Card.Header>
					<Card.Content>
						<TorrentTable isShow={false} torrents={movie.torrents} />
					</Card.Content>
				</Card.Root>
			</div>
		{:else}
			<div class="col-span-full text-center text-muted-foreground">No Torrents added yet.</div>
		{/each}
	</Accordion.Root>
</main>
