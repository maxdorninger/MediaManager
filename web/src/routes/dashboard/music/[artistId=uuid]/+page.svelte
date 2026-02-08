<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { goto } from '$app/navigation';
	import { ImageOff } from 'lucide-svelte';
	import * as Table from '$lib/components/ui/table/index.js';
	import { getContext } from 'svelte';
	import type { components } from '$lib/api/api';
	import { getAudioQualityString } from '$lib/utils';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import { page } from '$app/state';
	import TorrentTable from '$lib/components/torrents/torrent-table.svelte';
	import MediaPicture from '$lib/components/media-picture.svelte';
	import LibraryCombobox from '$lib/components/library-combobox.svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import DeleteMediaDialog from '$lib/components/delete-media-dialog.svelte';
	import { resolve } from '$app/paths';

	let artist: components['schemas']['PublicArtist'] = $derived(page.data.artistData);
	let torrents: components['schemas']['RichArtistTorrent'] = $derived(page.data.torrentsData);
	let user: () => components['schemas']['UserRead'] = getContext('user');
</script>

<svelte:head>
	<title>{artist.name} - MediaManager</title>
	<meta
		content="View details and manage downloads for {artist.name} in MediaManager"
		name="description"
	/>
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
					<Breadcrumb.Page>{artist.name}</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
	{artist.name}
</h1>
<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<div class="flex flex-col gap-4 md:flex-row md:items-stretch">
		<div class="w-full overflow-hidden rounded-xl bg-muted/50 md:w-1/3 md:max-w-sm">
			{#if artist.id}
				<MediaPicture media={artist} />
			{:else}
				<div
					class="flex aspect-square h-auto w-full items-center justify-center rounded-lg bg-gray-200 text-gray-500"
				>
					<ImageOff size={48} />
				</div>
			{/if}
		</div>
		<div class="h-full w-full flex-auto rounded-xl md:w-1/4">
			<Card.Root class="h-full w-full">
				<Card.Header>
					<Card.Title>Overview</Card.Title>
				</Card.Header>
				<Card.Content>
					<p class="leading-7 not-first:mt-6">
						{artist.overview}
					</p>
					{#if artist.country}
						<p class="mt-4 text-sm text-muted-foreground">Country: {artist.country}</p>
					{/if}
					{#if artist.disambiguation}
						<p class="text-sm text-muted-foreground">({artist.disambiguation})</p>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>
		<div
			class="flex h-full w-full flex-auto flex-col items-center justify-start gap-4 rounded-xl md:w-1/3 md:max-w-[40em]"
		>
			{#if user().is_superuser}
				<Card.Root class="w-full flex-1">
					<Card.Header>
						<Card.Title>Administrator Controls</Card.Title>
					</Card.Header>
					<Card.Content class="flex flex-col items-center gap-4">
						<LibraryCombobox media={artist} mediaType="music" />
						<DeleteMediaDialog isShow={false} isMusic={true} media={artist} />
					</Card.Content>
				</Card.Root>
			{/if}
		</div>
	</div>
	<div class="flex-1 rounded-xl">
		<Card.Root class="w-full">
			<Card.Header>
				<Card.Title>Albums</Card.Title>
				<Card.Description>
					A list of all albums for {artist.name}.
				</Card.Description>
			</Card.Header>
			<Card.Content class="w-full overflow-x-auto">
				<Table.Root>
					<Table.Caption>A list of all albums.</Table.Caption>
					<Table.Header>
						<Table.Row>
							<Table.Head>Name</Table.Head>
							<Table.Head>Year</Table.Head>
							<Table.Head>Type</Table.Head>
							<Table.Head>Downloaded</Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#if artist.albums && artist.albums.length > 0}
							{#each artist.albums as album (album.id)}
								<Table.Row
									onclick={() =>
										goto(
											resolve('/dashboard/music/[artistId]/[albumId]', {
												artistId: artist.id,
												albumId: album.id
											})
										)}
								>
									<Table.Cell class="min-w-[100px] font-medium">{album.name}</Table.Cell>
									<Table.Cell class="min-w-[50px]">{album.year ?? 'N/A'}</Table.Cell>
									<Table.Cell class="min-w-[50px] capitalize">{album.album_type}</Table.Cell>
									<Table.Cell class="min-w-[10px] font-medium">
										<CheckmarkX state={album.downloaded} />
									</Table.Cell>
								</Table.Row>
							{/each}
						{:else}
							<Table.Row>
								<Table.Cell colspan={4} class="text-center">No album data available.</Table.Cell>
							</Table.Row>
						{/if}
					</Table.Body>
				</Table.Root>
			</Card.Content>
		</Card.Root>
	</div>
	<div class="flex-1 rounded-xl">
		<Card.Root>
			<Card.Header>
				<Card.Title>Torrent Information</Card.Title>
				<Card.Description>A list of all torrents associated with this artist.</Card.Description>
			</Card.Header>

			<Card.Content class="w-full overflow-x-auto">
				{#if torrents && torrents.torrents}
					<Table.Root>
						<Table.Caption>Torrents for {artist.name}.</Table.Caption>
						<Table.Header>
							<Table.Row>
								<Table.Head>Title</Table.Head>
								<Table.Head>Quality</Table.Head>
								<Table.Head>Imported</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each torrents.torrents as torrent (torrent.torrent_id)}
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
				{:else}
					<p class="text-center text-muted-foreground">No torrents associated.</p>
				{/if}
			</Card.Content>
		</Card.Root>
	</div>
</main>
