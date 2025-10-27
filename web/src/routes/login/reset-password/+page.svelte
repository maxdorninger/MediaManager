<script lang="ts">
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
	import { onMount } from 'svelte';
	import client from '$lib/api';
	import { resolve } from '$app/paths';

	let newPassword = $state('');
	let confirmPassword = $state('');
	let isLoading = $state(false);
	let resetToken = $derived(page.data.token);

	onMount(() => {
		if (!resetToken) {
			toast.error('Invalid or missing reset token.');
			goto(resolve('/login', {}));
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

		const { response } = await client.POST('/api/v1/auth/reset-password', {
			body: {
				password: newPassword,
				token: resetToken
			}
		});

		if (response.ok) {
			toast.success('Password reset successfully! You can now log in with your new password.');
			goto(resolve('/login', {}));
		} else {
			toast.error(`Failed to reset password`);
		}
		isLoading = false;
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
					bind:value={newPassword}
					disabled={isLoading}
					id="new-password"
					minlength={1}
					placeholder="Enter your new password"
					required
					type="password"
				/>
			</div>
			<div class="grid gap-2">
				<Label for="confirm-password">Confirm Password</Label>
				<Input
					bind:value={confirmPassword}
					disabled={isLoading}
					id="confirm-password"
					minlength={1}
					placeholder="Confirm your new password"
					required
					type="password"
				/>
			</div>
			<Button class="w-full" disabled={isLoading || !newPassword || !confirmPassword} type="submit">
				{#if isLoading}
					Resetting Password...
				{:else}
					Reset Password
				{/if}
			</Button>
		</form>
		<div class="mt-4 text-center text-sm">
			<a class="text-primary font-semibold hover:underline" href={resolve('/login', {})}>
				Back to Login
			</a>
			<span class="text-muted-foreground mx-2">•</span>
			<a class="text-primary hover:underline" href={resolve('/login/forgot-password', {})}>
				Request New Reset Link
			</a>
		</div>
	</CardContent>
</Card>
