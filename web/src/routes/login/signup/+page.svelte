<script lang="ts">
	import SignupCard from "$lib/components/signup-card.svelte";
    import {getContext} from "svelte";

    let oauthProvider: () => {oauth_name: string} = getContext("oauthProvider");
</script>

<svelte:head>
    <title>Login - MediaManager</title>
    <meta
            content="Signup - MediaManager"
            name="description"
    />
</svelte:head>

<SignupCard oauthProvider={oauthProvider()}/>
