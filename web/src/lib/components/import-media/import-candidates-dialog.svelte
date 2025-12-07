<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { toast } from 'svelte-sonner';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import { Spinner } from '$lib/components/ui/spinner';
	import SuggestedMediaCard from '$lib/components/import-media/suggested-media-card.svelte';
    import {invalidateAll} from "$app/navigation";

	let {
		isTv,
		name,
		candidates,
		children
	}: {
		isTv: boolean;
		name: string;
		candidates: components['schemas']['MetaDataProviderSearchResult'][];
		children: any;
	} = $props();
	let dialogOpen = $state(false);
	let submitRequestError = $state<string | null>(null);
	let isImporting = $state<boolean>(false);

	async function handleImportMedia(media: components['schemas']['MetaDataProviderSearchResult']) {
		isImporting = true;
		submitRequestError = null;
        let errored = null;
        if(isTv) {
            let { data } = await client.POST('/api/v1/tv/shows', {
                params: {
                    query: {
                        metadata_provider: media.metadata_provider as 'tmdb' | 'tvdb',
                        show_id: media.external_id
                    }
                }
            });
            let showId = data?.id ?? 'no_id';
            const { error } = await client.POST('/api/v1/tv/importable/{show_id}', {
                params: {
                    path: {
                        show_id: showId
                    },
                    query: {
                        directory: name
                    }
                }
            });
            errored = error;
        }else{
            let { data } = await client.POST('/api/v1/movies', {
                params: {
                    query: {
                        metadata_provider: media.metadata_provider as 'tmdb' | 'tvdb',
                        movie_id: media.external_id
                    }
                }
            });
            let movieId = data?.id ?? 'no_id';
            const { error } = await client.POST('/api/v1/movies/importable/{movie_id}', {
                params: {
                    path: {
                        movie_id: movieId
                    },
                    query: {
                        directory: name
                    }
                }
            });
            errored = error;
        }
		isImporting = false;

		if (errored) {
			toast.error('Failed to import');
		} else {
			dialogOpen = false;
			toast.success('Imported successfully!');
		}
        await invalidateAll()
    }
</script>

<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Trigger
		class={buttonVariants({ variant: 'default' })}
		onclick={() => {
			dialogOpen = true;
		}}
	>
		{@render children?.()}
	</Dialog.Trigger>
	<Dialog.Content class="max-h-[90vh] w-fit min-w-[80vw] overflow-y-auto">
		<Dialog.Header>
			<Dialog.Title>Import unknown {isTv ? 'show' : 'movie'} "{name}"</Dialog.Title>
			<Dialog.Description
				>Select the {isTv ? 'show' : 'movie'} that is in this directory to import it!
			</Dialog.Description>
		</Dialog.Header>
		<div
			class="grid w-full auto-rows-min gap-4 sm:grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-4"
		>
			{#if !isImporting}
				{#each candidates as candidate (candidate.external_id)}
					<SuggestedMediaCard result={candidate} action={() => handleImportMedia(candidate)}
					></SuggestedMediaCard>
				{:else}
					No {isTv ? 'shows' : 'movies'} were found, change the directory's name for better search results!
				{/each}
			{:else}
				<Spinner class="size-8"></Spinner>
			{/if}
			{#if submitRequestError}
				<p class="col-span-full text-center text-sm text-red-500">{submitRequestError}</p>
			{/if}
		</div>
		<Dialog.Footer>
			<Button disabled={isImporting} onclick={() => (dialogOpen = false)} variant="outline"
				>Cancel
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
