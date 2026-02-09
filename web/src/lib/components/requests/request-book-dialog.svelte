<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import { toast } from 'svelte-sonner';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';
	import { invalidateAll } from '$app/navigation';

	let {
		author,
		book
	}: {
		author: components['schemas']['PublicAuthor'];
		book: components['schemas']['Book'];
	} = $props();

	let dialogOpen = $state(false);
	let isSubmittingRequest = $state(false);
	let submitRequestError = $state<string | null>(null);

	async function handleRequestBook() {
		isSubmittingRequest = true;
		submitRequestError = null;
		const { response } = await client.POST('/api/v1/books/books/requests', {
			body: {
				book_id: book.id!,
				min_quality: 0 as components['schemas']['Quality'],
				wanted_quality: 0 as components['schemas']['Quality']
			}
		});
		isSubmittingRequest = false;

		if (response.ok) {
			dialogOpen = false;
			toast.success('Book request submitted successfully!');
		} else {
			toast.error('Failed to submit request');
		}
		await invalidateAll();
	}
</script>

<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Trigger
		class={buttonVariants({ variant: 'default' })}
		onclick={() => {
			dialogOpen = true;
		}}
	>
		Request Book
	</Dialog.Trigger>
	<Dialog.Content class="max-h-[90vh] w-fit min-w-[clamp(300px,50vw,600px)] overflow-y-auto">
		<Dialog.Header>
			<Dialog.Title>Request {book.name}</Dialog.Title>
			<Dialog.Description>
				Request a download of {book.name} by {author.name}.
			</Dialog.Description>
		</Dialog.Header>
		<div class="grid gap-4 py-4">
			<p class="text-sm text-muted-foreground">
				This will submit a request to download this book. An administrator will need to approve it
				before it is automatically downloaded.
			</p>
			{#if submitRequestError}
				<p class="col-span-full text-center text-sm text-red-500">{submitRequestError}</p>
			{/if}
		</div>
		<Dialog.Footer>
			<Button disabled={isSubmittingRequest} onclick={() => (dialogOpen = false)} variant="outline"
				>Cancel
			</Button>
			<Button disabled={isSubmittingRequest} onclick={handleRequestBook}>
				{#if isSubmittingRequest}
					<LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
					Submitting...
				{:else}
					Submit Request
				{/if}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
