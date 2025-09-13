<script lang="ts">
	import LoginCard from '$lib/components/login-card.svelte';
	import { getContext } from 'svelte';

	let oauthProvider: () => string[] = getContext('oauthProviders');
</script>

<svelte:head>
	<title>Login - MediaManager</title>
	<meta
		content="Login to MediaManager - Access your personal media management dashboard"
		name="description"
	/>
</svelte:head>

<main>
	<LoginCard oauthProviderNames={oauthProvider()} />
</main>
