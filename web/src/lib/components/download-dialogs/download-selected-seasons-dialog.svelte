<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import { formatSecondsToOptimalUnit } from '$lib/utils.ts';
	import * as Table from '$lib/components/ui/table';
	import { Badge } from '$lib/components/ui/badge';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import SelectFilePathSuffixDialog from '$lib/components/download-dialogs/select-file-path-suffix-dialog.svelte';
	import { invalidateAll } from '$app/navigation';
	import TorrentTable from '$lib/components/download-dialogs/torrent-table.svelte';
	import DownloadDialogWrapper from '$lib/components/download-dialogs/download-dialog-wrapper.svelte';

	let {
		show,
		selectedSeasonNumbers,
		triggerText = 'Download Selected Seasons'
	}: {
		show: components['schemas']['Show'];
		selectedSeasonNumbers: number[];
		triggerText?: string;
	} = $props();

	let dialogueState = $state(false);
	let torrentsError: string | null = $state(null);
	let filePathSuffix: string = $state('');
	let torrentsPromise: any = $state();
	let isLoading: boolean = $state(false);

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
			const errorMessage = `Filepath Suffix '${filePathSuffix}' already exists.`;
			torrentsError = errorMessage;
			toast.error(errorMessage);
		} else if (!response.ok) {
			const errorMessage = `Failed to download torrent: ${response.statusText}`;
			torrentsError = errorMessage;
			toast.error(errorMessage);
		} else {
			toast.success('Torrent download started successfully!');
		}

		await invalidateAll();
	}

	function isEpisodeRelease(title: string) {
		const lower = title.toLowerCase();

		const episodePatterns = [
			/s\d{1,2}e\d{1,2}/i,
			/\d{1,2}x\d{1,2}/i,
			/\be\d{1,2}\b/i,
			/e\d{1,2}-e?\d{1,2}/i,
			/vol\.?\s?\d+/i
		];

		return episodePatterns.some((regex) => regex.test(lower));
	}

	async function search() {
		if (!selectedSeasonNumbers || selectedSeasonNumbers.length === 0) {
			toast.error('No seasons selected.');
			return;
		}

		isLoading = true;
		torrentsError = null;

		toast.info(`Searching torrents for seasons: ${selectedSeasonNumbers.join(', ')}`);

		torrentsPromise = Promise.all(
			selectedSeasonNumbers.map((seasonNumber) =>
				client
					.GET('/api/v1/tv/torrents', {
						params: {
							query: {
								show_id: show.id!,
								season_number: seasonNumber
							}
						}
					})
					.then((data) => data?.data ?? [])
			)
		)
			.then((results) => results.flat())
			.then((allTorrents) => allTorrents.filter((torrent) => !isEpisodeRelease(torrent.title)))
			.finally(() => (isLoading = false));

		try {
			await torrentsPromise;
		} catch (error: any) {
			console.error(error);
			torrentsError = error.message || 'An error occurred while searching for torrents.';
			toast.error(torrentsError);
		}
	}
</script>

<DownloadDialogWrapper
	bind:open={dialogueState}
	{triggerText}
	title="Download Selected Seasons"
	description="Search and download torrents for the selected seasons."
>
	<div class="flex flex-col gap-3">
		<p class="text-sm text-muted-foreground">
			Selected seasons:
			<strong>
				{selectedSeasonNumbers.length > 0
					? selectedSeasonNumbers
							.slice()
							.sort((a, b) => a - b)
							.map((n) => `S${String(n).padStart(2, '0')}`)
							.join(', ')
					: 'None'}
			</strong>
		</p>

		<Button
			class="w-fit"
			disabled={isLoading || selectedSeasonNumbers.length === 0}
			onclick={search}
		>
			Search Torrents
		</Button>
	</div>

	{#if torrentsError}
		<div class="my-2 w-full text-center text-red-500">
			An error occurred: {torrentsError}
		</div>
	{/if}

	<TorrentTable {torrentsPromise} columns={tableColumnHeadings}>
		{#snippet rowSnippet(torrent)}
			<Table.Cell class="font-medium">{torrent.title}</Table.Cell>
			<Table.Cell>
				{(torrent.size / 1024 / 1024 / 1024).toFixed(2)}GB
			</Table.Cell>
			<Table.Cell>{torrent.usenet}</Table.Cell>
			<Table.Cell>{torrent.usenet ? 'N/A' : torrent.seeders}</Table.Cell>
			<Table.Cell>
				{torrent.age ? formatSecondsToOptimalUnit(torrent.age) : torrent.usenet ? 'N/A' : ''}
			</Table.Cell>
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
				{torrent.season ?? '-'}
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
