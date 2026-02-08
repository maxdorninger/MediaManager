<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { LoaderCircle } from 'lucide-svelte';
	import AddMediaCard from '$lib/components/add-media-card.svelte';
	import { onMount } from 'svelte';
	import { resolve } from '$app/paths';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import { handleQueryNotificationToast } from '$lib/utils.ts';

	let searchTerm: string = $state('');
	let results: components['schemas']['MetaDataProviderSearchResult'][] | null = $state(null);
	let isSearching: boolean = $state(false);

	onMount(() => {
		search('');
	});

	async function search(query: string) {
		isSearching = true;
		try {
			const { data } =
				query.length > 0
					? await client.GET('/api/v1/music/search', {
							params: {
								query: {
									query: query
								}
							}
						})
					: await client.GET('/api/v1/music/recommended');
			if (data && data.length > 0) {
				results = data as components['schemas']['MetaDataProviderSearchResult'][];
			} else {
				results = null;
			}
			handleQueryNotificationToast(data?.length ?? 0, query);
		} finally {
			isSearching = false;
		}
	}
</script>

<svelte:head>
	<title>Add Artist - MediaManager</title>
	<meta content="Add a new artist to your MediaManager music collection" name="description" />
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
					<Breadcrumb.Page>Add an Artist</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<main class="flex w-full max-w-[90vw] flex-1 flex-col items-center gap-4 p-4 pt-0">
	<div class="grid w-full max-w-sm items-center gap-12">
		<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
			Add an Artist
		</h1>
		<section>
			<Label for="search-box">Artist Name</Label>
			<Input
				bind:value={searchTerm}
				id="search-box"
				placeholder="Artist Name"
				type="text"
				onkeydown={(e) => {
					if (e.key === 'Enter' && !isSearching) {
						search(searchTerm);
					}
				}}
			/>
			<p class="text-sm text-muted-foreground">Search MusicBrainz for an artist to add.</p>
		</section>
		<section>
			<Button onclick={() => search(searchTerm)} type="submit" disabled={isSearching}>
				{#if isSearching}
					<LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
					<span class="animate-pulse">Searching...</span>
				{:else}
					Search
				{/if}
			</Button>
		</section>
	</div>

	<Separator class="my-8" />

	{#if results && results.length === 0}
		<h3 class="mx-auto">No artists found.</h3>
	{:else if results}
		<div
			class="grid w-full auto-rows-min gap-4 sm:grid-cols-1
		 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
		>
			{#each results as result (result.external_id)}
				<AddMediaCard {result} mediaType="music" />
			{/each}
		</div>
	{/if}
</main>
