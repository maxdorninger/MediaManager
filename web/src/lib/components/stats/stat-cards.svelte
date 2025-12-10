<script lang="ts">
	import Card from '$lib/components/stats/card.svelte';
	import { getContext, onMount } from 'svelte';
	import client from '$lib/api';
	import { isSemver, semverIsGreater } from '$lib/utils.ts';
	import { env } from '$env/dynamic/public';
	import { animate } from 'animejs';
	import { resolve } from '$app/paths';

    let {showCount, moviesCount}: {showCount: number, moviesCount: number} = $props();

	let episodeCount: number= $state(0);
	let episodeCountString: string = $derived(episodeCount.toString().padStart(3, '0'));
	let torrentCount: number = $state(0);
    let torrentCountString: string = $derived(torrentCount.toString().padStart(3, '0'));

    let installedVersion: string | undefined = env.PUBLIC_VERSION?.replace(/v*/, '');
	let releaseUrl: string | null = $state(null);
	let newestVersion: string | null = $state(null);

	let importablesShows: () => [] = getContext('importableShows');
	let importablesMovies: () => [] = getContext('importableMovies');

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

    client.GET('/api/v1/torrent').then(res => {
        if (!res.error) {
            torrentCount = res.data.length;
        }
    });
    client.GET('/api/v1/tv/episodes/count').then(res => {
        if (!res.error) {
            episodeCount = Number(res.data);
        }
    });

	onMount(async () => {
        animateCounter(showEl, showCount, 3);

        animateCounter(episodeEl, episodeCount, 3);

        animateCounter(moviesEl, moviesCount, 3);

        animateCounter(torrentEl, torrentCount, 3);

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
		<Card title="TV Shows" footer="Total count of downloaded episodes">
			<span bind:this={showEl}>{showCount ?? 'Error'}</span>
		</Card>
	</div>
	<div class="flex-auto">
		<Card title="Episodes" footer="Total count of downloaded episodes">
			<span bind:this={episodeEl}>{episodeCountString ?? 'Error'}</span>
		</Card>
	</div>
	<div class="flex-auto">
		<Card title="Movies" footer="Total count of movies">
			<span bind:this={moviesEl}>{moviesCount ?? 'Error'}</span>
		</Card>
	</div>
	<div class="flex-auto">
		<Card title="Torrents" footer="Total count of torrents/NZBs">
			<span bind:this={torrentEl}>{torrentCountString ?? 'Error'}</span>
		</Card>
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
					v{installedVersion} → v{newestVersion}
				</a>
			</Card>
		{/if}
	</div>
</div>
