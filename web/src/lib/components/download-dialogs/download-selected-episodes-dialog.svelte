<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import { formatSecondsToOptimalUnit } from '$lib/utils';
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
		selectedEpisodeNumbers,
		triggerText = 'Download Episodes'
	}: {
		show: components['schemas']['Show'];
		selectedEpisodeNumbers: { seasonNumber: number; episodeNumber: number }[];
		triggerText?: string;
	} = $props();

	let dialogueState = $state(false);
	let torrentsPromise: any = $state();
	let isLoading: boolean = $state(false);
	let filePathSuffix: string = $state('');
	let torrentsError: string | null = $state(null);

	const tableColumnHeadings = [
		{ name: 'Size', id: 'size' },
		{ name: 'Usenet', id: 'usenet' },
		{ name: 'Seeders', id: 'seeders' },
		{ name: 'Age', id: 'age' },
		{ name: 'Score', id: 'score' },
		{ name: 'Indexer', id: 'indexer' },
		{ name: 'Indexer Flags', id: 'flags' }
	];

    function torrentMatchesSelectedEpisodes(
        torrentTitle: string,
        selectedEpisodes: { seasonNumber: number; episodeNumber: number }[]
    ) {
        const normalizedTitle = torrentTitle.toLowerCase();

        return selectedEpisodes.some((ep) => {
            const s = String(ep.seasonNumber).padStart(2, '0');
            const e = String(ep.episodeNumber).padStart(2, '0');

            const patterns = [
                `s${s}e${e}`,
                `${s}x${e}`,
                `season ${ep.seasonNumber} episode ${ep.episodeNumber}`
            ];

            return patterns.some((pattern) =>
                normalizedTitle.includes(pattern)
            );
        });
    }

	async function search() {
        if (!selectedEpisodeNumbers || selectedEpisodeNumbers.length === 0) {
            toast.error('No episodes selected.');
            return;
        }

        isLoading = true;

        torrentsPromise = Promise.all(
            selectedEpisodeNumbers.map((ep) =>
                client
                    .GET('/api/v1/tv/torrents', {
                        params: {
                            query: {
                                show_id: show.id!,
                                season_number: ep.seasonNumber,
                                episode_number: ep.episodeNumber
                            }
                        }
                    })
                    .then((r) => r?.data ?? [])
            )
        )
            .then((results) => results.flat())
            .then((allTorrents) =>
                allTorrents.filter((torrent) =>
                    torrentMatchesSelectedEpisodes(
                        torrent.title,
                        selectedEpisodeNumbers
                    )
                )
            )
            .finally(() => (isLoading = false));

        await torrentsPromise;
    }

	async function downloadTorrent(result_id: string) {
		const { response } = await client.POST('/api/v1/tv/torrents', {
			params: {
				query: {
					show_id: show.id!,
					public_indexer_result_id: result_id,
					override_file_path_suffix:
						filePathSuffix === '' ? undefined : filePathSuffix
				}
			}
		});

		if (!response.ok) {
			toast.error('Download failed.');
		} else {
			toast.success('Download started.');
		}

		await invalidateAll();
	}
</script>

<DownloadDialogWrapper
	bind:open={dialogueState}
	triggerText={triggerText}
	title="Download Selected Episodes"
	description="Search and download torrents for selected episodes."
>
	<div class="flex flex-col gap-3">
		<p class="text-sm text-muted-foreground">
			Selected episodes:
			<strong>
				{selectedEpisodeNumbers.length > 0
					? selectedEpisodeNumbers.map(e => `S${String(e.seasonNumber).padStart(2, '0')}E${String(e.episodeNumber).padStart(2, '0')}`).join(', ')
					: 'None'}
			</strong>
		</p>

        <Button
            class="w-fit"
            disabled={isLoading || selectedEpisodeNumbers.length === 0}
            onclick={search}
        >
            Search Torrents
        </Button>
    </div>

	<TorrentTable {torrentsPromise} columns={tableColumnHeadings}>
		{#snippet rowSnippet(torrent)}
			<Table.Cell>{torrent.title}</Table.Cell>
			<Table.Cell>
				{(torrent.size / 1024 / 1024 / 1024).toFixed(2)}GB
			</Table.Cell>
			<Table.Cell>{torrent.usenet}</Table.Cell>
			<Table.Cell>{torrent.usenet ? 'N/A' : torrent.seeders}</Table.Cell>
			<Table.Cell>
				{torrent.age
					? formatSecondsToOptimalUnit(torrent.age)
					: torrent.usenet
						? 'N/A'
						: ''}
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
