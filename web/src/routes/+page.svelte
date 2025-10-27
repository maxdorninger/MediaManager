<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { browser } from '$app/environment';
	import { redirect } from '@sveltejs/kit';

	if (browser) goto(resolve('/dashboard', {}));
	else throw redirect(307, resolve('/login', {}));
</script>

<svelte:head>
	<title>MediaManager - Smart PVR for Movies and TV Shows</title>
	<meta
		content="Smart PVR for movies and TV shows - Your personal media management solution"
		name="description"
	/>
</svelte:head>
<h1>Servas</h1>
