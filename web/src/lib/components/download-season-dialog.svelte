<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { toast } from 'svelte-sonner';

	import type { PublicIndexerQueryResult } from '$lib/types.js';
	import {
		convertTorrentSeasonRangeToIntegerRange,
		formatSecondsToOptimalUnit,
		getFullyQualifiedMediaName
	} from '$lib/utils';
	import { LoaderCircle } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge';

	const apiUrl = env.PUBLIC_API_URL;
	let { show } = $props();
	let dialogueState = $state(false);
	let selectedSeasonNumber: number = $state(1);
	let torrents: PublicIndexerQueryResult[] = $state([]);
	let isLoadingTorrents: boolean = $state(false);
	let torrentsError: string | null = $state(null);
	let queryOverride: string = $state('');
	let filePathSuffix: string = $state('');

	async function downloadTorrent(result_id: string) {
		const urlParams = new URLSearchParams();
		urlParams.append('public_indexer_result_id', result_id);
		urlParams.append('show_id', show.id);
		if (filePathSuffix !== '') {
			urlParams.append('override_file_path_suffix', filePathSuffix);
		}
		const urlString = `${apiUrl}/tv/torrents?${urlParams.toString()}`;
		try {
			const response = await fetch(urlString, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include'
			});

			if (response.status === 409) {
				const errorMessage = `There already is a Season File using the Filepath Suffix '${filePathSuffix}'. Try again with a different Filepath Suffix.`;
				console.warn(errorMessage);
				torrentsError = errorMessage;
				if (dialogueState) toast.info(errorMessage);
				return [];
			}

			if (!response.ok && response.status !== 409) {
				const errorMessage = `Failed to download torrent for show ${show.id} and season ${selectedSeasonNumber}: ${response.statusText}`;
				console.error(errorMessage);
				torrentsError = errorMessage;
				toast.error(errorMessage);
				return false;
			}

			const data: PublicIndexerQueryResult[] = await response.json();
			console.log('Downloading torrent:', data);
			toast.success('Torrent download started successfully!');

			return true;
		} catch (err) {
			const errorMessage = `Error downloading torrent: ${err instanceof Error ? err.message : 'An unknown error occurred'}`;
			console.error(errorMessage);
			toast.error(errorMessage);
			return false;
		}
	}

	async function getTorrents(
		season_number: number,
		override: boolean = false
	): Promise<PublicIndexerQueryResult[]> {
		isLoadingTorrents = true;
		torrentsError = null;
		torrents = [];

		const urlParams = new URLSearchParams();
		urlParams.append('show_id', show.id);
		if (override) {
			urlParams.append('search_query_override', queryOverride);
		} else {
			urlParams.append('season_number', season_number.toString());
		}
		const urlString = `${apiUrl}/tv/torrents?${urlParams.toString()}`;

		try {
			const response = await fetch(urlString, {
				method: 'GET',
				credentials: 'include'
			});

			if (!response.ok) {
				const errorMessage = `Failed to fetch torrents for show ${show.id} and season ${selectedSeasonNumber}: ${response.statusText}`;
				console.error(errorMessage);
				torrentsError = errorMessage;
				if (dialogueState) toast.error(errorMessage);
				return [];
			}

			const data: PublicIndexerQueryResult[] = await response.json();
			console.log('Fetched torrents:', data);
			if (dialogueState) {
				if (data.length > 0) {
					toast.success(`Found ${data.length} torrents.`);
				} else {
					toast.info('No torrents found for your query.');
				}
			}
			return data;
		} catch (err) {
			const errorMessage = `Error fetching torrents: ${err instanceof Error ? err.message : 'An unknown error occurred'}`;
			console.error(errorMessage);
			torrentsError = errorMessage;
			if (dialogueState) toast.error(errorMessage);
			return [];
		} finally {
			isLoadingTorrents = false;
		}
	}

</script>

{#snippet saveDirectoryPreview(
	show: { name: string; metadata_provider: string; external_id: number; year: number | null },
	filePathSuffix: string
)}
	/{getFullyQualifiedMediaName(show)} [{show.metadata_provider}id-{show.external_id}]/ Season XX/{show.name}
	SXXEXX {filePathSuffix === '' ? '' : ' - ' + filePathSuffix}.mkv
{/snippet}

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
					{#if show?.seasons?.length > 0}
						<Label for="season-number"
						>Enter a season number from 1 to {show.seasons.at(-1).number}</Label
						>
						<div class="flex w-full max-w-sm items-center space-x-2">
							<Input
								type="number"
								class="max-w-sm"
								id="season-number"
								bind:value={selectedSeasonNumber}
								max={show.seasons.at(-1).number}
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
						<p class="text-sm text-muted-foreground">
							Enter the season's number you want to search for. The first, usually 1, or the last
							season number usually yield the most season packs. Note that only Seasons which are
							listed in the "Seasons" cell will be imported!
						</p>
						<Label for="file-suffix">Filepath suffix</Label>
						<Select.Root type="single" bind:value={filePathSuffix}>
							<Select.Trigger class="w-[180px]">{filePathSuffix}</Select.Trigger>
							<Select.Content>
								<Select.Item value="">None</Select.Item>
								<Select.Item value="2160P">2160p</Select.Item>
								<Select.Item value="1080P">1080p</Select.Item>
								<Select.Item value="720P">720p</Select.Item>
								<Select.Item value="480P">480p</Select.Item>
								<Select.Item value="360P">360p</Select.Item>
							</Select.Content>
						</Select.Root>
						<p class="text-sm text-muted-foreground">
							This is necessary to differentiate between versions of the same season/show, for
							example a 1080p and a 4K version of a season.
						</p>
						<Label for="file-suffix-display"
							>The files will be saved in the following directory:</Label
						>
						<p class="text-sm text-muted-foreground" id="file-suffix-display">
							{@render saveDirectoryPreview(show, filePathSuffix)}
						</p>
					{:else}
						<p class="text-sm text-muted-foreground">
							No season information available for this show.
						</p>
					{/if}
				</div>
			</Tabs.Content>
			<Tabs.Content value="advanced">
				<div class="grid w-full items-center gap-1.5">
					{#if show?.seasons?.length > 0}
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
						<p class="text-sm text-muted-foreground">
							The custom query will override the default search string like "The Simpsons Season 3".
							Note that only Seasons which are listed in the "Seasons" cell will be imported!
						</p>
						<Label for="file-suffix">Filepath suffix</Label>
						<Input
							type="text"
							class="max-w-sm"
							id="file-suffix"
							bind:value={filePathSuffix}
							placeholder="1080P"
						/>
						<p class="text-sm text-muted-foreground">
							This is necessary to differentiate between versions of the same season/show, for
							example a 1080p and a 4K version of a season.
						</p>

						<Label for="file-suffix-display"
							>The files will be saved in the following directory:</Label
						>
						<p class="text-sm text-muted-foreground" id="file-suffix-display">
							{@render saveDirectoryPreview(show, filePathSuffix)}
						</p>
					{:else}
						<p class="text-sm text-muted-foreground">
							No season information available for this show.
						</p>
					{/if}
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
										>{torrent.usenet ? formatSecondsToOptimalUnit(torrent.age) : 'N/A'}</Table.Cell
									>
									<Table.Cell>{torrent.score}</Table.Cell>
									<Table.Cell>
										{#each torrent.flags as flag}
											<Badge variant="outline">{flag}</Badge>
										{/each}
									</Table.Cell>
									<Table.Cell>
										{convertTorrentSeasonRangeToIntegerRange(torrent)}
									</Table.Cell>
									<Table.Cell class="text-right">
										<Button
											size="sm"
											variant="outline"
											onclick={() => {
												downloadTorrent(torrent.id);
											}}
										>
											Download
										</Button>
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
