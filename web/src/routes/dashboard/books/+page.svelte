<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import MediaPicture from '$lib/components/media-picture.svelte';
	import { resolve } from '$app/paths';
	import LoadingBar from '$lib/components/loading-bar.svelte';
	import client from '$lib/api';

	let authors = $state(loadAuthors());

	async function loadAuthors() {
		const { data } = await client.GET('/api/v1/books/authors');
		return data ?? [];
	}
</script>

<svelte:head>
	<title>Books - MediaManager</title>
	<meta content="Browse and manage your book collection in MediaManager" name="description" />
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
					<Breadcrumb.Page>Books</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
<main class="flex w-full flex-1 flex-col gap-4 p-4 pt-0">
	<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">Books</h1>
	{#await authors}
		<LoadingBar />
	{:then authorList}
		<div
			class="grid w-full auto-rows-min gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
		>
			{#each authorList as author (author.id)}
				<a href={resolve('/dashboard/books/[authorId]', { authorId: author.id })}>
					<Card.Root class="col-span-full max-w-[90vw] ">
						<Card.Header>
							<Card.Title class="h-6 truncate">{author.name}</Card.Title>
							<Card.Description class="truncate">{author.overview}</Card.Description>
						</Card.Header>
						<Card.Content>
							<MediaPicture media={author} />
						</Card.Content>
					</Card.Root>
				</a>
			{:else}
				<div class="col-span-full text-center text-muted-foreground">No authors added yet.</div>
			{/each}
		</div>
	{/await}
</main>
