<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { page } from '$app/state';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import { resolve } from '$app/paths';
	import type { components } from '$lib/api/api';
	import { getContext } from 'svelte';
	import DownloadBookDialog from '$lib/components/download-dialogs/download-book-dialog.svelte';
	import RequestBookDialog from '$lib/components/requests/request-book-dialog.svelte';

	let author: components['schemas']['PublicAuthor'] = $derived(page.data.authorData);
	let book: components['schemas']['Book'] = $derived(page.data.book);
	let bookFiles: components['schemas']['PublicBookFile'][] = $derived(page.data.bookFiles);
	let user: () => components['schemas']['UserRead'] = getContext('user');
</script>

<svelte:head>
	<title>{book.name} - {author.name} - MediaManager</title>
	<meta
		content="View details for book {book.name} by {author.name} in MediaManager"
		name="description"
	/>
</svelte:head>

<header class="flex h-16 shrink-0 items-center gap-2">
	<div class="flex items-center gap-2 px-4">
		<Sidebar.Trigger class="-ml-1" />
		<Separator class="mr-2 h-4" orientation="vertical" />
		<Breadcrumb.Root>
			<Breadcrumb.List>
				<Breadcrumb.Item class="hidden md:block">
					<Breadcrumb.Link href={resolve('/dashboard', {})}>MediaManager</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href={resolve('/dashboard', {})}>Home</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href={resolve('/dashboard/books', {})}>Books</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href={resolve('/dashboard/books/[authorId]', { authorId: author.id })}>
						{author.name}
					</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>{book.name}</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
	{book.name}
</h1>
<p class="text-center text-muted-foreground">
	{author.name}
	{#if book.year}
		&middot; {book.year}
	{/if}
	&middot; <span class="capitalize">{book.format}</span>
</p>
<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<div class="flex flex-col gap-4 md:flex-row md:items-stretch">
		<div class="w-full flex-1 rounded-xl">
			<Card.Root class="h-full w-full">
				<Card.Header>
					<Card.Title>Download Options</Card.Title>
				</Card.Header>
				<Card.Content class="flex flex-col items-center gap-4">
					{#if user().is_superuser}
						<DownloadBookDialog {author} {book} />
					{/if}
					<RequestBookDialog {author} {book} />
				</Card.Content>
			</Card.Root>
		</div>
		<div class="w-full flex-1 rounded-xl">
			<Card.Root class="h-full w-full">
				<Card.Header>
					<Card.Title>Book Files</Card.Title>
					<Card.Description>Downloaded/downloading versions of this book.</Card.Description>
				</Card.Header>
				<Card.Content>
					<Table.Root>
						<Table.Caption>
							A list of all downloaded/downloading versions of this book.
						</Table.Caption>
						<Table.Header>
							<Table.Row>
								<Table.Head>File Path Suffix</Table.Head>
								<Table.Head>Downloaded</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#if bookFiles && bookFiles.length > 0}
								{#each bookFiles as file (file)}
									<Table.Row>
										<Table.Cell class="w-[100px]">
											{file.file_path_suffix}
										</Table.Cell>
										<Table.Cell class="w-[10px] font-medium">
											<CheckmarkX state={file.downloaded} />
										</Table.Cell>
									</Table.Row>
								{/each}
							{:else}
								<Table.Row>
									<Table.Cell colspan={2} class="text-center">No book files yet.</Table.Cell>
								</Table.Row>
							{/if}
						</Table.Body>
					</Table.Root>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
</main>
