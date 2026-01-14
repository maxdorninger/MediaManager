<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { ImageOff } from 'lucide-svelte';
	import { getContext } from 'svelte';
	import type { components } from '$lib/api/api';
	import { getFullyQualifiedMediaName, getTorrentQualityString } from '$lib/utils';
	import { page } from '$app/state';
	import TorrentTable from '$lib/components/torrents/torrent-table.svelte';
	import MediaPicture from '$lib/components/media-picture.svelte';
	import DownloadMovieDialog from '$lib/components/download-dialogs/download-movie-dialog.svelte';
	import RequestMovieDialog from '$lib/components/requests/request-movie-dialog.svelte';
	import LibraryCombobox from '$lib/components/library-combobox.svelte';
	import { resolve } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';
	import DeleteMediaDialog from '$lib/components/delete-media-dialog.svelte';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';

	let movie: components['schemas']['PublicMovie'] = $derived(page.data.movie);
	let movieFiles: components['schemas']['PublicMovieFile'][] = $derived(page.data.movieFiles);
	let user: () => components['schemas']['UserRead'] = getContext('user');
</script>

<svelte:head>
	<title>{getFullyQualifiedMediaName(movie)} - MediaManager</title>
	<meta
		content="View details and manage downloads for {getFullyQualifiedMediaName(
			movie
		)} in MediaManager"
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
					<Breadcrumb.Link href={resolve('/dashboard/movies', {})}>Movies</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>{getFullyQualifiedMediaName(movie)}</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
	{getFullyQualifiedMediaName(movie)}
</h1>
<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<div class="flex flex-col gap-4 md:flex-row md:items-stretch">
		<div class="w-full overflow-hidden rounded-xl bg-muted/50 md:w-1/3 md:max-w-sm">
			{#if movie.id}
				<MediaPicture media={movie} />
			{:else}
				<div
					class="flex aspect-9/16 h-auto w-full items-center justify-center rounded-lg bg-gray-200 text-gray-500"
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
					<p class="text-sm leading-6 text-muted-foreground text-justify hyphens-auto">
						{movie.overview}
					</p>
				</Card.Content>
			</Card.Root>
		</div>
		<div
			class="flex h-full w-full flex-auto flex-col items-center justify-start gap-4 rounded-xl md:w-1/3 md:max-w-[40em]"
		>
			{#if user().is_superuser}
				<Card.Root class="w-full  flex-1">
					<Card.Header>
						<Card.Title>Administrator Controls</Card.Title>
					</Card.Header>
					<Card.Content class="flex flex-col items-center gap-4">
						<LibraryCombobox media={movie} mediaType="movie" />
						<DeleteMediaDialog isShow={false} media={movie} />
					</Card.Content>
				</Card.Root>
			{/if}
			<Card.Root class="w-full  flex-1">
				<Card.Header>
					<Card.Title>Download Options</Card.Title>
				</Card.Header>
				<Card.Content class="flex flex-col items-center gap-4">
					{#if user().is_superuser}
						<DownloadMovieDialog {movie} />
					{/if}
					<RequestMovieDialog {movie} />
				</Card.Content>
			</Card.Root>
		</div>
	</div>
	<div class="flex-1 rounded-xl">
		<Card.Root class="h-full w-full">
			<Card.Header>
				<Card.Title>Movie files</Card.Title>
				<Card.Description>
					A list of all downloaded/downloading versions of this movie.
				</Card.Description>
			</Card.Header>
			<Card.Content>
				<Table.Root>
					<Table.Caption>
						A list of all downloaded/downloading versions of this movie.
					</Table.Caption>
					<Table.Header>
						<Table.Row>
							<Table.Head>Quality</Table.Head>
							<Table.Head>File Path Suffix</Table.Head>
							<Table.Head>Imported</Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#each movieFiles as file (file)}
							<Table.Row>
								<Table.Cell class="w-[50px]">
									{getTorrentQualityString(file.quality)}
								</Table.Cell>
								<Table.Cell class="w-[100px]">
									{file.file_path_suffix}
								</Table.Cell>
								<Table.Cell class="w-[10px] font-medium">
									<CheckmarkX state={file.imported} />
								</Table.Cell>
							</Table.Row>
						{/each}
					</Table.Body>
				</Table.Root>
			</Card.Content>
		</Card.Root>
	</div>
	<div class="flex-1 rounded-xl">
		<Card.Root class="h-full w-full">
			<Card.Header>
				<Card.Title>Torrent Information</Card.Title>
				<Card.Description>A list of all torrents associated with this movie.</Card.Description>
			</Card.Header>
			<Card.Content class="flex flex-col gap-4">
				<TorrentTable isShow={false} torrents={movie.torrents} />
			</Card.Content>
		</Card.Root>
	</div>
</main>
