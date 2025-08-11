<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Label } from '$lib/components/ui/label';
	import * as Select from '$lib/components/ui/select/index.js';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import type { PublicMovie, Quality } from '$lib/types.js';
	import { getFullyQualifiedMediaName, getTorrentQualityString } from '$lib/utils.js';
	import { toast } from 'svelte-sonner';

	const apiUrl = env.PUBLIC_API_URL;
	let { movie }: { movie: PublicMovie } = $props();
	let dialogOpen = $state(false);
	let minQuality = $state<string | undefined>(undefined);
	let wantedQuality = $state<string | undefined>(undefined);
	let isSubmittingRequest = $state(false);
	let submitRequestError = $state<string | null>(null);

	const qualityValues: Quality[] = [1, 2, 3, 4];
	let qualityOptions = $derived(
		qualityValues.map((q) => ({ value: q.toString(), label: getTorrentQualityString(q) }))
	);
	let isFormInvalid = $derived(
		!minQuality || !wantedQuality || parseInt(wantedQuality) > parseInt(minQuality)
	);

	async function handleRequestMovie() {
		isSubmittingRequest = true;
		submitRequestError = null;

		try {
			const response = await fetch(`${apiUrl}/movies/requests`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include',
				body: JSON.stringify({
					movie_id: movie.id,
					min_quality: parseInt(minQuality!),
					wanted_quality: parseInt(wantedQuality!)
				})
			});

			if (response.ok) {
				dialogOpen = false;
				minQuality = undefined;
				wantedQuality = undefined;
				toast.success('Movie request submitted successfully!');
			} else {
				const errorData = await response.json().catch(() => ({ message: response.statusText }));
				submitRequestError = `Failed to submit request: ${errorData.message || response.statusText}`;
				toast.error(submitRequestError);
				console.error('Failed to submit request', response.statusText, errorData);
			}
		} catch (error) {
			submitRequestError = `Error submitting request: ${error instanceof Error ? error.message : String(error)}`;
			toast.error(submitRequestError);
			console.error('Error submitting request:', error);
		} finally {
			isSubmittingRequest = false;
		}
	}
</script>

<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Trigger
		class={buttonVariants({ variant: 'default' })}
		onclick={() => {
			dialogOpen = true;
		}}
	>
		Request Movie
	</Dialog.Trigger>
	<Dialog.Content class="max-h-[90vh] w-fit min-w-[clamp(300px,50vw,600px)] overflow-y-auto">
		<Dialog.Header>
			<Dialog.Title>Request {getFullyQualifiedMediaName(movie)}</Dialog.Title>
			<Dialog.Description>Select desired qualities to submit a request.</Dialog.Description>
		</Dialog.Header>
		<div class="grid gap-4 py-4">
			<!-- Min Quality Select -->
			<div class="grid grid-cols-[1fr_3fr] items-center gap-4 md:grid-cols-[100px_1fr]">
				<Label class="text-right" for="min-quality">Min Quality</Label>
				<Select.Root bind:value={minQuality} type="single">
					<Select.Trigger class="w-full" id="min-quality">
						{minQuality ? getTorrentQualityString(parseInt(minQuality)) : 'Select Minimum Quality'}
					</Select.Trigger>
					<Select.Content>
						{#each qualityOptions as option (option.value)}
							<Select.Item value={option.value}>{option.label}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>

			<!-- Wanted Quality Select -->
			<div class="grid grid-cols-[1fr_3fr] items-center gap-4 md:grid-cols-[100px_1fr]">
				<Label class="text-right" for="wanted-quality">Wanted Quality</Label>
				<Select.Root bind:value={wantedQuality} type="single">
					<Select.Trigger class="w-full" id="wanted-quality">
						{wantedQuality
							? getTorrentQualityString(parseInt(wantedQuality))
							: 'Select Wanted Quality'}
					</Select.Trigger>
					<Select.Content>
						{#each qualityOptions as option (option.value)}
							<Select.Item value={option.value}>{option.label}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>

			{#if submitRequestError}
				<p class="col-span-full text-center text-sm text-red-500">{submitRequestError}</p>
			{/if}
		</div>
		<Dialog.Footer>
			<Button disabled={isSubmittingRequest} onclick={() => (dialogOpen = false)} variant="outline"
				>Cancel
			</Button>
			<Button disabled={isFormInvalid || isSubmittingRequest} onclick={handleRequestMovie}>
				{#if isSubmittingRequest}
					<LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
					Submitting...
				{:else}
					Submit Request
				{/if}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
