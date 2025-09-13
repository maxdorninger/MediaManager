<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { toast } from 'svelte-sonner';
	import { base } from '$app/paths';
	import client from '$lib/api';

	let email = $state('');
	let isLoading = $state(false);
	let isSuccess = $state(false);

	async function requestPasswordReset() {
		if (!email) {
			toast.error('Please enter your email address.');
			return;
		}

		isLoading = true;
		const { error } = await client.POST('/api/v1/auth/forgot-password', { body: { email: email } });

		if (error) {
			toast.error(`Failed to send reset email`);
		} else {
			isSuccess = true;
			toast.success('Password reset email sent! Check your inbox for instructions.');
		}
		isLoading = false;
	}

	const handleSubmit = (event: Event) => {
		event.preventDefault();
		requestPasswordReset();
	};
</script>

<svelte:head>
	<title>Forgot Password - MediaManager</title>
	<meta
		content="Reset your MediaManager password - Enter your email to receive a reset link"
		name="description"
	/>
</svelte:head>

<Card class="mx-auto max-w-sm">
	<CardHeader>
		<CardTitle class="text-2xl">Forgot Password</CardTitle>
		<CardDescription>
			{#if isSuccess}
				We've sent a password reset link to your email address if a SMTP server is configured. Check
				your inbox and follow the instructions to reset your password. If you didn't receive an
				email, please contact an administrator, the reset link will be in the logs of MediaManager.
			{:else}
				Enter your email address and we'll send you a link to reset your password.
			{/if}
		</CardDescription>
	</CardHeader>
	<CardContent>
		{#if isSuccess}
			<div class="space-y-4">
				<div class="rounded-lg bg-green-50 p-4 text-center dark:bg-green-950">
					<p class="text-sm text-green-700 dark:text-green-300">
						Password reset email sent successfully!
					</p>
				</div>
				<div class="text-muted-foreground text-center text-sm">
					<p>Didn't receive the email? Check your spam folder or</p>
					<button
						class="text-primary hover:underline"
						onclick={() => {
							isSuccess = false;
							email = '';
						}}
					>
						try again
					</button>
				</div>
			</div>
		{:else}
			<form class="grid gap-4" onsubmit={handleSubmit}>
				<div class="grid gap-2">
					<Label for="email">Email</Label>
					<Input
						id="email"
						type="email"
						placeholder="m@example.com"
						bind:value={email}
						disabled={isLoading}
						required
					/>
				</div>
				<Button type="submit" class="w-full" disabled={isLoading || !email}>
					{#if isLoading}
						Sending Reset Email...
					{:else}
						Send Reset Email
					{/if}
				</Button>
			</form>
		{/if}
		<div class="mt-4 text-center text-sm">
			<a class="text-primary font-semibold hover:underline" href="{base}/login"> Back to Login </a>
		</div>
	</CardContent>
</Card>
