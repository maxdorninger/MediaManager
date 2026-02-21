<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
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
	import { getFullyQualifiedMediaName } from '$lib/utils';

	let { show }: { show: components['schemas']['Show'] } = $props();

	let dialogueState = $state(false);
	let torrentsError: string | null = $state(null);
	let queryOverride: string = $state('');
	let filePathSuffix: string = $state('');

	let torrentsPromise: any = $state();
	let torrentsData: any[] | null = $state(null);
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
			const errorMessage = `There already is a File using the Filepath Suffix '${filePathSuffix}'. Try again with a different Filepath Suffix.`;
			console.warn(errorMessage);
			torrentsError = errorMessage;
			if (dialogueState) toast.info(errorMessage);
		} else if (!response.ok) {
			const errorMessage = `Failed to download torrent for show ${show.id}: ${response.statusText}`;
			console.error(errorMessage);
			torrentsError = errorMessage;
			toast.error(errorMessage);
		} else {
			toast.success('Torrent download started successfully!');
		}

		await invalidateAll();
	}

	async function search() {
		if (!queryOverride || queryOverride.trim() === '') {
			toast.error('Please enter a custom query.');
			return;
		}

		isLoading = true;
		torrentsError = null;
		torrentsData = null;

		torrentsPromise = client
			.GET('/api/v1/tv/torrents', {
				params: {
					query: {
						show_id: show.id!,
						search_query_override: queryOverride
					}
				}
			})
			.then((data) => data?.data)
			.finally(() => (isLoading = false));

		toast.info('Searching for torrents...');

		torrentsData = await torrentsPromise;

		if (!torrentsData || torrentsData.length === 0) {
			toast.info('No torrents found.');
		} else {
			toast.success(`Found ${torrentsData.length} torrents.`);
		}
	}
</script>

<DownloadDialogWrapper
	bind:open={dialogueState}
	triggerText="Custom Download"
	title="Custom Torrent Download"
	description="Search and download torrents using a fully custom query string."
>
	<div class="grid w-full items-center gap-1.5">
		<Label for="query-override">Enter a custom query</Label>

		<div class="flex w-full max-w-sm items-center space-x-2">
			<Input
				bind:value={queryOverride}
				id="query-override"
				type="text"
				placeholder={`e.g. ${getFullyQualifiedMediaName(show)} S01 1080p BluRay`}
			/>
			<Button disabled={isLoading} class="w-fit" onclick={search}>Search</Button>
		</div>

		<p class="text-sm text-muted-foreground">
			The custom query completely overrides the default search logic. Make sure the torrent title
			matches the episodes you want imported.
		</p>
	</div>

	{#if torrentsError}
		<div class="my-2 w-full text-center text-red-500">
			An error occurred: {torrentsError}
		</div>
	{/if}

	<TorrentTable {torrentsPromise} columns={tableColumnHeadings}>
		{#snippet rowSnippet(torrent)}
			<Table.Cell class="font-medium">{torrent.title}</Table.Cell>
			<Table.Cell>{(torrent.size / 1024 / 1024 / 1024).toFixed(2)}GB</Table.Cell>
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
