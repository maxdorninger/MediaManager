<script lang="ts">
	import UserTable from '$lib/components/user-data-table.svelte';
	import { page } from '$app/state';
	import * as Card from '$lib/components/ui/card/index.js';
	import { getContext } from 'svelte';
	import UserSettings from '$lib/components/user-settings.svelte';
	import { Separator } from '$lib/components/ui/separator';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { base } from '$app/paths';
	import type { User } from '$lib/types';

	let currentUser: () => User = getContext('user');
	let users: User[] = $derived(
		page.data.users.filter((user: User) => user.id !== currentUser().id)
	);
	console.log('Current user:', currentUser());
</script>

<svelte:head>
	<title>Settings - MediaManager</title>
	<meta content="Manage your MediaManager settings and user preferences" name="description" />
</svelte:head>

<header class="flex h-16 shrink-0 items-center gap-2">
	<div class="flex items-center gap-2 px-4">
		<Sidebar.Trigger class="-ml-1" />
		<Separator class="mr-2 h-4" orientation="vertical" />
		<Breadcrumb.Root>
			<Breadcrumb.List>
				<Breadcrumb.Item class="hidden md:block">
					<Breadcrumb.Link href="{base}/dashboard">MediaManager</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>Settings</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<h1 class="my-6 scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
		Settings
	</h1>
	<Card.Root id="me">
		<Card.Header>
			<Card.Title>You</Card.Title>
			<Card.Description>Change your email or password</Card.Description>
		</Card.Header>
		<Card.Content>
			<UserSettings />
		</Card.Content>
	</Card.Root>
	{#if currentUser().is_superuser}
		<Card.Root id="users">
			<Card.Header>
				<Card.Title>Users</Card.Title>
				<Card.Description>Edit, delete or change the permissions of other users</Card.Description>
			</Card.Header>
			<Card.Content>
				<UserTable {users} />
			</Card.Content>
		</Card.Root>
	{/if}
</main>
