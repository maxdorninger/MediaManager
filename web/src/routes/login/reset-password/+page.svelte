<script lang="ts">
	import logo from '$lib/images/logo.svg';
	import background from '$lib/images/pawel-czerwinski-NTYYL9Eb9y8-unsplash.jpg?enhanced';
	import { page } from '$app/state';
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
	import { goto } from '$app/navigation';
	import { env } from '$env/dynamic/public';
	import { onMount } from 'svelte';
	import { base } from '$app/paths';

	const apiUrl = env.PUBLIC_API_URL;
	let newPassword = $state('');
	let confirmPassword = $state('');
	let isLoading = $state(false);
	let resetToken = $derived(page.data.token);

	onMount(() => {
		if (!resetToken) {
			toast.error('Invalid or missing reset token.');
			goto(base + '/login');
		}
	});

	async function resetPassword() {
		if (newPassword !== confirmPassword) {
			toast.error('Passwords do not match.');
			return;
		}

		if (!resetToken) {
			toast.error('Invalid or missing reset token.');
			return;
		}

		isLoading = true;

		try {
			const response = await fetch(apiUrl + `/auth/reset-password`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ password: newPassword, token: resetToken }),
				credentials: 'include'
			});

			if (response.ok) {
				toast.success('Password reset successfully! You can now log in with your new password.');
				goto(base + '/login');
			} else {
				const errorText = await response.text();
				toast.error(`Failed to reset password: ${errorText}`);
				throw new Error(`Failed to reset password: ${errorText}`);
			}
		} catch (error) {
			console.error('Error resetting password:', error);
			toast.error(error instanceof Error ? error.message : 'An unknown error occurred.');
		} finally {
			isLoading = false;
		}
	}

	const handleSubmit = (event: Event) => {
		event.preventDefault();
		resetPassword();
	};
</script>

<svelte:head>
	<title>Reset Password - MediaManager</title>
	<meta content="Reset your MediaManager password with a secure token" name="description" />
</svelte:head>

<Card class="mx-auto max-w-sm">
	<CardHeader>
		<CardTitle class="text-2xl">Reset Password</CardTitle>
		<CardDescription>Enter your new password below.</CardDescription>
	</CardHeader>
	<CardContent>
		<form class="grid gap-4" onsubmit={handleSubmit}>
			<div class="grid gap-2">
				<Label for="new-password">New Password</Label>
				<Input
					id="new-password"
					type="password"
					placeholder="Enter your new password"
					bind:value={newPassword}
					disabled={isLoading}
					required
					minlength={1}
				/>
			</div>
			<div class="grid gap-2">
				<Label for="confirm-password">Confirm Password</Label>
				<Input
					id="confirm-password"
					type="password"
					placeholder="Confirm your new password"
					bind:value={confirmPassword}
					disabled={isLoading}
					required
					minlength={1}
				/>
			</div>
			<Button
				type="submit"
				class="w-full"
				disabled={isLoading || !newPassword || !confirmPassword}
			>
				{#if isLoading}
					Resetting Password...
				{:else}
					Reset Password
				{/if}
			</Button>
		</form>
		<div class="mt-4 text-center text-sm">
			<a href="{base}/login" class="font-semibold text-primary hover:underline">
				Back to Login
			</a>
			<span class="mx-2 text-muted-foreground">•</span>
			<a href="{base}/login/forgot-password" class="text-primary hover:underline">
				Request New Reset Link
			</a>
		</div>
	</CardContent>
</Card>
