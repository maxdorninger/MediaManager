<script lang="ts">
	import { buttonVariants } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { ImageOff } from 'lucide-svelte';
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { components } from '$lib/api/api';
	import { getFullyQualifiedMediaName } from '$lib/utils';
	import { page } from '$app/state';
	import TorrentTable from '$lib/components/torrent-table.svelte';
	import MediaPicture from '$lib/components/media-picture.svelte';
	import DownloadMovieDialog from '$lib/components/download-movie-dialog.svelte';
	import RequestMovieDialog from '$lib/components/request-movie-dialog.svelte';
	import LibraryCombobox from '$lib/components/library-combobox.svelte';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Label } from '$lib/components/ui/label';
	import { base } from '$app/paths';
	import { resolve } from '$app/paths';
	import { goto } from '$app/navigation';
	import * as Card from '$lib/components/ui/card/index.js';
	import client from '$lib/api';

	let movie: components['schemas']['PublicMovie'] = page.data.movie;
	let user: () => components['schemas']['UserRead'] = getContext('user');
	let deleteDialogOpen = $state(false);
	let deleteFilesOnDisk = $state(false);

	async function delete_movie() {
		// TODO: Implement delete_files_on_disk parameter in backend API
		const { response } = await client.DELETE('/api/v1/movies/{movie_id}', {
			params: {
				path: { movie_id: movie.id }
				// query: { delete_files_on_disk: deleteFilesOnDisk } // Not yet implemented
			}
		});
		if (!response.ok) {
			const errorText = await response.text();
			toast.error('Failed to delete movie: ' + errorText);
		} else {
			toast.success('Movie deleted successfully.');
			deleteDialogOpen = false;
			await goto(resolve('/dashboard/movies', {}), { invalidateAll: true });
		}
	}
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
						<AlertDialog.Root bind:open={deleteDialogOpen}>
							<AlertDialog.Trigger
								class={buttonVariants({ variant: "destructive" })}
							>
								Delete Show
							</AlertDialog.Trigger>
							<AlertDialog.Content>
								<AlertDialog.Header>
									<AlertDialog.Title>Are you absolutely sure?</AlertDialog.Title>
									<AlertDialog.Description>
										This action cannot be undone. This will permanently delete
										<strong>{getFullyQualifiedMediaName(movie)}</strong> from the database.
									</AlertDialog.Description>
								</AlertDialog.Header>
								<div class="flex items-center space-x-2 py-4">
									<Checkbox bind:checked={deleteFilesOnDisk} id="delete-files" />
									<Label
										for="delete-files"
										class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
									>
										Also delete files on disk (not yet implemented)
									</Label>
								</div>
								<AlertDialog.Footer>
									<AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
									<AlertDialog.Action
										onclick={() => delete_movie()}
										class={buttonVariants({ variant: "destructive" })}
									>
										Delete
									</AlertDialog.Action>
								</AlertDialog.Footer>
							</AlertDialog.Content>
						</AlertDialog.Root>
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
