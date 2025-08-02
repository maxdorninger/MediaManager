<script lang="ts">
	import { UserCheck } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import Logo from '$lib/components/logo-side-by-side.svelte';
	import { handleLogout } from '$lib/utils.ts';
	import { base } from '$app/paths';
</script>

<svelte:head>
	<title>Verify Account - MediaManager</title>
	<meta content="Verify your MediaManager account to complete registration" name="description" />
</svelte:head>

<div class="absolute right-4 top-4">
	<Button onclick={() => handleLogout()} variant="outline">Logout</Button>
</div>
<div class="mx-auto w-full max-w-md text-center">
	<div class="mb-6">
		<UserCheck class="mx-auto h-16 w-16 text-primary" />
	</div>
	<h1 class="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
		Account Pending Activation
	</h1>
	<p class="mt-4 text-lg text-muted-foreground">
		Your account has been successfully created, but activation by an administrator is required.
	</p>
	<div class="mt-8">
		<Button href="{base}/dashboard">Go to Dashboard</Button>
	</div>
	<p class="mt-10 text-sm text-muted-foreground">
		The above button will only work once your account is verified.
	</p>
	<p class="end mt-10 text-sm text-muted-foreground">
		If you have any questions, please contact an administrator.
	</p>
</div>

