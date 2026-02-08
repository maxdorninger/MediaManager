<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';

	import * as Table from '$lib/components/ui/table';
	import * as Dialog from '$lib/components/ui/dialog';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import { invalidateAll } from '$app/navigation';
	import TorrentTable from '$lib/components/download-dialogs/torrent-table.svelte';
	import SearchTabs from '$lib/components/download-dialogs/search-tabs.svelte';
	import DownloadDialogWrapper from '$lib/components/download-dialogs/download-dialog-wrapper.svelte';

	let {
		artist,
		album
	}: {
		artist: components['schemas']['PublicArtist'];
		album: components['schemas']['Album'];
	} = $props();

	let dialogueState = $state(false);
	let torrentsError: string | null = $state(null);
	let queryOverride: string = $state('');
	let filePathSuffix: string = $state('');

	let torrentsPromise: any = $state(null);
	let torrentsData: any[] | null = $state(null);
	let tabState: string = $state('basic');
	let isLoading: boolean = $state(false);

	let advancedMode: boolean = $derived(tabState === 'advanced');

	let suffixDialogOpen = $state(false);
	let pendingDownloadId: string | null = $state(null);

	const tableColumnHeadings = [
		{ name: 'Size', id: 'size' },
		{ name: 'Seeders', id: 'seeders' },
		{ name: 'Score', id: 'score' },
		{ name: 'Indexer', id: 'indexer' },
		{ name: 'Indexer Flags', id: 'flags' }
	];

	async function downloadTorrent(result_id: string) {
		torrentsError = null;
		const { data, response } = await client.POST('/api/v1/music/torrents', {
			params: {
				query: {
					public_indexer_result_id: result_id,
					artist_id: artist.id!,
					album_id: album.id!,
					override_file_path_suffix: filePathSuffix === '' ? undefined : filePathSuffix
				}
			}
		});
		if (response.status === 409) {
			const errorMessage = `There already is an Album File using the Filepath Suffix '${filePathSuffix}'. Try again with a different Filepath Suffix.`;
			console.warn(errorMessage);
			torrentsError = errorMessage;
			if (dialogueState) toast.info(errorMessage);
		} else if (!response.ok) {
			const errorMessage = `Failed to download torrent for album ${album.name}: ${response.statusText}`;
			console.error(errorMessage);
			torrentsError = errorMessage;
			toast.error(errorMessage);
		} else {
			console.log('Downloading torrent:', data);
			toast.success('Torrent download started successfully!');
		}
		await invalidateAll();
	}

	function openSuffixDialog(resultId: string) {
		pendingDownloadId = resultId;
		suffixDialogOpen = true;
	}

	function confirmDownload() {
		if (pendingDownloadId) {
			downloadTorrent(pendingDownloadId);
		}
		suffixDialogOpen = false;
		pendingDownloadId = null;
	}

	async function search() {
		isLoading = true;
		torrentsError = null;
		torrentsData = null;
		torrentsPromise = client
			.GET('/api/v1/music/torrents', {
				params: {
					query: {
						artist_id: artist.id!,
						album_name: album.name,
						search_query_override: advancedMode ? queryOverride : undefined
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
	triggerText="Download Album"
	title="Download an Album"
	description="Search and download torrents for {album.name} by {artist.name}."
>
	<SearchTabs
		bind:tabState
		{isLoading}
		bind:queryOverride
		onSearch={search}
		advancedModeHelpText="The custom query will override the default search string like '{artist.name} {album.name}'."
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
			<Table.Cell class="font-medium">{torrent.title}</Table.Cell>
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
				<Button class="w-full" onclick={() => openSuffixDialog(torrent.id)}>Download</Button>
			</Table.Cell>
		{/snippet}
	</TorrentTable>
</DownloadDialogWrapper>

<Dialog.Root bind:open={suffixDialogOpen}>
	<Dialog.Content class="w-full max-w-[600px] rounded-lg p-6 shadow-lg">
		<Dialog.Header>
			<Dialog.Title class="mb-1 text-xl font-semibold">Set File Path Suffix</Dialog.Title>
			<Dialog.Description class="mb-4 text-sm">
				Optional suffix to differentiate between versions of the same album (e.g. "FLAC", "320K").
			</Dialog.Description>
		</Dialog.Header>
		<div class="grid w-full items-center gap-1.5">
			<Label for="file-suffix">Filepath suffix (optional)</Label>
			<Input
				type="text"
				class="max-w-sm"
				id="file-suffix"
				bind:value={filePathSuffix}
				placeholder="FLAC"
			/>
		</div>
		<div class="mt-8 flex justify-between gap-2">
			<Button onclick={() => (suffixDialogOpen = false)} variant="secondary">Cancel</Button>
			<Button onclick={() => confirmDownload()}>Download Torrent</Button>
		</div>
	</Dialog.Content>
</Dialog.Root>
