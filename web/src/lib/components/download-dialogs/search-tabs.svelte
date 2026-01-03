<script lang="ts">
	import * as Tabs from '$lib/components/ui/tabs';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { type Snippet } from 'svelte';

	let {
		tabState = $bindable(),
		isLoading,
		queryOverride = $bindable(),
		onSearch,
		basicModeContent,
		advancedModeHelpText
	}: {
		tabState: string;
		isLoading: boolean;
		queryOverride: string;
		onSearch: () => void;
		basicModeContent: Snippet;
		advancedModeHelpText: string;
	} = $props();
</script>

<Tabs.Root class="w-full" bind:value={tabState}>
	<Tabs.List>
		<Tabs.Trigger value="basic">Standard Mode</Tabs.Trigger>
		<Tabs.Trigger value="advanced">Advanced Mode</Tabs.Trigger>
	</Tabs.List>
	<Tabs.Content value="basic">
		<div class="grid w-full items-center gap-1.5">
			{@render basicModeContent()}
		</div>
	</Tabs.Content>
	<Tabs.Content value="advanced">
		<div class="grid w-full items-center gap-1.5">
			<Label for="query-override">Enter a custom query</Label>
			<div class="flex w-full max-w-sm items-center space-x-2">
				<Input bind:value={queryOverride} id="query-override" type="text" />
				<Button disabled={isLoading} class="w-fit" onclick={onSearch}>Search for Torrents</Button>
			</div>
			<p class="text-sm text-muted-foreground">
				{advancedModeHelpText}
			</p>
		</div>
	</Tabs.Content>
</Tabs.Root>
