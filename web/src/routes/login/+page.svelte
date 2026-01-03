<script lang="ts">
	import LoginCard from '$lib/components/auth/login-card.svelte';
	import { page } from '$app/state';
	import type { components } from '$lib/api/api';
	let loginMetaData: components['schemas']['AuthMetadata'] = $derived(page.data.loginData);
</script>

<svelte:head>
	<title>Login - MediaManager</title>
	<meta
		content="Login to MediaManager - Access your personal media management dashboard"
		name="description"
	/>
</svelte:head>

<main>
	<LoginCard oauthProviderNames={loginMetaData.oauth_providers} />
</main>
