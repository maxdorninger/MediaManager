<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Label } from '$lib/components/ui/label';
	import * as Select from '$lib/components/ui/select/index.js';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import { getFullyQualifiedMediaName, getTorrentQualityString } from '$lib/utils.js';
	import { toast } from 'svelte-sonner';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';

	let { show }: { show: components['schemas']['PublicShow'] } = $props();

	let dialogOpen = $state(false);
	let selectedSeasonsIds = $state<string[]>([]);
	let minQuality = $state<string | undefined>(undefined);
	let wantedQuality = $state<string | undefined>(undefined);
	let isSubmittingRequest = $state(false);
	let submitRequestError = $state<string | null>(null);

	const qualityValues: components['schemas']['Quality'][] = [1, 2, 3, 4];
	let qualityOptions = $derived(
		qualityValues.map((q) => ({ value: q.toString(), label: getTorrentQualityString(q) }))
	);
	let isFormInvalid = $derived(
		!selectedSeasonsIds ||
			selectedSeasonsIds.length === 0 ||
			!minQuality ||
			!wantedQuality ||
			parseInt(wantedQuality) > parseInt(minQuality)
	);

	async function handleRequestSeason() {
		isSubmittingRequest = true;
		submitRequestError = null;

		for (const id of selectedSeasonsIds) {
			const { response, error } = await client.POST('/api/v1/tv/seasons/requests', {
				body: {
					season_id: id,
					min_quality: parseInt(minQuality!) as components['schemas']['Quality'],
					wanted_quality: parseInt(wantedQuality!) as components['schemas']['Quality']
				}
			});

			if (!response.ok) {
				toast.error('Failed to submit request: ' + error);
				submitRequestError = `Failed to submit request for season ID ${id}: ${error}`;
			}
		}

		if (!submitRequestError) {
			dialogOpen = false;
			// Reset form fields
			selectedSeasonsIds = [];
			minQuality = undefined;
			wantedQuality = undefined;
			toast.success('Season request(s) submitted successfully!');
		}

		isSubmittingRequest = false;
	}
</script>

<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Trigger
		class={buttonVariants({ variant: 'default' })}
		onclick={() => {
			dialogOpen = true;
		}}
	>
		Request Season
	</Dialog.Trigger>
	<Dialog.Content class="max-h-[90vh] w-fit min-w-[clamp(300px,50vw,600px)] overflow-y-auto">
		<Dialog.Header>
			<Dialog.Title>Request a Season for {getFullyQualifiedMediaName(show)}</Dialog.Title>
			<Dialog.Description>
				Select a season and desired qualities to submit a request.
			</Dialog.Description>
		</Dialog.Header>
		<div class="grid gap-4 py-4">
			<!-- Season Select -->
			<div class="grid grid-cols-[1fr_3fr] items-center gap-4 md:grid-cols-[100px_1fr]">
				<Label class="text-right" for="season">Season</Label>
				<Select.Root bind:value={selectedSeasonsIds} type="multiple">
					<Select.Trigger class="w-full" id="season">
						{#each selectedSeasonsIds as seasonId (seasonId)}
							{#if show.seasons.find((season) => season.id === seasonId)}
								Season {show.seasons.find((season) => season.id === seasonId)?.number},&nbsp;
							{/if}
						{:else}
							Select one or more seasons
						{/each}
					</Select.Trigger>
					<Select.Content>
						{#each show.seasons as season (season.id)}
							<Select.Item value={season.id || ''}>
								Season {season.number}{season.name ? `: ${season.name}` : ''}
							</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>

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
			<Button disabled={isFormInvalid || isSubmittingRequest} onclick={handleRequestSeason}>
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
