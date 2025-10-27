<script lang="ts">
	import { UserCheck } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { handleLogout } from '$lib/utils.ts';
</script>

<svelte:head>
	<title>Verify Account - MediaManager</title>
	<meta content="Verify your MediaManager account to complete registration" name="description" />
</svelte:head>

<div class="absolute top-4 right-4">
	<Button onclick={() => handleLogout()} variant="outline">Logout</Button>
</div>
<div class="mx-auto w-full max-w-md text-center">
	<div class="mb-6">
		<UserCheck class="text-primary mx-auto h-16 w-16" />
	</div>
	<h1 class="text-foreground mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
		Account Pending Activation
	</h1>
	<p class="text-muted-foreground mt-4 text-lg">
		Your account has been successfully created, but activation by an administrator is required.
	</p>
	<div class="mt-8">
		<Button onclick={() => handleLogout()}>Logout</Button>
	</div>
	<p class="end text-muted-foreground mt-10 text-sm">
		If you have any questions, please contact an administrator.
	</p>
</div>
