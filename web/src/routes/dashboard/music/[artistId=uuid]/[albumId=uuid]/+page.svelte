<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { page } from '$app/state';
	import { getAudioQualityString } from '$lib/utils';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import { resolve } from '$app/paths';
	import type { components } from '$lib/api/api';
	import { getContext } from 'svelte';
	import DownloadAlbumDialog from '$lib/components/download-dialogs/download-album-dialog.svelte';
	import RequestAlbumDialog from '$lib/components/requests/request-album-dialog.svelte';

	let artist: components['schemas']['PublicArtist'] = $derived(page.data.artistData);
	let album: components['schemas']['Album'] = $derived(page.data.album);
	let albumFiles: components['schemas']['PublicAlbumFile'][] = $derived(page.data.albumFiles);
	let user: () => components['schemas']['UserRead'] = getContext('user');
</script>

<svelte:head>
	<title>{album.name} - {artist.name} - MediaManager</title>
	<meta
		content="View details for album {album.name} by {artist.name} in MediaManager"
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
					<Breadcrumb.Link href={resolve('/dashboard/music/[artistId]', { artistId: artist.id })}>
						{artist.name}
					</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>{album.name}</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
	{album.name}
</h1>
<p class="text-center text-muted-foreground">
	{artist.name}
	{#if album.year}
		&middot; {album.year}
	{/if}
	&middot; <span class="capitalize">{album.album_type}</span>
</p>
<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<div class="flex flex-col gap-4 md:flex-row md:items-stretch">
		<div class="w-full flex-1 rounded-xl">
			<Card.Root class="h-full w-full">
				<Card.Header>
					<Card.Title>Download Options</Card.Title>
				</Card.Header>
				<Card.Content class="flex flex-col items-center gap-4">
					{#if user().is_superuser}
						<DownloadAlbumDialog {artist} {album} />
					{/if}
					<RequestAlbumDialog {artist} {album} />
				</Card.Content>
			</Card.Root>
		</div>
		<div class="w-full flex-1 rounded-xl">
			<Card.Root class="h-full w-full">
				<Card.Header>
					<Card.Title>Album Files</Card.Title>
					<Card.Description>Downloaded/downloading versions of this album.</Card.Description>
				</Card.Header>
				<Card.Content>
					<Table.Root>
						<Table.Caption>
							A list of all downloaded/downloading versions of this album.
						</Table.Caption>
						<Table.Header>
							<Table.Row>
								<Table.Head>Quality</Table.Head>
								<Table.Head>File Path Suffix</Table.Head>
								<Table.Head>Downloaded</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#if albumFiles && albumFiles.length > 0}
								{#each albumFiles as file (file)}
									<Table.Row>
										<Table.Cell class="w-[50px]">
											{getAudioQualityString(file.quality)}
										</Table.Cell>
										<Table.Cell class="w-[100px]">
											{file.file_path_suffix}
										</Table.Cell>
										<Table.Cell class="w-[10px] font-medium">
											<CheckmarkX state={file.downloaded} />
										</Table.Cell>
									</Table.Row>
								{/each}
							{:else}
								<Table.Row>
									<Table.Cell colspan={3} class="text-center">No album files yet.</Table.Cell>
								</Table.Row>
							{/if}
						</Table.Body>
					</Table.Root>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
	<div class="flex-1 rounded-xl">
		<Card.Root class="w-full">
			<Card.Header>
				<Card.Title>Tracks</Card.Title>
				<Card.Description>
					Track listing for {album.name}.
				</Card.Description>
			</Card.Header>
			<Card.Content class="w-full overflow-x-auto">
				<Table.Root>
					<Table.Caption>Track listing.</Table.Caption>
					<Table.Header>
						<Table.Row>
							<Table.Head>#</Table.Head>
							<Table.Head>Title</Table.Head>
							<Table.Head>Duration</Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#if album.tracks && album.tracks.length > 0}
							{#each album.tracks as track (track.id)}
								<Table.Row>
									<Table.Cell class="w-[30px] font-medium">{track.number}</Table.Cell>
									<Table.Cell>{track.title}</Table.Cell>
									<Table.Cell class="w-[80px]">
										{#if track.duration_ms}
											{Math.floor(track.duration_ms / 60000)}:{String(
												Math.floor((track.duration_ms % 60000) / 1000)
											).padStart(2, '0')}
										{:else}
											--:--
										{/if}
									</Table.Cell>
								</Table.Row>
							{/each}
						{:else}
							<Table.Row>
								<Table.Cell colspan={3} class="text-center">No track data available.</Table.Cell>
							</Table.Row>
						{/if}
					</Table.Body>
				</Table.Root>
			</Card.Content>
		</Card.Root>
	</div>
</main>
