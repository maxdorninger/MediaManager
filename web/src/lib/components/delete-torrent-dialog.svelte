<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label';
	import { toast } from 'svelte-sonner';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import client from '$lib/api';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { invalidateAll } from '$app/navigation';

	let { torrentId, torrentName }: { torrentId: string; torrentName: string } = $props();
	let dialogueState = $state(false);
	let deleteFiles = $state(false);

	async function deleteTorrent() {
		const { error } = await client.DELETE(`/api/v1/torrent/{torrent_id}`, {
			params: {
				path: {
					torrent_id: torrentId
				},
				query: {
					delete_files: deleteFiles
				}
			}
		});
		if (error) {
			toast.error(`Failed to delete torrent: ${error}`);
		} else {
			toast.success('Torrent deleted successfully!');
			dialogueState = false;
		}
		await invalidateAll();
	}
</script>

<Dialog.Root bind:open={dialogueState}>
	<Dialog.Trigger class={buttonVariants({ variant: 'destructive' })}>Delete Torrent</Dialog.Trigger>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>Delete a Torrent</Dialog.Title>
			<Dialog.Description>
				Delete Torrent "{torrentName}". This action cannot be undone!
			</Dialog.Description>
		</Dialog.Header>
		<div class="flex w-full max-w-sm items-center space-x-2">
			<Checkbox bind:checked={deleteFiles} id="delete-files" />
			<div class="flex flex-col">
				<Label for="delete-files">
					Delete associated files as well.
					<p class="text-muted-foreground text-sm font-normal">
						(Only files in the download location will be deleted)
					</p>
				</Label>
			</div>
		</div>

		<Dialog.Footer>
			<Button onclick={() => (dialogueState = false)}>Cancel</Button>
			<Button onclick={() => deleteTorrent()} variant="destructive">Delete Torrent</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
