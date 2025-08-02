<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Command from '$lib/components/ui/command/index.js';
	import * as Popover from '$lib/components/ui/popover/index.js';
	import { cn } from '$lib/utils.js';
	import { tick } from 'svelte';
	import { CheckIcon, ChevronsUpDownIcon } from 'lucide-svelte';
	import type { LibraryItem, PublicMovie, PublicShow } from '$lib/types.js';
	import { onMount } from 'svelte';
	import { env } from '$env/dynamic/public';
	import { toast } from 'svelte-sonner';

	const apiUrl = env.PUBLIC_API_URL;

	let {
		media,
		mediaType
	}: {
		media: PublicShow | PublicMovie;
		mediaType: 'tv' | 'movie';
	} = $props();

	let open = $state(false);
	let value = $derived(media.library === '' ? 'Default' : media.library);
	let libraries = $state<LibraryItem[]>([]);
	let triggerRef = $state<HTMLButtonElement>(null!);
	const selectedLabel = $derived<string>(
		libraries.find((item) => item.name === value)?.name ?? 'Default'
	);
	onMount(async () => {
		const endpoint = mediaType === 'tv' ? '/tv/shows/libraries' : '/movies/libraries';
		try {
			const response = await fetch(apiUrl + endpoint, {
				credentials: 'include'
			});
			if (response.ok) {
				libraries = await response.json();
				if (!value && libraries.length > 0) {
					value = 'Default';
				}
				libraries.push({
					name: 'Default',
					path: 'Default'
				});
			} else {
				toast.error('Failed to load libraries.');
			}
		} catch (error) {
			toast.error('Error fetching libraries.');
			console.error(error);
		}
	});

	async function handleSelect() {
		open = false;
		await tick();
		triggerRef.focus();

		const endpoint =
			mediaType === 'tv' ? `/tv/shows/${media.id}/library` : `/movies/${media.id}/library`;
		const urlParams = new URLSearchParams();
		urlParams.append('library', selectedLabel);
		const urlString = `${apiUrl}${endpoint}?${urlParams.toString()}`;
		try {
			const response = await fetch(urlString, {
				method: 'POST',
				credentials: 'include'
			});
			if (response.ok) {
				toast.success(`Library updated to ${selectedLabel}`);
				media.library = selectedLabel;
			} else {
				const errorText = await response.text();
				toast.error(`Failed to update library: ${errorText}`);
			}
		} catch (error) {
			toast.error('Error updating library.');
			console.error(error);
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
				{'Select Library'}
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
