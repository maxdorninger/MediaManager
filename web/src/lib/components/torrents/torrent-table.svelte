<script lang="ts">
	import {
		convertTorrentSeasonRangeToIntegerRange,
		convertTorrentEpisodeRangeToIntegerRange,
		getTorrentQualityString,
		getTorrentStatusString
	} from '$lib/utils.js';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import * as Table from '$lib/components/ui/table';
	import type { components } from '$lib/api/api';
	import { getContext } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import client from '$lib/api';
	import { toast } from 'svelte-sonner';
	import DeleteTorrentDialog from '$lib/components/torrents/delete-torrent-dialog.svelte';
	import EditTorrentDialog from '$lib/components/torrents/edit-torrent-dialog.svelte';
	import { invalidateAll } from '$app/navigation';
	import { resolve } from '$app/paths';
	let {
		torrents,
		isShow = true,
		showId,
		movieId
	}: {
		torrents:
			| components['schemas']['MovieTorrent'][]
			| components['schemas']['RichSeasonTorrent'][];
		isShow: boolean;
		showId?: string;
		movieId?: string;
	} = $props();

	let user: () => components['schemas']['UserRead'] = getContext('user');

	async function retryTorrentDownload(
		torrent: components['schemas']['MovieTorrent'] | components['schemas']['RichSeasonTorrent']
	) {
		console.log(`Retrying download for torrent ${torrent.torrent_title}`);
		const { error } = await client.POST('/api/v1/torrent/{torrent_id}/retry', {
			params: {
				path: {
					torrent_id: torrent.torrent_id!
				}
			}
		});
		if (error) {
			toast.error(`Failed on retrying download: ${error}`);
		} else {
			console.log(`Successfully retried download for torrent ${torrent.torrent_title}`);
			toast.success('Trying to download torrent...');
		}
		await invalidateAll();
	}
</script>

<Table.Root>
	<Table.Caption>A list of all torrents.</Table.Caption>
	<Table.Header>
		<Table.Row>
			<Table.Head>Name</Table.Head>
			{#if isShow}
				<Table.Head>Seasons</Table.Head>
				<Table.Head>Episodes</Table.Head>
			{/if}
			<Table.Head>Download Status</Table.Head>
			<Table.Head>Quality</Table.Head>
			<Table.Head>File Path Suffix</Table.Head>
			<Table.Head>Imported</Table.Head>
			{#if user().is_superuser}
				<Table.Head>Actions</Table.Head>
			{/if}
		</Table.Row>
	</Table.Header>
	<Table.Body>
		{#each torrents as torrent (torrent.torrent_id)}
			<Table.Row>
				<Table.Cell class="font-medium">
					{#if isShow && showId}
						<a
							href={resolve('/dashboard/tv/[showId]', { showId })}
							class="text-primary hover:underline"
						>
							{torrent.torrent_title}
						</a>
					{:else if !isShow && movieId}
						<a
							href={resolve('/dashboard/movies/[movieId]', { movieId })}
							class="text-primary hover:underline"
						>
							{torrent.torrent_title}
						</a>
					{:else}
						{torrent.torrent_title}
					{/if}
				</Table.Cell>
				{#if isShow}
					<Table.Cell>
						{convertTorrentSeasonRangeToIntegerRange(
							(torrent as components['schemas']['RichSeasonTorrent']).seasons!
						)}
					</Table.Cell>
					<Table.Cell>
						{convertTorrentEpisodeRangeToIntegerRange(
							(torrent as components['schemas']['RichSeasonTorrent']).episodes!
						)}
					</Table.Cell>
				{/if}
				<Table.Cell>
					{getTorrentStatusString(torrent.status)}
				</Table.Cell>
				<Table.Cell class="font-medium">
					{getTorrentQualityString(torrent.quality)}
				</Table.Cell>
				<Table.Cell>
					{torrent.file_path_suffix}
				</Table.Cell>
				<Table.Cell>
					<CheckmarkX state={torrent.imported} />
				</Table.Cell>
				{#if user().is_superuser}
					<Table.Cell class="flex flex-col justify-center gap-2 xl:flex-row">
						{#if 'finished' !== getTorrentStatusString(torrent.status)}
							<Button variant="secondary" onclick={() => retryTorrentDownload(torrent)}>
								Retry Download
							</Button>
						{/if}
						<DeleteTorrentDialog torrentName={torrent.torrent_title} torrentId={torrent.torrent_id!}
						></DeleteTorrentDialog>
						<EditTorrentDialog {torrent} />
					</Table.Cell>
				{/if}
			</Table.Row>
		{/each}
	</Table.Body>
</Table.Root>
