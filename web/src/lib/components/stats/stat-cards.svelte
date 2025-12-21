<script lang="ts">
	import Card from '$lib/components/stats/card.svelte';
	import { getContext, onMount } from 'svelte';
	import client from '$lib/api';
	import { isSemver, semverIsGreater } from '$lib/utils.ts';
	import { resolve } from '$app/paths';
	import AnimatedCard from '$lib/components/stats/animated-card.svelte';
	let { showCount, moviesCount }: { showCount: number; moviesCount: number } = $props();
    import { PUBLIC_VERSION } from '$env/static/public';

	let episodeCount: Promise<number> = $state(
		client.GET('/api/v1/tv/episodes/count').then((res) => {
			return Number(res.data ?? 0);
		})
	);
	let torrentCount: Promise<number> = $state(
		client.GET('/api/v1/torrent').then((res) => {
			return res.data?.length ?? 0;
		})
	);

	let installedVersion: string | undefined = PUBLIC_VERSION.replace(/v*/, '');
	let releaseUrl: string | null = $state(null);
	let newestVersion: string | null = $state(null);

	let importablesShows: () => [] = getContext('importableShows');
	let importablesMovies: () => [] = getContext('importableMovies');

	onMount(async () => {
		let releases = await fetch('https://api.github.com/repos/maxdorninger/mediamanager/releases');
		if (releases.ok) {
			let latestRelease = await releases.json().then((x) => x[0]);
			newestVersion = latestRelease.tag_name.toString().replace(/v*/, '');
			releaseUrl = latestRelease.html_url;
		}
	});
</script>

<div class="flex flex-wrap gap-2">
	<div class="flex-auto">
		<AnimatedCard title="TV Shows" footer="Total count of downloaded episodes" number={showCount}
		></AnimatedCard>
	</div>
	<div class="flex-auto">
		{#await episodeCount then episodes}
			<AnimatedCard title="Episodes" footer="Total count of downloaded episodes" number={episodes}
			></AnimatedCard>
		{/await}
	</div>
	<div class="flex-auto">
		<AnimatedCard title="Movies" footer="Total count of movies" number={moviesCount}></AnimatedCard>
	</div>
	<div class="flex-auto">
		{#await torrentCount then torrent}
			<AnimatedCard title="Torrents" footer="Total count of torrents/NZBs" number={torrent}
			></AnimatedCard>
		{/await}
	</div>
	{#if importablesShows().length > 0}
		<div class="flex-auto">
			<Card title="Detected TV shows!" footer="Count of detected TV shows ready to import">
				<a rel="external" target="_blank" href={resolve('/dashboard/tv/', {})} class="underline">
					{importablesShows().length}
				</a>
			</Card>
		</div>
	{/if}
	{#if importablesMovies().length > 0}
		<div class="flex-auto">
			<Card title="Detected movies!" footer="Count of detected movies ready to import">
				<a
					rel="external"
					target="_blank"
					href={resolve('/dashboard/movies/', {})}
					class="underline"
				>
					{importablesMovies().length}
				</a>
			</Card>
		</div>
	{/if}
	<div class="flex-auto">
		{#if semverIsGreater(newestVersion ?? '', installedVersion ?? '') || !isSemver(installedVersion ?? '')}
			<Card title="New version available!" footer="A new version of MediaManager is available!">
				<a
					rel="external"
					target="_blank"
					href={releaseUrl ?? 'https://github.com/maxdorninger/MediaManager/releases'}
					class="underline"
				>
					{isSemver(installedVersion ?? '') ? 'v' : ''}{installedVersion} → v{newestVersion}
				</a>
			</Card>
		{/if}
	</div>
</div>
