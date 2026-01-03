<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { toast } from 'svelte-sonner';
	import {
		convertTorrentSeasonRangeToIntegerRange,
		formatSecondsToOptimalUnit
	} from '$lib/utils.ts';
	import * as Table from '$lib/components/ui/table';
	import { Badge } from '$lib/components/ui/badge';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import SelectFilePathSuffixDialog from '$lib/components/download-dialogs/select-file-path-suffix-dialog.svelte';
	import { invalidateAll } from '$app/navigation';
	import TorrentTable from '$lib/components/download-dialogs/torrent-table.svelte';
	import SearchTabs from '$lib/components/download-dialogs/search-tabs.svelte';
	import DownloadDialogWrapper from '$lib/components/download-dialogs/download-dialog-wrapper.svelte';

	let { show }: { show: components['schemas']['Show'] } = $props();
	let dialogueState = $state(false);
	let selectedSeasonNumber: number = $state(1);
	let torrentsError: string | null = $state(null);
	let queryOverride: string = $state('');
	let filePathSuffix: string = $state('');

	let torrentsPromise: any = $state();
	let torrentsData: any[] | null = $state(null);
	let tabState: string = $state('basic');
	let isLoading: boolean = $state(false);

	let advancedMode: boolean = $derived(tabState === 'advanced');

	const tableColumnHeadings = [
		{ name: 'Size', id: 'size' },
		{ name: 'Usenet', id: 'usenet' },
		{ name: 'Seeders', id: 'seeders' },
		{ name: 'Age', id: 'age' },
		{ name: 'Score', id: 'score' },
		{ name: 'Indexer', id: 'indexer' },
		{ name: 'Indexer Flags', id: 'flags' },
		{ name: 'Seasons', id: 'season' }
	];

	async function downloadTorrent(result_id: string) {
		torrentsError = null;
		const { response } = await client.POST('/api/v1/tv/torrents', {
			params: {
				query: {
					show_id: show.id!,
					public_indexer_result_id: result_id,
					override_file_path_suffix: filePathSuffix === '' ? undefined : filePathSuffix
				}
			}
		});
		if (response.status === 409) {
			const errorMessage = `There already is a Season File using the Filepath Suffix '${filePathSuffix}'. Try again with a different Filepath Suffix.`;
			console.warn(errorMessage);
			torrentsError = errorMessage;
			if (dialogueState) toast.info(errorMessage);
		} else if (!response.ok) {
			const errorMessage = `Failed to download torrent for show ${show.id} and season ${selectedSeasonNumber}: ${response.statusText}`;
			console.error(errorMessage);
			torrentsError = errorMessage;
			toast.error(errorMessage);
		} else {
			toast.success('Torrent download started successfully!');
		}
		await invalidateAll();
	}

	async function search() {
		isLoading = true;
		torrentsError = null;
		torrentsData = null;
		torrentsPromise = client
			.GET('/api/v1/tv/torrents', {
				params: {
					query: {
						show_id: show.id!,
						search_query_override: advancedMode ? queryOverride : undefined,
						season_number: advancedMode ? undefined : selectedSeasonNumber
					}
				}
			})
			.then((data) => data?.data)
			.finally(() => (isLoading = false));

		toast.info('Searching for torrents...');

		torrentsData = await torrentsPromise;
		toast.info('Found ' + torrentsData?.length + ' torrents.');
	}
</script>

<DownloadDialogWrapper
	bind:open={dialogueState}
	triggerText="Download Seasons"
	title="Download a Season"
	description="Search and download torrents for a specific season or season packs."
>
	<SearchTabs
		bind:tabState
		{isLoading}
		bind:queryOverride
		onSearch={search}
		advancedModeHelpText="The custom query will override the default search string like 'The Simpsons Season 3'. Note that only Seasons which are listed in the 'Seasons' cell will be imported!"
	>
		{#snippet basicModeContent()}
			<Label for="season-number">
				Enter a season number from 1 to {show.seasons.at(-1)?.number}
			</Label>
			<div class="flex w-full max-w-sm items-center space-x-2">
				<Input
					type="number"
					id="season-number"
					bind:value={selectedSeasonNumber}
					max={show.seasons.at(-1)?.number}
				/>
				<Button disabled={isLoading} class="w-fit" onclick={search}>Search for Torrents</Button>
			</div>
			<p class="text-sm text-muted-foreground">
				Enter the season's number you want to search for. The first, usually 1, or the last season
				number usually yield the most season packs. Note that only Seasons which are listed in the
				"Seasons" cell will be imported!
			</p>
		{/snippet}
	</SearchTabs>
	{#if torrentsError}
		<div class="my-2 w-full text-center text-red-500">An error occurred: {torrentsError}</div>
	{/if}
	<TorrentTable {torrentsPromise} columns={tableColumnHeadings}>
		{#snippet rowSnippet(torrent)}
			<Table.Cell class="max-w-[300px] font-medium">{torrent.title}</Table.Cell>
			<Table.Cell>{(torrent.size / 1024 / 1024 / 1024).toFixed(2)}GB</Table.Cell>
			<Table.Cell>{torrent.usenet}</Table.Cell>
			<Table.Cell>{torrent.usenet ? 'N/A' : torrent.seeders}</Table.Cell>
			<Table.Cell
				>{torrent.age
					? formatSecondsToOptimalUnit(torrent.age)
					: torrent.usenet
						? 'N/A'
						: ''}</Table.Cell
			>
			<Table.Cell>{torrent.score}</Table.Cell>
			<Table.Cell>{torrent.indexer ?? 'unknown'}</Table.Cell>
			<Table.Cell>
				{#if torrent.flags}
					{#each torrent.flags as flag (flag)}
						<Badge variant="outline">{flag}</Badge>
					{/each}
				{/if}
			</Table.Cell>
			<Table.Cell>
				{#if torrent.season}
					{convertTorrentSeasonRangeToIntegerRange(torrent.season)}
				{/if}
			</Table.Cell>
			<Table.Cell class="text-right">
				<SelectFilePathSuffixDialog
					bind:filePathSuffix
					media={show}
					callback={() => downloadTorrent(torrent.id)}
				/>
			</Table.Cell>
		{/snippet}
	</TorrentTable>
</DownloadDialogWrapper>
