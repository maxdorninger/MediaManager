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

	let {
		oauthProvider
	}: {
		oauthProvider: {
			oauth_name: string;
		};
	} = $props();

	let email = $state('');
	let password = $state('');
	let errorMessage = $state('');
	let isLoading = $state(false);

	async function handleLogin(event: Event) {
		event.preventDefault();

		isLoading = true;
		errorMessage = '';

		const { response } = await client.POST('/api/v1/auth/cookie/login', {
			requestBody: {
				content: {
					'application/x-www-form-urlencoded': {
						username: email,
						password: password
					}
				}
			}
		});
		isLoading = false;

		if (response.ok) {
			console.log('Login successful!');
			console.log('Received User Data: ', response);
			errorMessage = 'Login successful! Redirecting...';
			toast.success(errorMessage);
			goto(base + '/dashboard');
		} else {
			let errorText = await response.text();
			try {
				const errorData = JSON.parse(errorText);
				errorMessage = errorData.message || 'Login failed. Please check your credentials.';
			} catch {
				errorMessage = errorText || 'Login failed. Please check your credentials.';
			}
			toast.error(errorMessage);
			console.error('Login failed:', response.status, errorText);
		}
	}

	async function handleOauth() {
		const { response, data } = await client.GET('/api/v1/auth/cookie/OpenID/authorize', {
			params: {
				query: {
					scopes: 'email'
				}
			}
		});
		if (response.ok) {
			window.location = data.authorization_url;
		} else {
			toast.error(data);
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
		{#await oauthProvider}
			<LoadingBar />
		{:then result}
			{#if result.oauth_name != null}
				<div
					class="after:border-border relative mt-2 text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t"
				>
					<span class="bg-background text-muted-foreground relative z-10 px-2">
						Or continue with
					</span>
				</div>
				<Button class="mt-2 w-full" onclick={() => handleOauth()} variant="outline"
					>Login with {result.oauth_name}</Button
				>
			{/if}
		{/await}
		<div class="mt-4 text-center text-sm">
			<Button href="{base}/login/signup/" variant="link">Don't have an account? Sign up</Button>
		</div>
	</Card.Content>
</Card.Root>
