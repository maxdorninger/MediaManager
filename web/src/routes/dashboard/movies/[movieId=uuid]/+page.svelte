<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { ImageOff } from 'lucide-svelte';
	import { getContext } from 'svelte';
	import type { PublicMovie, User } from '$lib/types.js';
	import { getFullyQualifiedMediaName } from '$lib/utils';
	import { page } from '$app/state';
	import TorrentTable from '$lib/components/torrent-table.svelte';
	import MediaPicture from '$lib/components/media-picture.svelte';
	import DownloadMovieDialog from '$lib/components/download-movie-dialog.svelte';
	import RequestMovieDialog from '$lib/components/request-movie-dialog.svelte';
	import LibraryCombobox from '$lib/components/library-combobox.svelte';
	import { base } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';

	let movie: PublicMovie = page.data.movie;
	let user: () => User = getContext('user');
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
					class="aspect-9/16 flex h-auto w-full items-center justify-center rounded-lg bg-gray-200 text-gray-500"
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
				<Card.Title>Torrent Information</Card.Title>
				<Card.Description>A list of all torrents associated with this movie.</Card.Description>
			</Card.Header>
			<Card.Content class="flex flex-col gap-4">
				<TorrentTable isShow={false} torrents={movie.torrents} />
			</Card.Content>
		</Card.Root>
	</div>
</main>
