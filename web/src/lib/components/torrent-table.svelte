<script lang="ts">
	import {
		convertTorrentSeasonRangeToIntegerRange,
		getTorrentQualityString,
		getTorrentStatusString
	} from '$lib/utils.js';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import * as Table from '$lib/components/ui/table/index.js';

	let { torrents, isShow = true } = $props();
</script>

<Table.Root>
	<Table.Caption>A list of all torrents.</Table.Caption>
	<Table.Header>
		<Table.Row>
			<Table.Head>Name</Table.Head>
			{#if isShow}
				<Table.Head>Seasons</Table.Head>
			{/if}
			<Table.Head>Download Status</Table.Head>
			<Table.Head>Quality</Table.Head>
			<Table.Head>File Path Suffix</Table.Head>
			<Table.Head>Imported</Table.Head>
		</Table.Row>
	</Table.Header>
	<Table.Body>
		{#each torrents as torrent}
			<Table.Row>
				<Table.Cell class="font-medium">
					{torrent.torrent_title}
				</Table.Cell>
				{#if isShow}
					<Table.Cell>
						{convertTorrentSeasonRangeToIntegerRange(torrent)}
					</Table.Cell>
				{/if}
				<Table.Cell>
					{getTorrentStatusString(torrent.status)}
				</Table.Cell>
				<Table.Cell class="font-medium">
					{getTorrentQualityString(torrent.quality)}
				</Table.Cell>
				<Table.Cell class="font-medium">
					{torrent.file_path_suffix}
				</Table.Cell>
				<Table.Cell>
					<CheckmarkX state={torrent.imported} />
				</Table.Cell>
			</Table.Row>
		{/each}
	</Table.Body>
</Table.Root>
