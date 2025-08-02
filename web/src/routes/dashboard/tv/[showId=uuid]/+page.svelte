<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { goto } from '$app/navigation';
	import { ImageOff } from 'lucide-svelte';
	import * as Table from '$lib/components/ui/table/index.js';
	import { getContext } from 'svelte';
	import type { PublicShow, RichShowTorrent, User } from '$lib/types.js';
	import { getFullyQualifiedMediaName } from '$lib/utils';
	import DownloadSeasonDialog from '$lib/components/download-season-dialog.svelte';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import { page } from '$app/state';
	import TorrentTable from '$lib/components/torrent-table.svelte';
	import RequestSeasonDialog from '$lib/components/request-season-dialog.svelte';
	import MediaPicture from '$lib/components/media-picture.svelte';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { toast } from 'svelte-sonner';
	import { Label } from '$lib/components/ui/label';
	import LibraryCombobox from '$lib/components/library-combobox.svelte';
	import * as Card from '$lib/components/ui/card/index.js';

	const apiUrl = env.PUBLIC_API_URL;
	let show: () => PublicShow = getContext('show');
	let user: () => User = getContext('user');
	let torrents: RichShowTorrent = page.data.torrentsData;
	import { base } from '$app/paths';

	let continuousDownloadEnabled = $state(show().continuous_download);

	async function toggle_continuous_download() {
		const urlString = `${apiUrl}/tv/shows/${show().id}/continuousDownload?continuous_download=${!continuousDownloadEnabled}`;
		console.log(
			'Toggling continuous download for show',
			show().name,
			'to',
			!continuousDownloadEnabled
		);
		const response = await fetch(urlString, {
			method: 'POST',
			credentials: 'include'
		});
		if (!response.ok) {
			const errorText = await response.text();
			toast.error('Failed to toggle continuous download: ' + errorText);
		} else {
			continuousDownloadEnabled = !continuousDownloadEnabled;
			toast.success('Continuous download toggled successfully.');
		}
	}

	/*	$effect(()=>{
        continuousDownloadEnabled;
        toggle_continuous_download();
    });*/
</script>

<svelte:head>
	<title>{getFullyQualifiedMediaName(show())} - MediaManager</title>
	<meta
		content="View details and manage downloads for {getFullyQualifiedMediaName(
			show()
		)} in MediaManager"
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
					<Breadcrumb.Link href="{base}/dashboard">MediaManager</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href="{base}/dashboard">Home</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href="{base}/dashboard/tv">Shows</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>{getFullyQualifiedMediaName(show())}</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>
<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
	{getFullyQualifiedMediaName(show())}
</h1>
<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<div class="flex flex-col gap-4 md:flex-row md:items-stretch">
		<div class="w-full overflow-hidden rounded-xl bg-muted/50 md:w-1/3 md:max-w-sm">
			{#if show().id}
				<MediaPicture media={show()} />
			{:else}
				<div
					class="aspect-9/16 flex h-auto w-full items-center justify-center rounded-lg bg-gray-200 text-gray-500"
				>
					<ImageOff size={48} />
				</div>
			{/if}
		</div>
		<div class="h-full w-full flex-auto rounded-xl md:w-1/4">
			<Card.Root class="h-full w-full">
				<Card.Header>
					<Card.Title>Overview</Card.Title>
				</Card.Header>
				<Card.Content>
					<p class="leading-7 not-first:mt-6">
						{show().overview}
					</p>
				</Card.Content>
			</Card.Root>
		</div>
		<div
			class="flex h-full w-full flex-auto flex-col items-center justify-start gap-4 rounded-xl md:w-1/3 md:max-w-[40em]"
		>
			{#if user().is_superuser}
				<Card.Root class="w-full  flex-1">
					<Card.Header>
						<Card.Title>Administrator Controls</Card.Title>
					</Card.Header>
					<Card.Content class="flex flex-col items-center gap-4">
						{#if !show().ended}
							<div class="flex items-center gap-3">
								<Switch
									bind:checked={() => continuousDownloadEnabled, toggle_continuous_download}
									id="continuous-download-checkbox"
								/>
								<Label for="continuous-download-checkbox">
									Enable automatic download of future seasons
								</Label>
							</div>
						{/if}
						<LibraryCombobox media={show()} mediaType="tv" />
					</Card.Content>
				</Card.Root>
			{/if}
			<Card.Root class="w-full  flex-1">
				<Card.Header>
					<Card.Title>Download Options</Card.Title>
				</Card.Header>
				<Card.Content class="flex flex-col items-center gap-4">
					{#if user().is_superuser}
						<DownloadSeasonDialog show={show()} />
					{/if}
					<RequestSeasonDialog show={show()} />
				</Card.Content>
			</Card.Root>
		</div>
	</div>
	<div class="flex-1 rounded-xl">
		<Card.Root class="w-full">
			<Card.Header>
				<Card.Title>Season Details</Card.Title>
				<Card.Description>
					A list of all seasons for {getFullyQualifiedMediaName(show())}.
				</Card.Description>
			</Card.Header>
			<Card.Content class="w-full overflow-x-auto">
				<Table.Root>
					<Table.Caption>A list of all seasons.</Table.Caption>
					<Table.Header>
						<Table.Row>
							<Table.Head>Number</Table.Head>
							<Table.Head>Exists on file</Table.Head>
							<Table.Head>Title</Table.Head>
							<Table.Head>Overview</Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#if show().seasons.length > 0}
							{#each show().seasons as season (season.id)}
								<Table.Row
									link={true}
									onclick={() => goto(base + '/dashboard/tv/' + show().id + '/' + season.id)}
								>
									<Table.Cell class="min-w-[10px] font-medium">{season.number}</Table.Cell>
									<Table.Cell class="min-w-[10px] font-medium">
										<CheckmarkX state={season.downloaded} />
									</Table.Cell>
									<Table.Cell class="min-w-[50px]">{season.name}</Table.Cell>
									<Table.Cell class="max-w-[300px] truncate">{season.overview}</Table.Cell>
								</Table.Row>
							{/each}
						{:else}
							<Table.Row>
								<Table.Cell colspan={3} class="text-center">No season data available.</Table.Cell>
							</Table.Row>
						{/if}
					</Table.Body>
				</Table.Root>
			</Card.Content>
		</Card.Root>
	</div>
	<div class="flex-1 rounded-xl">
		<Card.Root>
			<Card.Header>
				<Card.Title>Torrent Information</Card.Title>
				<Card.Description>A list of all torrents associated with this show.</Card.Description>
			</Card.Header>

			<Card.Content class="w-full overflow-x-auto">
				<TorrentTable torrents={torrents.torrents} />
			</Card.Content>
		</Card.Root>
	</div>
</main>
