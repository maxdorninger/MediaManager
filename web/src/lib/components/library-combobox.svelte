<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Command from '$lib/components/ui/command/index.js';
	import * as Popover from '$lib/components/ui/popover/index.js';
	import { cn } from '$lib/utils.js';
	import { tick } from 'svelte';
	import { CheckIcon, ChevronsUpDownIcon } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';

	let {
		media,
		mediaType
	}: {
		media: components['schemas']['PublicShow'] | components['schemas']['PublicMovie'];
		mediaType: 'tv' | 'movie';
	} = $props();

	let open = $state(false);
	let value = $derived(media.library === '' ? 'Default' : media.library);
	let libraries: components['schemas']['LibraryItem'][] = $state([]);
	let triggerRef: HTMLButtonElement = $state(null!);
	const selectedLabel: string = $derived(
		libraries.find((item) => item.name === value)?.name ?? 'Default'
	);
	onMount(async () => {
		const tvLibraries = await client.GET('/api/v1/tv/shows/libraries');
		const movieLibraries = await client.GET('/api/v1/movies/libraries');

		if (mediaType === 'tv') {
			libraries = tvLibraries.data as components['schemas']['LibraryItem'][];
		} else {
			libraries = movieLibraries.data as components['schemas']['LibraryItem'][];
		}

		if (!value && libraries.length > 0) {
			value = 'Default';
		}
		libraries.push({
			name: 'Default',
			path: 'Default'
		} as components['schemas']['LibraryItem']);
	});

	async function handleSelect() {
		open = false;
		await tick();
		triggerRef.focus();
		let response;
		if (mediaType === 'tv') {
			response = await client.POST('/api/v1/tv/shows/{show_id}/library', {
				params: {
					path: { show_id: media.id! },
					query: { library: selectedLabel }
				}
			});
		} else {
			response = await client.POST('/api/v1/movies/{movie_id}/library', {
				params: {
					path: { movie_id: media.id! },
					query: { library: selectedLabel }
				}
			});
		}
		if (response.error) {
			toast.error('Failed to update library');
		} else {
			toast.success(`Library updated to ${selectedLabel}`);
			media.library = selectedLabel;
		}
	}

	function closeAndFocusTrigger() {
		open = false;
		tick().then(() => {
			triggerRef.focus();
		});
	}
</script>

<Popover.Root bind:open>
	<Popover.Trigger bind:ref={triggerRef}>
		{#snippet child({ props })}
			<Button
				{...props}
				variant="outline"
				class="w-[200px] justify-between"
				role="combobox"
				aria-expanded={open}
			>
				Select Library
				<ChevronsUpDownIcon class="opacity-50" />
			</Button>
		{/snippet}
	</Popover.Trigger>
	<Popover.Content class="w-[200px] p-0">
		<Command.Root>
			<Command.Input placeholder="Search library..." />
			<Command.List>
				<Command.Empty>No library found.</Command.Empty>
				<Command.Group value="libraries">
					{#each libraries as item (item.name)}
						<Command.Item
							value={item.name}
							onSelect={() => {
								value = item.name;
								handleSelect();
								closeAndFocusTrigger();
							}}
						>
							<CheckIcon class={cn(value !== item.name && 'text-transparent')} />
							{item.name}
						</Command.Item>
					{/each}
				</Command.Group>
			</Command.List>
		</Command.Root>
	</Popover.Content>
</Popover.Root>
