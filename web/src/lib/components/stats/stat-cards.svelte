<script lang="ts">
    import { Badge } from "$lib/components/ui/badge/index.js";
    import Card from "$lib/components/stats/card.svelte";
    import { onMount } from 'svelte';
    import client from '$lib/api';
    import type { components } from '$lib/api/api.d.ts';

    let moviesCount: string | null = $state(null);
    let episodeCount: string | null = $state(null);
    let showCount: string | null = $state(null);
    let torrentCount: string | null = $state(null);

    onMount(async () => {
        let tvShows = await client.GET("/api/v1/tv/shows")
        if(!tvShows.error)
            showCount = tvShows.data.length.toString().padStart(3, "0");

        let episodes = await client.GET("/api/v1/tv/episodes/count")
        if(!episodes.error)
            episodeCount = episodes.data.toString().padStart(3, "0")

        let movies = await client.GET("/api/v1/movies")
        if(!movies.error)
            moviesCount= movies.data.length.toString().padStart(3, "0")

        let torrents = await client.GET("/api/v1/torrent")
        if(!torrents.error)
            torrentCount = torrents.data.length.toString().padStart(3, "0")
    })

</script>
<div
        class="lg:grid-cols-2 xl:grid-cols-4 grid grid-cols-1 gap-4 px-4 lg:px-6"
>
    <Card title="TV Shows" content={showCount} footer="Total count of downloaded episodes"></Card>
    <Card title="Episodes" content={episodeCount} footer="Total count of downloaded episodes"></Card>
    <Card title="Movies" content={moviesCount} footer="Total count of movies"></Card>
    <Card title="Torrents" content={torrentCount} footer="Total count of torrents/NZBs"></Card>
</div>