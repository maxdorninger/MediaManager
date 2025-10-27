<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { getFullyQualifiedMediaName } from '$lib/utils';
	import MediaPicture from '$lib/components/media-picture.svelte';
	import { onMount } from 'svelte';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { resolve } from '$app/paths';
	import client from '$lib/api';
	import type { components } from '$lib/api/api.d.ts';

	let movies: components['schemas']['PublicMovie'][] = [];
	let loading = false;
	onMount(async () => {
		loading = true;
		const { data } = await client.GET('/api/v1/movies', { fetch: fetch });

		movies = data as components['schemas']['PublicMovie'][];
		console.log('got movies: ', movies);
		loading = false;
	});
</script>

<svelte:head>
	<title>Movies - MediaManager</title>
	<meta content="Browse and manage your movie collection in MediaManager" name="description" />
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
					<Breadcrumb.Page>Movies</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
{#snippet loadingbar()}
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
	<Skeleton class="h-[50vh] w-full " />
{/snippet}
<main class="flex w-full flex-1 flex-col gap-4 p-4 pt-0">
	<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">Movies</h1>
	<div
		class="grid w-full auto-rows-min gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
	>
		{#if loading}
			{@render loadingbar()}
		{:else}
			{#each movies as movie (movie.id)}
				<a href={resolve('/dashboard/movies/[movieId]', { movieId: movie.id! })}>
					<Card.Root class="col-span-full max-w-[90vw] ">
						<Card.Header>
							<Card.Title class="h-6 truncate">{getFullyQualifiedMediaName(movie)}</Card.Title>
							<Card.Description class="truncate">{movie.overview}</Card.Description>
						</Card.Header>
						<Card.Content>
							<MediaPicture media={movie} />
						</Card.Content>
					</Card.Root>
				</a>
			{:else}
				<div class="col-span-full text-center text-muted-foreground">No movies added yet.</div>
			{/each}
		{/if}
	</div>
</main>
