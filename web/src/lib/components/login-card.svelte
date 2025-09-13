<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { base } from '$app/paths';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import AlertCircleIcon from '@lucide/svelte/icons/alert-circle';
	import LoadingBar from '$lib/components/loading-bar.svelte';
	import client from '$lib/api';
	import { handleOauth } from '$lib/utils.ts';

	let {
		oauthProviderNames
	}: {
		oauthProviderNames: string[];
	} = $props();

	let email = $state('');
	let password = $state('');
	let errorMessage = $state('');
	let isLoading = $state(false);

	async function handleLogin(event: Event) {
		event.preventDefault();

		isLoading = true;
		errorMessage = '';

		const { error, response } = await client.POST('/api/v1/auth/cookie/login', {
			body: {
				username: email,
				password: password,
				scope: ''
			},
			headers: {
				'Content-Type': 'application/x-www-form-urlencoded'
			}
		});
		isLoading = false;

		if (!error) {
			console.log('Login successful!');
			console.log('Received User Data: ', response);
			errorMessage = 'Login successful! Redirecting...';
			toast.success(errorMessage);
			goto(base + '/dashboard');
		} else {
			toast.error('Login failed!');
			errorMessage = `Login failed! Please check your credentials and try again.`;
		}
	}
</script>

<Card.Root class="mx-auto max-w-sm">
	<Card.Header>
		<Card.Title class="text-2xl">Login</Card.Title>
		<Card.Description>Enter your email below to log in to your account</Card.Description>
	</Card.Header>
	<Card.Content>
		<form class="grid gap-4" onsubmit={handleLogin}>
			<div class="grid gap-2">
				<Label for="email">Email</Label>
				<Input
					autocomplete="email"
					bind:value={email}
					id="email"
					placeholder="m@example.com"
					required
					type="email"
				/>
			</div>
			<div class="grid gap-2">
				<div class="flex items-center">
					<Label for="password">Password</Label>
					<a class="ml-auto inline-block text-sm underline" href="{base}/login/forgot-password">
						Forgot your password?
					</a>
				</div>
				<Input
					autocomplete="current-password"
					bind:value={password}
					id="password"
					required
					type="password"
				/>
			</div>

			{#if errorMessage}
				<Alert.Root variant="destructive">
					<AlertCircleIcon class="size-4" />
					<Alert.Title>Error</Alert.Title>
					<Alert.Description>{errorMessage}</Alert.Description>
				</Alert.Root>
			{/if}

			{#if isLoading}
				<LoadingBar />
			{/if}
			<Button class="w-full" disabled={isLoading} type="submit">Login</Button>
		</form>
		{#each oauthProviderNames as name (name)}
			<div
				class="after:border-border relative mt-2 text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t"
			>
				<span class="bg-background text-muted-foreground relative z-10 px-2">
					Or continue with
				</span>
			</div>
			<Button class="mt-2 w-full" onclick={() => handleOauth()} variant="outline"
				>Login with {name}</Button
			>
		{/each}
		<div class="mt-4 text-center text-sm">
			<Button href="{base}/login/signup/" variant="link">Don't have an account? Sign up</Button>
		</div>
	</Card.Content>
</Card.Root>
