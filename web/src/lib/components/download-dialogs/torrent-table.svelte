<script lang="ts">
	import { ArrowDown, ArrowUp, LoaderCircle } from 'lucide-svelte';
	import * as Table from '$lib/components/ui/table';
	import { type Snippet } from 'svelte';

	let {
		torrentsPromise,
		columns,
		rowSnippet
	}: {
		torrentsPromise: Promise<any>;
		columns: { name: string; id: string }[];
		rowSnippet: Snippet<[any]>;
	} = $props();

	let sortBy = $state({ col: 'score', ascending: false });

	function getSortedColumnState(column: string | undefined): boolean | null {
		if (sortBy.col !== column) return null;
		return sortBy.ascending;
	}

	function toggleSort(column: string) {
		if (column === sortBy.col) {
			sortBy.ascending = !sortBy.ascending;
		} else {
			sortBy = { col: column, ascending: true };
		}
	}
	function sort(data: any[], column: string, ascending: boolean): any[] {
		let modifier = ascending ? 1 : -1;
		return [...data].sort((a, b) => {
			if (a[column] < b[column]) {
				return -1 * modifier;
			} else if (a[column] > b[column]) {
				return modifier;
			} else {
				return 0;
			}
		});
	}
</script>

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
						{#each columns as column (column.id)}
							<Table.Head onclick={() => toggleSort(column.id)} class="cursor-pointer">
								<div class="inline-flex items-center">
									{column.name}
									{#if getSortedColumnState(column.id) === true}
										<ArrowUp />
									{:else if getSortedColumnState(column.id) === false}
										<ArrowDown />
									{:else}
										<!-- Preserve layout (column width) when no sort is applied -->
										<ArrowUp class="invisible"></ArrowUp>
									{/if}
								</div>
							</Table.Head>
						{/each}
						<Table.Head class="text-right">Actions</Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#if data}
						{@const sortedData = sort(data, sortBy.col, sortBy.ascending)}
						{#each sortedData as torrent (torrent.id)}
							<Table.Row>
								{@render rowSnippet(torrent)}
							</Table.Row>
						{:else}
							<Table.Cell colspan={columns.length + 2}>
								<div class="font-light text-center w-full">No torrents found.</div>
							</Table.Cell>
						{/each}
					{:else}
						<Table.Cell colspan={columns.length + 2}>
							<div class="w-full text-center font-light">
								Start searching by clicking the search button!
							</div>
						</Table.Cell>
					{/if}
				</Table.Body>
			</Table.Root>
		</div>
	{:catch error}
		<div class="w-full text-center text-red-500">Failed to load torrents.</div>
		<div class="w-full text-center text-red-500">Error: {error.message}</div>
	{/await}
</div>
