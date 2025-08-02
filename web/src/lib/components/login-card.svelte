<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { goto } from '$app/navigation';
	import { env } from '$env/dynamic/public';
	import { toast } from 'svelte-sonner';
	import { base } from '$app/paths';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import AlertCircleIcon from '@lucide/svelte/icons/alert-circle';
	import LoadingBar from '$lib/components/loading-bar.svelte';

	const apiUrl = env.PUBLIC_API_URL;

	let {
		oauthProvider
	}: {
		oauthProvider: {
			oauth_name: string;
		};
	} = $props();
	let oauthProviderName = $derived(oauthProvider.oauth_name);

	let email = $state('');
	let password = $state('');
	let errorMessage = $state('');
	let isLoading = $state(false);

	async function handleLogin(event: Event) {
		event.preventDefault();

		isLoading = true;
		errorMessage = '';

		const formData = new URLSearchParams();
		formData.append('username', email);
		formData.append('password', password);
		try {
			const response = await fetch(apiUrl + '/auth/cookie/login', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded'
				},
				body: formData.toString(),
				credentials: 'include'
			});

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
		} catch (error) {
			console.error('Login request failed:', error);
			errorMessage = 'An error occurred during the login request.';
			toast.error(errorMessage);
		} finally {
			isLoading = false;
		}
	}

	async function handleOauth() {
		try {
			const response = await fetch(
				apiUrl + '/auth/cookie/' + oauthProviderName + '/authorize?scopes=email',
				{
					method: 'GET',
					headers: {
						'Content-Type': 'application/json'
					}
				}
			);
			if (response.ok) {
				let result = await response.json();
				console.log(
					'Redirecting to OAuth provider:',
					oauthProviderName,
					'url: ',
					result.authorization_url
				);
				toast.success('Redirecting to ' + oauthProviderName + ' for authentication...');
				window.location = result.authorization_url;
			} else {
				let errorText = await response.text();
				toast.error(errorMessage);
				console.error('Login failed:', response.status, errorText);
			}
		} catch (error) {
			console.error('Login request failed:', error);
			errorMessage = 'An error occurred during the login request.';
			toast.error(errorMessage);
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
					bind:value={email}
					id="email"
					placeholder="m@example.com"
					required
					type="email"
					autocomplete="email"
				/>
			</div>
			<div class="grid gap-2">
				<div class="flex items-center">
					<Label for="password">Password</Label>
					<a class="ml-auto inline-block text-sm underline" href="{base}/login/forgot-password">
						Forgot your password?
					</a>
				</div>
				<Input bind:value={password} id="password" required type="password" autocomplete="current-password" />
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
					class="relative mt-2 text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t after:border-border"
				>
					<span class="relative z-10 bg-background px-2 text-muted-foreground">
						Or continue with
					</span>
				</div>
				<Button class="mt-2 w-full" onclick={() => handleOauth()} variant="outline"
					>Login with {result.oauth_name}</Button
				>
			{/if}
		{/await}
		<div class="mt-4 text-center text-sm">
			<Button href="{base}/login/signup/" variant="link">
				Don't have an account? Sign up
			</Button>
		</div>
	</Card.Content>
</Card.Root>
