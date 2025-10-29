<script lang="ts">
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { saveDirectoryPreview } from '$lib/utils.js';
	import type { components } from '$lib/api/api';
	import * as Tabs from '$lib/components/ui/tabs/index.js';

	import { Input } from '$lib/components/ui/input';
	let {
		media,
		filePathSuffix = $bindable()
	}: {
		media: components['schemas']['Movie'] | components['schemas']['Show'];
		filePathSuffix: string;
	} = $props();
</script>

{#snippet filePathPreview()}
	<p class="text-muted-foreground text-sm">
		This is necessary to differentiate between versions of the same movie or show, for example a
		1080p and a 4K version.
	</p>
	<Label for="file-suffix-display">The files will be saved in the following directory:</Label>
	<p class="text-muted-foreground text-sm" id="file-suffix-display">
		{saveDirectoryPreview(media, filePathSuffix)}
	</p>
{/snippet}

<Tabs.Root value="basic">
	<Tabs.List>
		<Tabs.Trigger value="basic">Standard Mode</Tabs.Trigger>
		<Tabs.Trigger value="advanced">Advanced Mode</Tabs.Trigger>
	</Tabs.List>
	<Tabs.Content value="basic">
		<div class="grid w-full items-center gap-1.5">
			<Label for="file-suffix">Filepath suffix</Label>
			<Select.Root bind:value={filePathSuffix} type="single">
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
			{@render filePathPreview()}
		</div>
	</Tabs.Content>
	<Tabs.Content value="advanced">
		<Label for="file-suffix">Filepath suffix</Label>
		<Input
			type="text"
			class="max-w-sm"
			id="file-suffix"
			bind:value={filePathSuffix}
			placeholder="1080P"
		/>
		{@render filePathPreview()}
	</Tabs.Content>
</Tabs.Root>
