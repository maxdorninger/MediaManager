<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { env } from '$env/dynamic/public';
	import { toast } from 'svelte-sonner';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import AlertCircleIcon from '@lucide/svelte/icons/alert-circle';
	import LoadingBar from '$lib/components/loading-bar.svelte';
	import CheckCircle2Icon from '@lucide/svelte/icons/check-circle-2';
	import {base} from "$app/paths";

	const apiUrl = env.PUBLIC_API_URL;

	let email = $state('');
	let password = $state('');
	let errorMessage = $state('');
	let successMessage = $state('');
	let isLoading = $state(false);
	let confirmPassword = $state('');
	let {
		oauthProvider
	}: {
		oauthProvider: {
			oauth_name: string;
		};
	} = $props();
	let oauthProviderName = $derived(oauthProvider.oauth_name);

	async function handleSignup(event: Event) {
		event.preventDefault();

		isLoading = true;
		errorMessage = '';
		successMessage = '';

		try {
			const response = await fetch(apiUrl + '/auth/register', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					email: email,
					password: password
				}),
				credentials: 'include'
			});

			if (response.ok) {
				console.log('Registration successful!');
				console.log('Received User Data: ', response);
				successMessage = 'Registration successful! Please login.';
				toast.success(successMessage);
			} else {
				let errorText = await response.text();
				try {
					const errorData = JSON.parse(errorText);
					errorMessage = errorData.message || 'Registration failed. Please check your credentials.';
				} catch {
					errorMessage = errorText || 'Registration failed. Please check your credentials.';
				}
				toast.error(errorMessage);
				console.error('Registration failed:', response.status, errorText);
			}
		} catch (error) {
			console.error('Registration request failed:', error);
			errorMessage = 'An error occurred during the Registration request.';
			toast.error(errorMessage);
		} finally {
			isLoading = false;
		}
	}
</script>

<Card.Root class="mx-auto max-w-sm">
	<Card.Header>
		<Card.Title class="text-xl">Sign Up</Card.Title>
		<Card.Description>Enter your information to create an account</Card.Description>
	</Card.Header>
	<Card.Content>
		<form class="grid gap-4" onsubmit={handleSignup}>
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
				<Label for="password">Password</Label>
				<Input bind:value={password} id="password" required type="password" autocomplete="new-password" />
			</div>
			<div class="grid gap-2">
				<Label for="password">Confirm Password</Label>
				<Input bind:value={confirmPassword} id="confirm-password" required type="password" autocomplete="new-password" />
			</div>
			{#if errorMessage}
				<Alert.Root variant="destructive">
					<AlertCircleIcon class="size-4" />
					<Alert.Title>Error</Alert.Title>
					<Alert.Description>{errorMessage}</Alert.Description>
				</Alert.Root>
			{/if}
			{#if successMessage}
				<Alert.Root variant="default">
					<CheckCircle2Icon class="size-4" />
					<Alert.Title>Success</Alert.Title>
					<Alert.Description>{successMessage}</Alert.Description>
				</Alert.Root>
			{/if}
			{#if isLoading}
				<LoadingBar />
			{/if}
			<Button class="w-full" disabled={isLoading||password!==confirmPassword||password===''} type="submit">Create an account</Button>
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
			<Button href="{base}/login/" variant="link">
				Already have an account? Login
			</Button>
		</div>
	</Card.Content>
</Card.Root>

