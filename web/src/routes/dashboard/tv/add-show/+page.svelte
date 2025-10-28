<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { ChevronDown } from 'lucide-svelte';
	import * as Collapsible from '$lib/components/ui/collapsible/index.js';
	import * as RadioGroup from '$lib/components/ui/radio-group/index.js';
	import AddMediaCard from '$lib/components/add-media-card.svelte';
	import { onMount } from 'svelte';

	let searchTerm: string = $state('');
	let metadataProvider: 'tmdb' | 'tvdb' = $state('tmdb');
	let data: components['schemas']['MetaDataProviderSearchResult'][] | null = $state(null);
	import { resolve } from '$app/paths';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import { handleQueryNotificationToast } from '$lib/utils.ts';

	onMount(() => {
		search('');
	});

	async function search(query: string) {
		const results =
			query.length > 0
				? await client.GET('/api/v1/tv/search', {
						params: {
							query: {
								query: query,
								metadata_provider: metadataProvider
							}
						}
					})
				: await client.GET('/api/v1/tv/recommended');
		if (results.data && results.data.length > 0) {
			handleQueryNotificationToast(results.data.length, query);
			data = results.data as components['schemas']['MetaDataProviderSearchResult'][];
		} else {
			handleQueryNotificationToast(0, query);
			data = null;
		}
	}
</script>

<svelte:head>
	<title>Add TV Show - MediaManager</title>
	<meta content="Add a new TV show to your MediaManager collection" name="description" />
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
					<Breadcrumb.Page>Add a Show</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<main class="flex w-full max-w-[90vw] flex-1 flex-col items-center gap-4 p-4 pt-0">
	<div class="grid w-full max-w-sm items-center gap-12">
		<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
			Add a Show
		</h1>
		<section>
			<Label for="search-box">Show Name</Label>
			<Input bind:value={searchTerm} id="search-box" placeholder="Show Name" type="text" />
			<p class="text-muted-foreground text-sm">Search for a Show to add.</p>
		</section>
		<section>
			<Collapsible.Root class="w-full space-y-1">
				<Collapsible.Trigger>
					<div class="flex items-center justify-between space-x-4 px-4">
						<h4 class="text-sm font-semibold">Advanced Settings</h4>
						<Button class="w-9 p-0" size="sm" variant="ghost">
							<ChevronDown />
							<span class="sr-only">Toggle</span>
						</Button>
					</div>
				</Collapsible.Trigger>
				<Collapsible.Content class="space-y-1">
					<Label for="metadata-provider-selector">Choose which Metadata Provider to query.</Label>
					<RadioGroup.Root bind:value={metadataProvider} id="metadata-provider-selector">
						<div class="flex items-center space-x-2">
							<RadioGroup.Item id="option-one" value="tmdb" />
							<Label for="option-one">TMDB (Recommended)</Label>
						</div>
						<div class="flex items-center space-x-2">
							<RadioGroup.Item id="option-two" value="tvdb" />
							<Label for="option-two">TVDB</Label>
						</div>
					</RadioGroup.Root>
				</Collapsible.Content>
			</Collapsible.Root>
		</section>
		<section>
			<Button onclick={() => search(searchTerm)} type="submit">Search</Button>
		</section>
	</div>

	<Separator class="my-8" />

	{#if data && data.length === 0}
		<h3 class="mx-auto">No Shows found.</h3>
	{:else if data}
		<div
			class="grid w-full auto-rows-min gap-4 sm:grid-cols-1
		 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
		>
			{#each data as dataItem (dataItem.external_id)}
				<AddMediaCard result={dataItem} isShow={true} />
			{/each}
		</div>
	{/if}
</main>
