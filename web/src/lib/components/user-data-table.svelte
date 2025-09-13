<script lang="ts">
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { toast } from 'svelte-sonner';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as RadioGroup from '$lib/components/ui/radio-group/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { invalidateAll } from '$app/navigation';
	import client from '$lib/api';
	import type { components } from '$lib/api/api';

	let { users }: { users: components['schemas']['UserRead'][] } = $props();
	let sortedUsers = $derived(users.sort((a, b) => a.email.localeCompare(b.email)));
	let selectedUser: components['schemas']['UserRead'] | null = $state(null);
	let newPassword: string = $state('');
	let newEmail: string = $state('');
	let dialogOpen = $state(false);

	async function saveUser() {
		if (!selectedUser) return;

		const { error } = await client.PATCH('/api/v1/users/{id}', {
			params: {
				path: {
					id: selectedUser.id
				}
			},
			body: {
				is_verified: selectedUser.is_verified,
				is_active: selectedUser.is_active,
				is_superuser: selectedUser.is_superuser,
				...(newPassword !== '' && { password: newPassword }),
				...(newEmail !== '' && { email: newEmail })
			}
		});

		if (error) {
			toast.error(`Failed to update user ${selectedUser.email}: ${error}`);
		} else {
			toast.success(`User ${selectedUser.email} updated successfully.`);
			dialogOpen = false;
			selectedUser = null;
			newPassword = '';
			newEmail = '';
			await invalidateAll();
		}
	}
</script>

<Table.Root>
	<Table.Caption>A list of all users.</Table.Caption>
	<Table.Header>
		<Table.Row>
			<Table.Head>Email</Table.Head>
			<Table.Head>Verified</Table.Head>
			<Table.Head>Active</Table.Head>
			<Table.Head>Admin</Table.Head>
		</Table.Row>
	</Table.Header>
	<Table.Body>
		{#each sortedUsers as user (user.id)}
			<Table.Row>
				<Table.Cell class="font-medium">
					{user.email}
				</Table.Cell>
				<Table.Cell>
					<CheckmarkX state={user.is_verified} />
				</Table.Cell>
				<Table.Cell>
					<CheckmarkX state={user.is_active} />
				</Table.Cell>
				<Table.Cell>
					<CheckmarkX state={user.is_superuser} />
				</Table.Cell>
				<Table.Cell>
					<Button
						variant="secondary"
						onclick={() => {
							selectedUser = user;
							dialogOpen = true;
						}}
					>
						Edit
					</Button>
				</Table.Cell>
			</Table.Row>
		{/each}
	</Table.Body>
</Table.Root>
<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Content class="w-full max-w-[600px] rounded-lg p-6 shadow-lg">
		<Dialog.Header>
			<Dialog.Title class="mb-1 text-xl font-semibold">Edit user</Dialog.Title>
			<Dialog.Description class="mb-4 text-sm">
				Edit {selectedUser?.email}
			</Dialog.Description>
		</Dialog.Header>
		<div class="space-y-6">
			<!-- Verified -->
			<div>
				<Label class="mb-1 block text-sm font-medium" for="verified">Verified</Label>
				<RadioGroup.Root
					class="flex gap-4"
					onValueChange={(v) => {
						if (selectedUser) selectedUser.is_verified = v === 'true';
					}}
					value={selectedUser?.is_verified ? 'true' : 'false'}
				>
					<div class="flex items-center gap-1">
						<RadioGroup.Item class="accent-green-600" id="verified-true" value="true" />
						<Label class="text-sm" for="verified-true">True</Label>
					</div>
					<div class="flex items-center gap-1">
						<RadioGroup.Item class="accent-red-600" id="verified-false" value="false" />
						<Label class="text-sm" for="verified-false">False</Label>
					</div>
				</RadioGroup.Root>
			</div>
			<hr />
			<!-- Active -->
			<div>
				<Label class="mb-1 block text-sm font-medium" for="active">Active</Label>
				<RadioGroup.Root
					class="flex gap-4"
					onValueChange={(v) => {
						if (selectedUser) selectedUser.is_active = v === 'true';
					}}
					value={selectedUser?.is_active ? 'true' : 'false'}
				>
					<div class="flex items-center gap-1">
						<RadioGroup.Item class="accent-green-600" id="active-true" value="true" />
						<Label class="text-sm" for="active-true">True</Label>
					</div>
					<div class="flex items-center gap-1">
						<RadioGroup.Item class="accent-red-600" id="active-false" value="false" />
						<Label class="text-sm" for="active-false">False</Label>
					</div>
				</RadioGroup.Root>
			</div>
			<hr />
			<!-- Super User -->
			<div>
				<Label class="mb-1 block text-sm font-medium" for="superuser">Admin</Label>
				<RadioGroup.Root
					class="flex gap-4"
					onValueChange={(v) => {
						if (selectedUser) selectedUser.is_superuser = v === 'true';
					}}
					value={selectedUser?.is_superuser ? 'true' : 'false'}
				>
					<div class="flex items-center gap-1">
						<RadioGroup.Item class="accent-green-600" id="superuser-true" value="true" />
						<Label class="text-sm" for="superuser-true">True</Label>
					</div>
					<div class="flex items-center gap-1">
						<RadioGroup.Item class="accent-red-600" id="superuser-false" value="false" />
						<Label class="text-sm" for="superuser-false">False</Label>
					</div>
				</RadioGroup.Root>
			</div>
			<!-- Email -->
			<div>
				<Label class="mb-1 block text-sm font-medium" for="email">Email</Label>
				<Input
					bind:value={newEmail}
					class="w-full"
					id="email"
					placeholder={selectedUser?.email}
					type="text"
				/>
			</div>
			<!-- Password -->
			<div>
				<Label class="mb-1 block text-sm font-medium" for="superuser">Password</Label>
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
			<Button onclick={() => (dialogOpen = false)} variant="outline">Cancel</Button>
			<Button onclick={() => saveUser()} variant="destructive">Save</Button>
		</div>
	</Dialog.Content>
</Dialog.Root>
