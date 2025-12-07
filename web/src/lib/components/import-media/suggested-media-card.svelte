<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { ImageOff } from 'lucide-svelte';
	import type { components } from '$lib/api/api';

	let {
		result,
		action
	}: {
		result: components['schemas']['MetaDataProviderSearchResult'];
		action: () => void;
	} = $props();
</script>

<Card.Root class="col-span-full flex h-full flex-col overflow-x-hidden sm:col-span-1">
	<Card.Header>
		<Card.Title class="flex h-12 items-center leading-tight">
			{result.name}
			{#if result.year != null}
				({result.year})
			{/if}
		</Card.Title>
		<Card.Description class="truncate">
			{result.overview !== '' ? result.overview : 'No overview available'}
		</Card.Description>
	</Card.Header>
	<Card.Content class="flex flex-1 items-center justify-center">
		{#if result.poster_path != null}
			<img
				class="h-full w-full rounded-lg object-contain"
				src={result.poster_path}
				alt="{result.name}'s Poster Image"
			/>
		{:else}
			<div class="flex h-full w-full items-center justify-center">
				<ImageOff class="h-12 w-12 text-gray-400" />
			</div>
		{/if}
	</Card.Content>
	<Card.Footer class="flex flex-col items-start gap-2 rounded-b-lg border-t bg-card p-4">
		<Button class="w-full font-semibold" onclick={() => action()}>
			Import using this metadata
		</Button>
		<div class="flex w-full items-center gap-2">
			{#if result.vote_average != null}
				<span class="flex items-center text-sm font-medium text-yellow-600">
					<svg class="mr-1 h-4 w-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"
						><path
							d="M10 15l-5.878 3.09 1.122-6.545L.488 6.91l6.561-.955L10 0l2.951 5.955 6.561.955-4.756 4.635 1.122 6.545z"
						/></svg
					>
					Rating: {Math.round(result.vote_average)}/10
				</span>
			{/if}
		</div>
	</Card.Footer>
</Card.Root>
