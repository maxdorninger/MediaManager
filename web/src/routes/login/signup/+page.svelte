<script lang="ts">
	import SignupCard from '$lib/components/auth/signup-card.svelte';
	import { page } from '$app/state';

	let oauthProviders: string[] = $derived(page.data.oauthProviders);
</script>

<svelte:head>
	<title>Login - MediaManager</title>
	<meta content="Signup - MediaManager" name="description" />
</svelte:head>

<SignupCard oauthProviderNames={oauthProviders} />
