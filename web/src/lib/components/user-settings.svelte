<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { toast } from 'svelte-sonner';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import client from '$lib/api';

	let newPassword: string = $state('');
	let newEmail: string = $state('');
	let dialogOpen = $state(false);

	async function saveUser() {
		const { error } = await client.PATCH('/api/v1/users/me', {
			body: {
				...(newPassword !== '' && { password: newPassword }),
				...(newEmail !== '' && { email: newEmail })
			}
		});
		if (error) {
			toast.error(`Failed to update user`);
		} else {
			toast.success(`Updated details successfully.`);
			dialogOpen = false;
		}
		newPassword = '';
		newEmail = '';
	}
</script>

<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Trigger>
		<Button class="w-full" onclick={() => (dialogOpen = true)} variant="outline">
			Edit my details
		</Button>
	</Dialog.Trigger>
	<Dialog.Content class="w-full max-w-[600px] rounded-lg p-6 shadow-lg">
		<Dialog.Header>
			<Dialog.Title class="mb-1 text-xl font-semibold">Edit User Details</Dialog.Title>
			<Dialog.Description class="mb-4 text-sm">
				Change your email or password. Leave fields empty to not change them.
			</Dialog.Description>
		</Dialog.Header>
		<div class="space-y-6">
			<!-- Email -->
			<div>
				<Label class="mb-1 block text-sm font-medium" for="email">Email</Label>
				<Input
					bind:value={newEmail}
					class="w-full"
					id="email"
					placeholder="Keep empty to not change the email"
					type="email"
				/>
			</div>
			<!-- Password -->
			<div>
				<Label class="mb-1 block text-sm font-medium" for="password">Password</Label>
				<Input
					bind:value={newPassword}
					class="w-full"
					id="password"
					placeholder="Keep empty to not change the password"
					type="password"
				/>
			</div>
		</div>
		<div class="mt-8 flex justify-end gap-2">
			<Button onclick={() => saveUser()} variant="destructive">Save</Button>
		</div>
	</Dialog.Content>
</Dialog.Root>
