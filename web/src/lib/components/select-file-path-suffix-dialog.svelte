<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import FilePathSuffixSelector from '$lib/components/file-path-suffix-selector.svelte';
	import type { components } from '$lib/api/api';

	let {
		filePathSuffix = $bindable(),
		media,
		callback
	}: {
		filePathSuffix: string;
		media: components['schemas']['Movie'] | components['schemas']['Show'];
		callback: () => void;
	} = $props();
	let dialogOpen = $state(false);

	function onDownload() {
		callback();
		dialogOpen = false;
	}
</script>

<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Trigger>
		<Button class="w-full" onclick={() => (dialogOpen = true)}>Download</Button>
	</Dialog.Trigger>
	<Dialog.Content class="w-full max-w-[600px] rounded-lg p-6 shadow-lg">
		<Dialog.Header>
			<Dialog.Title class="mb-1 text-xl font-semibold">Set File Path Suffix</Dialog.Title>
			<Dialog.Description class="mb-4 text-sm">
				Set the filepath suffix for downloaded files of the torrent.
			</Dialog.Description>
		</Dialog.Header>
		<FilePathSuffixSelector bind:filePathSuffix {media} />
		<div class="mt-8 flex justify-between gap-2">
			<Button onclick={() => (dialogOpen = false)} variant="secondary">Cancel</Button>
			<Button onclick={() => onDownload()}>Download Torrent</Button>
		</div>
	</Dialog.Content>
</Dialog.Root>
