<script lang="ts">
	import '../app.css';
	import { ModeWatcher } from 'mode-watcher';
	import { Toaster } from '$lib/components/ui/sonner/index.js';
	import { resolve } from '$app/paths';

	let { children } = $props();
</script>

<svelte:head>
	<title>MediaManager</title>
	<meta content="Smart PVR for movies and TV shows" name="description" />
	<link href={resolve('/logo.svg', {})} rel="icon" type="image/svg" />
</svelte:head>

<ModeWatcher />
<Toaster />
{@render children()}
