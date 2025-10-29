<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { toast } from 'svelte-sonner';
	import { convertTorrentSeasonRangeToIntegerRange, formatSecondsToOptimalUnit } from '$lib/utils';
	import { LoaderCircle } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import SelectFilePathSuffixDialog from '$lib/components/select-file-path-suffix-dialog.svelte';

	let { show }: { show: components['schemas']['Show'] } = $props();
	let dialogueState = $state(false);
	let selectedSeasonNumber: number = $state(1);
	let torrents: components['schemas']['IndexerQueryResult'][] = $state([]);
	let isLoadingTorrents: boolean = $state(false);
	let torrentsError: string | null = $state(null);
	let queryOverride: string = $state('');
	let filePathSuffix: string = $state('');

	async function downloadTorrent(result_id: string) {
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
			return false;
		} else if (!response.ok) {
			const errorMessage = `Failed to download torrent for show ${show.id} and season ${selectedSeasonNumber}: ${response.statusText}`;
			console.error(errorMessage);
			torrentsError = errorMessage;
			toast.error(errorMessage);
			return false;
		} else {
			toast.success('Torrent download started successfully!');
			return true;
		}
	}

	async function getTorrents(
		season_number: number,
		override: boolean = false
	): Promise<components['schemas']['IndexerQueryResult'][]> {
		isLoadingTorrents = true;
		torrentsError = null;
		torrents = [];

		let { response, data } = await client.GET('/api/v1/tv/torrents', {
			params: {
				query: {
					show_id: show.id!,
					search_query_override: override ? queryOverride : undefined,
					season_number: override ? undefined : season_number
				}
			}
		});
		data = data as components['schemas']['IndexerQueryResult'][];
		isLoadingTorrents = false;

		if (!response.ok) {
			const errorMessage = `Failed to fetch torrents for show ${show.id} and season ${selectedSeasonNumber}: ${response.statusText}`;
			torrentsError = errorMessage;
			if (dialogueState) toast.error(errorMessage);
			return [];
		}

		if (dialogueState) {
			if (data.length > 0) {
				toast.success(`Found ${data.length} torrents.`);
			} else {
				toast.info('No torrents found for your query.');
			}
		}
		return data;
	}
	$effect(() => {
		if (show?.id) {
			getTorrents(selectedSeasonNumber).then((fetchedTorrents) => {
				if (!isLoadingTorrents) {
					torrents = fetchedTorrents;
				} else if (fetchedTorrents.length > 0 || torrentsError) {
					torrents = fetchedTorrents;
				}
			});
		}
	});
</script>

<Dialog.Root bind:open={dialogueState}>
	<Dialog.Trigger class={buttonVariants({ variant: 'default' })}>Download Seasons</Dialog.Trigger>
	<Dialog.Content class="max-h-[90vh] w-fit min-w-[80vw] overflow-y-auto">
		<Dialog.Header>
			<Dialog.Title>Download a Season</Dialog.Title>
			<Dialog.Description>
				Search and download torrents for a specific season or season packs.
			</Dialog.Description>
		</Dialog.Header>
		<Tabs.Root class="w-full" value="basic">
			<Tabs.List>
				<Tabs.Trigger value="basic">Standard Mode</Tabs.Trigger>
				<Tabs.Trigger value="advanced">Advanced Mode</Tabs.Trigger>
			</Tabs.List>
			<Tabs.Content value="basic">
				<div class="grid w-full items-center gap-1.5">
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
						<Button
							variant="secondary"
							onclick={async () => {
								isLoadingTorrents = true;
								torrentsError = null;
								torrents = [];
								try {
									torrents = await getTorrents(selectedSeasonNumber, false);
								} catch (error) {
									console.log(error);
								} finally {
									isLoadingTorrents = false;
								}
							}}
						>
							Search
						</Button>
					</div>
					<p class="text-muted-foreground text-sm">
						Enter the season's number you want to search for. The first, usually 1, or the last
						season number usually yield the most season packs. Note that only Seasons which are
						listed in the "Seasons" cell will be imported!
					</p>
				</div>
			</Tabs.Content>
			<Tabs.Content value="advanced">
				<div class="grid w-full items-center gap-1.5">
					<Label for="query-override">Enter a custom query</Label>
					<div class="flex w-full max-w-sm items-center space-x-2">
						<Input type="text" id="query-override" bind:value={queryOverride} />
						<Button
							variant="secondary"
							onclick={async () => {
								isLoadingTorrents = true;
								torrentsError = null;
								torrents = [];
								try {
									torrents = await getTorrents(selectedSeasonNumber, true);
								} catch (error) {
									console.log(error);
								} finally {
									isLoadingTorrents = false;
								}
							}}
						>
							Search
						</Button>
					</div>
					<p class="text-muted-foreground text-sm">
						The custom query will override the default search string like "The Simpsons Season 3".
						Note that only Seasons which are listed in the "Seasons" cell will be imported!
					</p>
				</div>
			</Tabs.Content>
		</Tabs.Root>
		<div class="mt-4 items-center">
			{#if isLoadingTorrents}
				<div class="flex w-full max-w-sm items-center space-x-2">
					<LoaderCircle class="animate-spin" />
					<p>Loading torrents...</p>
				</div>
			{:else if torrentsError}
				<p class="text-red-500">Error: {torrentsError}</p>
			{:else if torrents.length > 0}
				<h3 class="mb-2 text-lg font-semibold">Found Torrents:</h3>
				<div class="overflow-y-auto rounded-md border p-2">
					<Table.Root>
						<Table.Header>
							<Table.Row>
								<Table.Head>Title</Table.Head>
								<Table.Head>Size</Table.Head>
								<Table.Head>Usenet</Table.Head>
								<Table.Head>Seeders</Table.Head>
								<Table.Head>Age</Table.Head>
								<Table.Head>Score</Table.Head>
								<Table.Head>Indexer</Table.Head>
								<Table.Head>Indexer Flags</Table.Head>
								<Table.Head>Seasons</Table.Head>
								<Table.Head class="text-right">Actions</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each torrents as torrent (torrent.id)}
								<Table.Row>
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
											callback={() => downloadTorrent(torrent.id!)}
										/>
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>
			{:else if show?.seasons?.length > 0}
				<p>No torrents found for season {selectedSeasonNumber}. Try a different season.</p>
			{/if}
		</div>
	</Dialog.Content>
</Dialog.Root>
