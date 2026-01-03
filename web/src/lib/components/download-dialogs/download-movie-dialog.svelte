<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import { Badge } from '$lib/components/ui/badge';

	import * as Table from '$lib/components/ui/table';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import SelectFilePathSuffixDialog from '$lib/components/download-dialogs/select-file-path-suffix-dialog.svelte';
	import { invalidateAll } from '$app/navigation';
	import TorrentTable from '$lib/components/download-dialogs/torrent-table.svelte';
	import SearchTabs from '$lib/components/download-dialogs/search-tabs.svelte';
	import DownloadDialogWrapper from '$lib/components/download-dialogs/download-dialog-wrapper.svelte';

	let { movie }: { movie: components['schemas']['Movie'] } = $props();
	let dialogueState = $state(false);
	let torrentsError: string | null = $state(null);
	let queryOverride: string = $state('');
	let filePathSuffix: string = $state('');

	let torrentsPromise: any = $state(null);
	let torrentsData: any[] | null = $state(null);
	let tabState: string = $state('basic');
	let isLoading: boolean = $state(false);

	let advancedMode: boolean = $derived(tabState === 'advanced');

	const tableColumnHeadings = [
		{ name: 'Size', id: 'size' },
		{ name: 'Seeders', id: 'seeders' },
		{ name: 'Score', id: 'score' },
		{ name: 'Indexer', id: 'indexer' },
		{ name: 'Indexer Flags', id: 'flags' }
	];

	async function downloadTorrent(result_id: string) {
		torrentsError = null;
		const { data, response } = await client.POST(`/api/v1/movies/{movie_id}/torrents`, {
			params: {
				path: {
					movie_id: movie.id!
				},
				query: {
					public_indexer_result_id: result_id,
					override_file_path_suffix: filePathSuffix === '' ? undefined : filePathSuffix
				}
			}
		});
		if (response.status === 409) {
			const errorMessage = `There already is a Movie File using the Filepath Suffix '${filePathSuffix}'. Try again with a different Filepath Suffix.`;
			console.warn(errorMessage);
			torrentsError = errorMessage;
			if (dialogueState) toast.info(errorMessage);
		} else if (!response.ok) {
			const errorMessage = `Failed to download torrent for movie ${movie.id}: ${response.statusText}`;
			console.error(errorMessage);
			torrentsError = errorMessage;
			toast.error(errorMessage);
		} else {
			console.log('Downloading torrent:', data);
			toast.success('Torrent download started successfully!');
		}
		await invalidateAll();
	}

	async function search() {
		isLoading = true;
		torrentsError = null;
		torrentsData = null;
		torrentsPromise = client
			.GET('/api/v1/movies/{movie_id}/torrents', {
				params: {
					query: {
						search_query_override: advancedMode ? queryOverride : undefined
					},
					path: {
						movie_id: movie.id!
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
	triggerText="Download Movie"
	title="Download a Movie"
	description="Search and download torrents for a specific season or season packs."
>
	<SearchTabs
		bind:tabState
		{isLoading}
		bind:queryOverride
		onSearch={search}
		advancedModeHelpText="The custom query will override the default search string like 'A Minecraft Movie (2025)'."
	>
		{#snippet basicModeContent()}
			<Button disabled={isLoading} class="w-fit" onclick={search}>Search for Torrents</Button>
		{/snippet}
	</SearchTabs>
	{#if torrentsError}
		<div class="my-2 w-full text-center text-red-500">An error occurred: {torrentsError}</div>
	{/if}
	<TorrentTable {torrentsPromise} columns={tableColumnHeadings}>
		{#snippet rowSnippet(torrent)}
			<Table.Cell class="max-w-[300px] font-medium">{torrent.title}</Table.Cell>
			<Table.Cell>{(torrent.size / 1024 / 1024 / 1024).toFixed(2)}GB</Table.Cell>
			<Table.Cell>{torrent.seeders}</Table.Cell>
			<Table.Cell>{torrent.score}</Table.Cell>
			<Table.Cell>{torrent.indexer ?? 'Unknown'}</Table.Cell>
			<Table.Cell>
				{#each torrent.flags as flag (flag)}
					<Badge variant="outline">{flag}</Badge>
				{/each}
			</Table.Cell>
			<Table.Cell class="text-right">
				<SelectFilePathSuffixDialog
					media={movie}
					bind:filePathSuffix
					callback={() => downloadTorrent(torrent.id)}
				/>
			</Table.Cell>
		{/snippet}
	</TorrentTable>
</DownloadDialogWrapper>
