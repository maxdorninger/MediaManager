<script lang="ts">
	import LoginCard from '$lib/components/login-card.svelte';
	import { page } from '$app/state';
	import {getContext} from "svelte";

	let oauthProvider: () => {oauth_name: string} = getContext("oauthProvider");
</script>

<svelte:head>
	<title>Login - MediaManager</title>
	<meta
		content="Login to MediaManager - Access your personal media management dashboard"
		name="description"
	/>
</svelte:head>

<main>
	<LoginCard oauthProvider={oauthProvider()} />
</main>