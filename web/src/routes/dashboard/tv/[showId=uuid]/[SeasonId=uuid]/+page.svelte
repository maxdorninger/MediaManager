<script lang="ts">
	import { page } from '$app/state';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import type { components } from '$lib/api/api';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import { getFullyQualifiedMediaName, getTorrentQualityString } from '$lib/utils';
	import MediaPicture from '$lib/components/media-picture.svelte';
	import { resolve } from '$app/paths';
	import * as Card from '$lib/components/ui/card/index.js';

	let episodeFiles: components['schemas']['PublicEpisodeFile'][] = $derived(page.data.files);
	let season: components['schemas']['Season'] = $derived(page.data.season);
	let show: components['schemas']['Show'] = $derived(page.data.showData);

	let episodeById = $derived(
		Object.fromEntries(
			season.episodes.map((ep) => [
				ep.id,
				`E${String(ep.number).padStart(2, '0')}`
			])
		)
	);
</script>

<svelte:head>
	<title>{getFullyQualifiedMediaName(show)} - Season {season.number} - MediaManager</title>
	<meta
		content="View episodes and manage downloads for {getFullyQualifiedMediaName(
			show
		)} Season {season.number} in MediaManager"
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
					<Breadcrumb.Link href={resolve('/dashboard/tv', {})}>Shows</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href={resolve('/dashboard/tv/[showId]', { showId: show.id! })}>
						{show.name}
						{show.year == null ? '' : '(' + show.year + ')'}
					</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>Season {season.number}</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
	{getFullyQualifiedMediaName(show)} - Season {season.number}
</h1>
<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<div class="flex flex-col gap-4 md:flex-row md:items-stretch">
		<div class="w-full overflow-hidden rounded-xl bg-muted/50 md:w-1/3 md:max-w-sm">
			<MediaPicture media={show} />
		</div>
		<div class="h-full w-full flex-auto rounded-xl md:w-1/4">
			<Card.Root class="h-full w-full">
				<Card.Content class="flex flex-col gap-6">
					<div>
						<Card.Title class="text-base mb-2">
							Series Overview
						</Card.Title>
						<p class="text-sm leading-6 text-muted-foreground text-justify hyphens-auto">
							{show.overview}
						</p>
					</div>
					<div class="border-t border-border"></div>
					<div>
						<Card.Title class="text-base mb-2">
							Season Overview
						</Card.Title>
						<p class="text-sm leading-6 text-muted-foreground text-justify hyphens-auto">
							{season.overview}
						</p>
					</div>

				</Card.Content>
			</Card.Root>
		</div>
		<div
			class="flex h-full w-full flex-auto flex-col items-center justify-start gap-4 rounded-xl md:w-1/3 md:max-w-[40em]"
		>
			<Card.Root class="h-full w-full">
				<Card.Header>
					<Card.Title>Season Details</Card.Title>
					<Card.Description>
						A list of all downloaded/downloading versions of this season.
					</Card.Description>
				</Card.Header>
				<Card.Content>
					<Table.Root>
						<Table.Caption
							>A list of all downloaded/downloading versions of this season.</Table.Caption
						>
						<Table.Header>
							<Table.Row>
								<Table.Head>Episode</Table.Head>
								<Table.Head>Quality</Table.Head>
								<Table.Head>File Path Suffix</Table.Head>
								<Table.Head>Imported</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each episodeFiles as file (file)}
								<Table.Row>
									<Table.Cell class="w-[50px]">
										{episodeById[file.episode_id] ?? 'E??'}
									</Table.Cell>
									<Table.Cell class="w-[50px]">
										{getTorrentQualityString(file.quality)}
									</Table.Cell>
									<Table.Cell class="w-[100px]">
										{file.file_path_suffix}
									</Table.Cell>
									<Table.Cell class="w-[10px] font-medium">
										<CheckmarkX state={file.downloaded} />
									</Table.Cell>
								</Table.Row>
							{:else}
								<span class="font-semibold">You haven't downloaded this season yet.</span>
							{/each}
						</Table.Body>
					</Table.Root>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
	<div class="flex-1 rounded-xl">
		<Card.Root class="w-full">
			<Card.Header>
				<Card.Title>Episodes</Card.Title>
				<Card.Description
					>A list of all episodes for {getFullyQualifiedMediaName(show)} Season {season.number}
					.
				</Card.Description>
			</Card.Header>
			<Card.Content class="w-full overflow-x-auto">
				<Table.Root class="w-full table-fixed">
					<Table.Caption>A list of all episodes.</Table.Caption>
					<Table.Header>
						<Table.Row>
							<Table.Head class="w-[80px]">Number</Table.Head>
							<Table.Head class="w-[240px]">Title</Table.Head>
							<Table.Head>Overview</Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#each season.episodes as episode (episode.id)}
							<Table.Row>
								<Table.Cell class="w-[100px] font-medium">E{String(episode.number).padStart(2, '0')}</Table.Cell>
								<Table.Cell class="min-w-[50px]">{episode.title}</Table.Cell>
								<Table.Cell colspan={2} class="truncate">{episode.overview}</Table.Cell>
							</Table.Row>
						{/each}
					</Table.Body>
				</Table.Root>
			</Card.Content>
		</Card.Root>
	</div>
</main>
