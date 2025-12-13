<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { toast } from 'svelte-sonner';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import CacheStatusBadge from '$lib/components/cache-status-badge.svelte';

	import { LoaderCircle } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import client from '$lib/api';
	import SelectFilePathSuffixDialog from '$lib/components/select-file-path-suffix-dialog.svelte';

	let { movie } = $props();
	let dialogueState = $state(false);
	let torrentsPromise: any = $state();
	let tabState: string = $state('basic');
	let isLoading: boolean = $state(false);
	let advancedMode: boolean = $derived(tabState === 'advanced');
	let queryOverride: string = $state('');
	let filePathSuffix: string = $state('');
	let torrentsError: string | null = $state(null);
	let hasDebrid: boolean = $state(false);

	// Check if debrid is configured on mount
	$effect(() => {
		client.GET('/api/v1/debrid/provider').then(({ data }) => {
			hasDebrid = data?.is_implemented ?? false;
		}).catch(() => {
			hasDebrid = false;
		});
	});

	async function downloadTorrent(result_id: string) {
		torrentsError = null;
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

	async function search() {
		isLoading = true;
		torrentsError = null;
		torrentsPromise = client
			.GET('/api/v1/movies/{movie_id}/torrents', {
				params: {
					query: {
						search_query_override: advancedMode ? queryOverride : undefined
					},
					path: {
						movie_id: movie.id
					}
				}
			})
			.finally(() => (isLoading = false));
		toast.info('Searching for torrents...');
		toast.info('Found ' + (await torrentsPromise).data?.length + ' torrents.');
	}
</script>

<Dialog.Root bind:open={dialogueState} onOpenChange={() => (dialogueState ? search() : null)}>
	<Dialog.Trigger class={buttonVariants({ variant: 'default' })}>Download Movie</Dialog.Trigger>
	<Dialog.Content class="max-h-[90vh] w-fit min-w-[80vw] overflow-y-auto">
		<Dialog.Header>
			<Dialog.Title>Download a Movie</Dialog.Title>
			<Dialog.Description>
				Search and download torrents for a specific season or season packs.
			</Dialog.Description>
		</Dialog.Header>
		<Tabs.Root class="w-full" bind:value={tabState}>
			<Tabs.List>
				<Tabs.Trigger value="basic">Standard Mode</Tabs.Trigger>
				<Tabs.Trigger value="advanced">Advanced Mode</Tabs.Trigger>
			</Tabs.List>
			<Tabs.Content value="basic">
				<div class="grid w-full items-center gap-1.5">
					<Button
						disabled={isLoading}
						class="w-fit"
						onclick={() => {
							search();
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
							disabled={isLoading}
							class="w-fit"
							onclick={() => {
								search();
							}}
						>
							Search for Torrents
						</Button>
					</div>
					<p class="text-sm text-muted-foreground">
						The custom query will override the default search string like "A Minecraft Movie
						(2025)".
					</p>
				</div>
			</Tabs.Content>
		</Tabs.Root>
		{#if torrentsError}
			<div class="my-2 w-full text-center text-red-500">An error occurred: {torrentsError}</div>
		{/if}
		<div class="mt-4 items-center">
			{#await torrentsPromise}
				<div class="flex w-full max-w-sm items-center space-x-2">
					<LoaderCircle class="animate-spin" />
					<p>Loading torrents...</p>
				</div>
			{:then data}
				<h3 class="mb-2 text-lg font-semibold">Found Torrents:</h3>
				<div class="overflow-y-auto rounded-md border p-2">
					<Table.Root>
						<Table.Header>
							<Table.Row>
								<Table.Head>Title</Table.Head>
								<Table.Head>Size</Table.Head>
								<Table.Head>Seeders</Table.Head>
								{#if hasDebrid}
									<Table.Head>Cache</Table.Head>
								{/if}
								<Table.Head>Score</Table.Head>
								<Table.Head>Indexer</Table.Head>
								<Table.Head>Indexer Flags</Table.Head>
								<Table.Head class="text-right">Actions</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each data?.data as torrent (torrent.id)}
								<Table.Row>
									<Table.Cell class="max-w-[300px] font-medium">{torrent.title}</Table.Cell>
									<Table.Cell>{(torrent.size / 1024 / 1024 / 1024).toFixed(2)}GB</Table.Cell>
									<Table.Cell>{torrent.seeders}</Table.Cell>
									{#if hasDebrid}
										<Table.Cell>
											<CacheStatusBadge infoHash={torrent.info_hash} />
										</Table.Cell>
									{/if}
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
							{:else}
								<Table.Cell colspan={hasDebrid ? 8 : 7}>
									<div class="font-light text-center w-full">No torrents found.</div>
								</Table.Cell>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>
			{:catch error}
				<div class="w-full text-center text-red-500">Failed to load torrents.</div>
				<div class="w-full text-center text-red-500">Error: {error.message}</div>
			{/await}
		</div>
	</Dialog.Content>
</Dialog.Root>