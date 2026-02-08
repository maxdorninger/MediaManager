<script lang="ts">
	import AddMediaCard from '$lib/components/add-media-card.svelte';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Button } from '$lib/components/ui/button';
	import { ChevronRight } from 'lucide-svelte';
	import type { components } from '$lib/api/api';
	import { resolve } from '$app/paths';

	let {
		media,
		mediaType,
		isLoading
	}: {
		media: components['schemas']['MetaDataProviderSearchResult'][];
		mediaType: 'tv' | 'movie' | 'music';
		isLoading: boolean;
	} = $props();

	const moreLinks = {
		tv: '/dashboard/tv/add-show',
		movie: '/dashboard/movies/add-movie',
		music: '/dashboard/music/add-artist'
	};
</script>

<div
	class="grid w-full gap-4 sm:grid-cols-1
     md:grid-cols-2 lg:grid-cols-3"
>
	{#if isLoading}
		<Skeleton class="h-[70vh] w-full" />
		<Skeleton class="h-[70vh] w-full" />
		<Skeleton class="h-[70vh] w-full" />
	{:else}
		{#each media.slice(0, 3) as mediaItem (mediaItem.external_id)}
			<AddMediaCard {mediaType} result={mediaItem} />
		{/each}
	{/if}
	<Button
		class="md:col-start-2"
		variant="secondary"
		href={resolve(moreLinks[mediaType], {})}
	>
		More recommendations
		<ChevronRight />
	</Button>
</div>
