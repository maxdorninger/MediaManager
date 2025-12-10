<script lang="ts">
	import Card from '$lib/components/stats/card.svelte';
	import { onMount } from 'svelte';
	import client from '$lib/api';
	import { isSemver, semverIsGreater } from '$lib/utils.ts';
	import { env } from '$env/dynamic/public';
	import { animate } from 'animejs';
	import { resolve } from '$app/paths';

	let moviesCount: string | null = $state(null);
	let episodeCount: string | null = $state(null);
	let showCount: string | null = $state(null);
	let torrentCount: string | null = $state(null);
	let installedVersion: string | undefined = env.PUBLIC_VERSION?.replace(/v*/, '');
	let releaseUrl: string | null = $state(null);
	let newestVersion: string | null = $state(null);

	let importablesShowsCount: number = $state(0);
	let importablesMoviesCount: number = $state(0);

	// Elements to animate
	let showEl: HTMLSpanElement;
	let episodeEl: HTMLSpanElement;
	let moviesEl: HTMLSpanElement;
	let torrentEl: HTMLSpanElement;

	function animateCounter(el: HTMLElement | undefined, target: number, pad = 3) {
		if (!el) return;

		const obj = { value: 0 };

		animate(obj, {
			value: target,
			duration: 2000,
			easing: 'easeInOutSine',
			onUpdate: () => {
				el.textContent = Math.floor(obj.value).toString().padStart(pad, '0');
			}
		});
	}

	onMount(async () => {
		let tvShows = await client.GET('/api/v1/tv/shows');
		if (!tvShows.error) {
			const target = tvShows.data.length;
			showCount = target.toString().padStart(3, '0');
			animateCounter(showEl, target, 3);
		}

		let episodes = await client.GET('/api/v1/tv/episodes/count');
		if (!episodes.error) {
			const target = Number(episodes.data);
			episodeCount = target.toString().padStart(3, '0');
			animateCounter(episodeEl, target, 3);
		}

		let movies = await client.GET('/api/v1/movies');
		if (!movies.error) {
			const target = movies.data.length;
			moviesCount = target.toString().padStart(3, '0');
			animateCounter(moviesEl, target, 3);
		}

		let torrents = await client.GET('/api/v1/torrent');
		if (!torrents.error) {
			const target = torrents.data.length;
			torrentCount = target.toString().padStart(3, '0');
			animateCounter(torrentEl, target, 3);
		}

		let releases = await fetch('https://api.github.com/repos/maxdorninger/mediamanager/releases');
		if (releases.ok) {
			let latestRelease = await releases.json().then((x) => x[0]);
			newestVersion = latestRelease.tag_name.toString().replace(/v*/, '');
			releaseUrl = latestRelease.html_url;
		}

		let importableShows = await client.GET('/api/v1/tv/importable');
		if (!importableShows.error) {
			importablesShowsCount = importableShows.data.length;
		}
		let importableMovies = await client.GET('/api/v1/movies/importable');
		if (!importableMovies.error) {
			importablesMoviesCount = importableMovies.data.length;
		}
	});
</script>

<div class="flex flex-wrap gap-2">
	<div class="flex-auto">
		<Card title="TV Shows" footer="Total count of downloaded episodes">
			<span bind:this={showEl}>{showCount ?? 'Error'}</span>
		</Card>
	</div>
	<div class="flex-auto">
		<Card title="Episodes" footer="Total count of downloaded episodes">
			<span bind:this={episodeEl}>{episodeCount ?? 'Error'}</span>
		</Card>
	</div>
	<div class="flex-auto">
		<Card title="Movies" footer="Total count of movies">
			<span bind:this={moviesEl}>{moviesCount ?? 'Error'}</span>
		</Card>
	</div>
	<div class="flex-auto">
		<Card title="Torrents" footer="Total count of torrents/NZBs">
			<span bind:this={torrentEl}>{torrentCount ?? 'Error'}</span>
		</Card>
	</div>
	{#if importablesShowsCount > 0}
		<div class="flex-auto">
			<Card title="Detected TV shows!" footer="Count of detected TV shows ready to import">
				<a rel="external" target="_blank" href={resolve('/dashboard/tv/', {})} class="underline">
					{importablesShowsCount}
				</a>
			</Card>
		</div>
	{/if}
	{#if importablesMoviesCount > 0}
		<div class="flex-auto">
			<Card title="Detected movies!" footer="Count of detected movies ready to import">
				<a
					rel="external"
					target="_blank"
					href={resolve('/dashboard/movies/', {})}
					class="underline"
				>
					{importablesMoviesCount}
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
					v{installedVersion} → v{newestVersion}
				</a>
			</Card>
		{/if}
	</div>
</div>
