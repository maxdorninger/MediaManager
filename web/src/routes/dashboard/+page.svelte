<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import RecommendedMediaCarousel from '$lib/components/recommended-media-carousel.svelte';
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { env } from '$env/dynamic/public';
	import type { MetaDataProviderSearchResult } from '$lib/types';

	const apiUrl = env.PUBLIC_API_URL;

	let recommendedShows: MetaDataProviderSearchResult[] = [];
	let showsLoading = true;

	let recommendedMovies: MetaDataProviderSearchResult[] = [];
	let moviesLoading = true;

	onMount(async () => {
		const showsRes = await fetch(apiUrl + '/tv/recommended', {
			headers: {
				'Content-Type': 'application/json',
				Accept: 'application/json'
			},
			credentials: 'include',
			method: 'GET'
		});
		recommendedShows = await showsRes.json();
		showsLoading = false;

		const moviesRes = await fetch(apiUrl + '/movies/recommended', {
			headers: {
				'Content-Type': 'application/json',
				Accept: 'application/json'
			},
			credentials: 'include',
			method: 'GET'
		});
		recommendedMovies = await moviesRes.json();
		moviesLoading = false;
	});
</script>

<svelte:head>
	<title>Dashboard - MediaManager</title>
	<meta
		content="MediaManager Dashboard - View your recommended movies and TV shows"
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
					<Breadcrumb.Page>Home</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
		Dashboard
	</h1>
	<main class="min-h-screen flex-1 items-center justify-center rounded-xl p-4 md:min-h-min">
		<div class="mx-auto max-w-[70vw] md:max-w-[80vw]">
			<h3 class="my-4 text-center text-2xl font-semibold">Trending Shows</h3>
			<RecommendedMediaCarousel isLoading={showsLoading} isShow={true} media={recommendedShows} />

			<h3 class="my-4 text-center text-2xl font-semibold">Trending Movies</h3>
			<RecommendedMediaCarousel
				isLoading={moviesLoading}
				isShow={false}
				media={recommendedMovies}
			/>
		</div>
	</main>

	<!---
        <div class="grid auto-rows-min gap-4 md:grid-cols-3">
            <div class="aspect-video rounded-xl bg-muted/50"></div>
            <div class="aspect-video rounded-xl bg-muted/50"></div>
            <div class="aspect-video rounded-xl bg-muted/50">
            </div>
        </div>
    -->
</div>
