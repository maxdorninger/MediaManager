<script lang="ts">
	import Card from '$lib/components/stats/card.svelte';
	import { onMount } from 'svelte';
	import client from '$lib/api';
	import { isSemver, semverIsGreater } from '$lib/utils.ts';
	import { env } from '$env/dynamic/public';
	import { resolve } from '$app/paths';

	let moviesCount: string | null = $state(null);
	let episodeCount: string | null = $state(null);
	let showCount: string | null = $state(null);
	let torrentCount: string | null = $state(null);
	let installedVersion: string | undefined = env.PUBLIC_VERSION;
	let releaseUrl: string | null = $state(null);
	let newestVersion: string | null = $state(null);

	onMount(async () => {
		let tvShows = await client.GET('/api/v1/tv/shows');
		if (!tvShows.error) showCount = tvShows.data.length.toString().padStart(3, '0');

		let episodes = await client.GET('/api/v1/tv/episodes/count');
		if (!episodes.error) episodeCount = episodes.data.toString().padStart(3, '0');

		let movies = await client.GET('/api/v1/movies');
		if (!movies.error) moviesCount = movies.data.length.toString().padStart(3, '0');

		let torrents = await client.GET('/api/v1/torrent');
		if (!torrents.error) torrentCount = torrents.data.length.toString().padStart(3, '0');

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
		<Card title="TV Shows" footer="Total count of downloaded episodes">{showCount ?? 'Error'}</Card>
	</div>
	<div class="flex-auto">
		<Card title="Episodes" footer="Total count of downloaded episodes"
			>{episodeCount ?? 'Error'}</Card
		>
	</div>
	<div class="flex-auto">
		<Card title="Movies" footer="Total count of movies">{moviesCount ?? 'Error'}</Card>
	</div>
	<div class="flex-auto">
		<Card title="Torrents" footer="Total count of torrents/NZBs">{torrentCount ?? 'Error'}</Card>
	</div>
	<div class="flex-auto">
		{#if semverIsGreater(newestVersion ?? '', installedVersion ?? '') || !isSemver(installedVersion ?? '')}
			<Card title="New version available!" footer="A new version of MediaManager is available!">
				<a
					target="_blank"
					href={resolve(releaseUrl ?? 'https://github.com/maxdorninger/MediaManager/releases')}
					class="underline"
				>
					{installedVersion} → v{newestVersion}
				</a>
			</Card>
		{/if}
	</div>
</div>
