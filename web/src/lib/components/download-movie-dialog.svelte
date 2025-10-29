<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { toast } from 'svelte-sonner';
	import { Badge } from '$lib/components/ui/badge/index.js';

	import { LoaderCircle } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import SelectFilePathSuffixDialog from '$lib/components/select-file-path-suffix-dialog.svelte';
	let { movie } = $props();
	let dialogueState = $state(false);
	let torrents: components['schemas']['IndexerQueryResult'][] = $state([]);
	let isLoadingTorrents: boolean = $state(false);
	let torrentsError: string | null = $state(null);
	let queryOverride: string = $state('');
	let filePathSuffix: string = $state('');

	async function downloadTorrent(result_id: string) {
		const { data, response } = await client.POST(`/api/v1/movies/{movie_id}/torrents`, {
			params: {
				path: {
					movie_id: movie.id
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
			return [];
		} else if (!response.ok) {
			const errorMessage = `Failed to download torrent for movie ${movie.id}: ${response.statusText}`;
			console.error(errorMessage);
			torrentsError = errorMessage;
			toast.error(errorMessage);
			return false;
		} else {
			console.log('Downloading torrent:', data);
			toast.success('Torrent download started successfully!');

			return true;
		}
	}

	async function getTorrents(
		override: boolean = false
	): Promise<components['schemas']['IndexerQueryResult'][]> {
		isLoadingTorrents = true;
		torrentsError = null;
		torrents = [];
		let { response, data } = await client.GET('/api/v1/movies/{movie_id}/torrents', {
			params: {
				query: {
					search_query_override: override ? queryOverride : undefined
				},
				path: {
					movie_id: movie.id
				}
			}
		});
		data = data as components['schemas']['IndexerQueryResult'][];
		isLoadingTorrents = false;

		if (!response.ok) {
			const errorMessage = `Failed to fetch torrents for movie ${movie.id}: ${response.statusText}`;
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
		if (movie?.id) {
			getTorrents().then((fetchedTorrents) => {
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
	<Dialog.Trigger class={buttonVariants({ variant: 'default' })}>Download Movie</Dialog.Trigger>
	<Dialog.Content class="max-h-[90vh] w-fit min-w-[80vw] overflow-y-auto">
		<Dialog.Header>
			<Dialog.Title>Download a Movie</Dialog.Title>
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
					<Button
						class="w-fit"
						variant="secondary"
						onclick={async () => {
							isLoadingTorrents = true;
							torrentsError = null;
							torrents = [];
							try {
								torrents = await getTorrents();
							} catch (error) {
								console.log(error);
							} finally {
								isLoadingTorrents = false;
							}
						}}
					>
						Search for Torrents
					</Button>
				</div>
			</Tabs.Content>
			<Tabs.Content value="advanced">
				<div class="grid w-full items-center gap-1.5">
					<Label for="query-override">Enter a custom query</Label>
					<div class="flex w-full max-w-sm items-center space-x-2">
						<Input bind:value={queryOverride} id="query-override" type="text" />
						<Button
							onclick={async () => {
								isLoadingTorrents = true;
								torrentsError = null;
								torrents = [];
								try {
									torrents = await getTorrents(true);
								} catch (error) {
									console.log(error);
								} finally {
									isLoadingTorrents = false;
								}
							}}
							variant="secondary"
						>
							Search
						</Button>
					</div>
					<p class="text-muted-foreground text-sm">
						The custom query will override the default search string like "A Minecraft Movie
						(2025)".
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
								<Table.Head>Seeders</Table.Head>
								<Table.Head>Score</Table.Head>
								<Table.Head>Indexer</Table.Head>
								<Table.Head>Indexer Flags</Table.Head>
								<Table.Head class="text-right">Actions</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each torrents as torrent (torrent.id)}
								<Table.Row>
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
											callback={() => downloadTorrent(torrent.id!)}
										/>
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>
			{:else}
				<p>No torrents found!</p>
			{/if}
		</div>
	</Dialog.Content>
</Dialog.Root>
