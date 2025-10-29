<script lang="ts">
	import { page } from '$app/state';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { getFullyQualifiedMediaName } from '$lib/utils';
	import * as Accordion from '$lib/components/ui/accordion/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import TorrentTable from '$lib/components/torrent-table.svelte';
	import { resolve } from '$app/paths';
</script>

<svelte:head>
	<title>TV Show Torrents - MediaManager</title>
	<meta content="View and manage TV show torrent downloads in MediaManager" name="description" />
</svelte:head>

<header class="flex h-16 shrink-0 items-center gap-2">
	<div class="flex items-center gap-2 px-4">
		<Sidebar.Trigger class="-ml-1" />
		<Separator class="mr-2 h-4" orientation="vertical" />
		<Breadcrumb.Root>
			<Breadcrumb.List>
				<Breadcrumb.Item class="hidden md:block">
					<Breadcrumb.Link href={resolve('/dashboard', {})}>MediaManager</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href={resolve('/dashboard', {})}>Home</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href={resolve('/dashboard/tv', {})}>Shows</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>TV Torrents</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<div class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
		TV Torrents
	</h1>
	<Accordion.Root type="single" class="w-full">
		{#each page.data.torrents as show (show.show_id)}
			<div class="p-6">
				<Card.Root>
					<Card.Header>
						<Card.Title>
							{getFullyQualifiedMediaName(show)}
						</Card.Title>
					</Card.Header>
					<Card.Content>
						<TorrentTable isShow={true} torrents={show.torrents} />
					</Card.Content>
				</Card.Root>
			</div>
		{:else}
			<div class="col-span-full text-center text-muted-foreground">No Torrents added yet.</div>
		{/each}
	</Accordion.Root>
</div>
