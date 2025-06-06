<script lang="ts">
    import {env} from '$env/dynamic/public';
    import {Button, buttonVariants} from '$lib/components/ui/button/index.js';
    import * as Dialog from '$lib/components/ui/dialog/index.js';
    import {Label} from '$lib/components/ui/label';
    import * as Select from '$lib/components/ui/select/index.js';
    import LoaderCircle from '@lucide/svelte/icons/loader-circle';
    import type {CreateSeasonRequest, PublicShow, Quality} from '$lib/types.js';
    import {getFullyQualifiedShowName, getTorrentQualityString} from '$lib/utils.js';
    import {toast} from 'svelte-sonner';
    import {browser} from "$app/environment";

    const apiUrl = browser ? env.PUBLIC_API_URL : env.PUBLIC_SSR_API_URL;
    let {show}: { show: PublicShow } = $props();

    let dialogOpen = $state(false);
    let selectedSeasonsIds = $state<string[]>([]);
    let minQuality = $state<Quality | undefined>(undefined);
    let wantedQuality = $state<Quality | undefined>(undefined);
    let isSubmittingRequest = $state(false);
    let submitRequestError = $state<string | null>(null);

    const qualityValues: Quality[] = [1, 2, 3, 4];
    let qualityOptions = $derived(
        qualityValues.map((q) => ({value: q, label: getTorrentQualityString(q)}))
    );
    let isFormInvalid = $derived(
        !selectedSeasonsIds ||
        selectedSeasonsIds.length === 0 ||
        !minQuality ||
        !wantedQuality ||
        wantedQuality > minQuality
    );

    async function handleRequestSeason() {
        isSubmittingRequest = true;
        submitRequestError = null;

        const payloads: CreateSeasonRequest = selectedSeasonsIds.map((seasonId) => ({
            season_id: seasonId,
            min_quality: minQuality,
            wanted_quality: wantedQuality
        }));
        for (const payload of payloads) {
            try {
                const response = await fetch(`${apiUrl}/tv/seasons/requests`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });

                if (response.status === 204) {
                    // Success, no content
                    dialogOpen = false; // Close the dialog
                    // Reset form fields
                    selectedSeasonsIds = undefined;
                    minQuality = undefined;
                    wantedQuality = undefined;
                    toast.success('Season request submitted successfully!');
                } else {
                    const errorData = await response.json().catch(() => ({message: response.statusText}));
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
    }
</script>

<Dialog.Root bind:open={dialogOpen}>
    <Dialog.Trigger
            class={buttonVariants({ variant: 'default' })}
            on:click={() => {
			dialogOpen = true;
		}}
    >
        Request Season
    </Dialog.Trigger>
    <Dialog.Content class="max-h-[90vh] w-fit min-w-[clamp(300px,50vw,600px)] overflow-y-auto">
        <Dialog.Header>
            <Dialog.Title>Request a Season for {getFullyQualifiedShowName(show)}</Dialog.Title>
            <Dialog.Description>
                Select a season and desired qualities to submit a request.
            </Dialog.Description>
        </Dialog.Header>
        <div class="grid gap-4 py-4">
            <!-- Season Select -->
            <div class="grid grid-cols-[1fr,3fr] items-center gap-4 md:grid-cols-[100px,1fr]">
                <Label class="text-right" for="season">Season</Label>
                <Select.Root bind:value={selectedSeasonsIds}>
                    <Select.Trigger class="w-full" id="season">
                        {#each selectedSeasonsIds as seasonId (seasonId)}
                            {#if show.seasons.find((season) => season.id === seasonId)}
                                {show.seasons.find((season) => season.id === seasonId).number},&nbsp;
                            {/if}
                        {:else}
                            Select one or more seasons
                        {/each}
                    </Select.Trigger>
                    <Select.Content>
                        {#each show.seasons as season (season.id)}
                            <Select.Item value={season.id}>
                                Season {season.number}{season.name ? `: ${season.name}` : ''}
                            </Select.Item>
                        {/each}
                    </Select.Content>
                </Select.Root>
            </div>

            <!-- Min Quality Select -->
            <div class="grid grid-cols-[1fr,3fr] items-center gap-4 md:grid-cols-[100px,1fr]">
                <Label class="text-right" for="min-quality">Min Quality</Label>
                <Select.Root bind:value={minQuality} type="single">
                    <Select.Trigger class="w-full" id="min-quality">
                        {minQuality ? getTorrentQualityString(minQuality) : 'Select Minimum Quality'}
                    </Select.Trigger>
                    <Select.Content>
                        {#each qualityOptions as option (option.value)}
                            <Select.Item value={option.value}>{option.label}</Select.Item>
                        {/each}
                    </Select.Content>
                </Select.Root>
            </div>

            <!-- Wanted Quality Select -->
            <div class="grid grid-cols-[1fr,3fr] items-center gap-4 md:grid-cols-[100px,1fr]">
                <Label class="text-right" for="wanted-quality">Wanted Quality</Label>
                <Select.Root bind:value={wantedQuality} type="single">
                    <Select.Trigger class="w-full" id="wanted-quality">
                        {wantedQuality ? getTorrentQualityString(wantedQuality) : 'Select Wanted Quality'}
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
                    <LoaderCircle class="mr-2 h-4 w-4 animate-spin"/>
                    Submitting...
                {:else}
                    Submit Request
                {/if}
            </Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>
