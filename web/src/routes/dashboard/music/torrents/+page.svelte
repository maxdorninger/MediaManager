<script lang="ts">
	import { page } from '$app/state';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { getAudioQualityString } from '$lib/utils';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import { resolve } from '$app/paths';

	let artistTorrents = $derived(page.data.torrents);
</script>

<svelte:head>
	<title>Music Torrents - MediaManager</title>
	<meta content="View and manage music torrent downloads in MediaManager" name="description" />
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
					<Breadcrumb.Link href={resolve('/dashboard/music', {})}>Music</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>Music Torrents</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<div class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
		Music Torrents
	</h1>
	{#if artistTorrents && artistTorrents.length > 0}
		{#each artistTorrents as artistTorrent (artistTorrent.artist_id)}
			<div class="p-6">
				<Card.Root>
					<Card.Header>
						<Card.Title>
							<a
								href={resolve('/dashboard/music/[artistId]', {
									artistId: artistTorrent.artist_id
								})}
								class="underline"
							>
								{artistTorrent.name}
							</a>
						</Card.Title>
					</Card.Header>
					<Card.Content>
						<Table.Root>
							<Table.Header>
								<Table.Row>
									<Table.Head>Title</Table.Head>
									<Table.Head>Quality</Table.Head>
									<Table.Head>Imported</Table.Head>
								</Table.Row>
							</Table.Header>
							<Table.Body>
								{#each artistTorrent.torrents as torrent (torrent.torrent_id)}
									<Table.Row>
										<Table.Cell>{torrent.torrent_title}</Table.Cell>
										<Table.Cell>{getAudioQualityString(torrent.quality)}</Table.Cell>
										<Table.Cell>
											<CheckmarkX state={torrent.imported} />
										</Table.Cell>
									</Table.Row>
								{/each}
							</Table.Body>
						</Table.Root>
					</Card.Content>
				</Card.Root>
			</div>
		{/each}
	{:else}
		<div class="col-span-full text-center text-muted-foreground">No Torrents added yet.</div>
	{/if}
</div>
