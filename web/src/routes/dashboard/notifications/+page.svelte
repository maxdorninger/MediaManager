<script lang="ts">
	import { onMount } from 'svelte';
	import { env } from '$env/dynamic/public';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';

	const apiUrl = env.PUBLIC_API_URL;
	import { base } from '$app/paths';

	interface NotificationResponse {
		id: string;
		read: boolean;
		message: string;
		timestamp: string;
	}

	let unreadNotifications: NotificationResponse[] = [];
	let readNotifications: NotificationResponse[] = [];
	let loading = true;
	let showRead = false;
	let markingAllAsRead = false;

	async function fetchNotifications() {
		try {
			loading = true;
			const [unreadResponse, allResponse] = await Promise.all([
				fetch(`${apiUrl}/notification/unread`, {
					method: 'GET',
					headers: {
						'Content-Type': 'application/json'
					},
					credentials: 'include'
				}),
				fetch(`${apiUrl}/notification`, {
					method: 'GET',
					headers: {
						'Content-Type': 'application/json'
					},
					credentials: 'include'
				})
			]);

			if (unreadResponse.ok) {
				unreadNotifications = await unreadResponse.json();
			}

			if (allResponse.ok) {
				const allNotifications: NotificationResponse[] = await allResponse.json();
				readNotifications = allNotifications.filter((n) => n.read);
			}
		} catch (error) {
			console.error('Failed to fetch notifications:', error);
		} finally {
			loading = false;
		}
	}

	async function markAsRead(notificationId: string) {
		try {
			const response = await fetch(`${apiUrl}/notification/${notificationId}/read`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include'
			});

			if (response.ok) {
				const notification = unreadNotifications.find((n) => n.id === notificationId);
				if (notification) {
					notification.read = true;
					readNotifications = [notification, ...readNotifications];
					unreadNotifications = unreadNotifications.filter((n) => n.id !== notificationId);
				}
			}
		} catch (error) {
			console.error('Failed to mark notification as read:', error);
		}
	}

	async function markAsUnread(notificationId: string) {
		try {
			const response = await fetch(`${apiUrl}/notification/${notificationId}/unread`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include'
			});

			if (response.ok) {
				const notification = readNotifications.find((n) => n.id === notificationId);
				if (notification) {
					notification.read = false;
					unreadNotifications = [notification, ...unreadNotifications];
					readNotifications = readNotifications.filter((n) => n.id !== notificationId);
				}
			}
		} catch (error) {
			console.error('Failed to mark notification as unread:', error);
		}
	}

	async function markAllAsRead() {
		if (unreadNotifications.length === 0) return;

		try {
			markingAllAsRead = true;
			const promises = unreadNotifications.map((notification) =>
				fetch(`${apiUrl}/notification/${notification.id}/read`, {
					method: 'PATCH',
					headers: {
						'Content-Type': 'application/json'
					},
					credentials: 'include'
				})
			);

			await Promise.all(promises);

			// Move all unread to read
			readNotifications = [
				...unreadNotifications.map((n) => ({ ...n, read: true })),
				...readNotifications
			];
			unreadNotifications = [];
		} catch (error) {
			console.error('Failed to mark all notifications as read:', error);
		} finally {
			markingAllAsRead = false;
		}
	}

	function formatTimestamp(timestamp: string): string {
		const date = new Date(timestamp);
		const now = new Date();
		const diffInMs = now.getTime() - date.getTime();
		const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
		const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
		const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

		if (diffInMinutes < 1) return 'Just now';
		if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
		if (diffInHours < 24) return `${diffInHours}h ago`;
		if (diffInDays < 7) return `${diffInDays}d ago`;

		return date.toLocaleDateString();
	}

	onMount(() => {
		fetchNotifications();

		const interval = setInterval(fetchNotifications, 30000);
		return () => clearInterval(interval);
	});
</script>

<svelte:head>
	<title>Notifications - MediaManager</title>
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
					<Breadcrumb.Link href="{base}/dashboard">Home</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>Notifications</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<main class="container mx-auto px-4 py-8">
	<div class="mb-6 flex items-center justify-between">
		<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Notifications</h1>
		{#if unreadNotifications.length > 0}
			<Button onclick={() => markAllAsRead()} disabled={markingAllAsRead} class="flex items-center">
				{#if markingAllAsRead}
					<div class="h-4 w-4 animate-spin rounded-full border-b-2 border-white"></div>
				{/if}
				Mark All as Read
			</Button>
		{/if}
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
		</div>
	{:else}
		<!-- Unread Notifications -->
		<div class="mb-8">
			<div class="mb-4 flex items-center gap-2">
				<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
					Unread Notifications{#if unreadNotifications.length > 0}:
						{unreadNotifications.length}
					{/if}
				</h2>
			</div>

			{#if unreadNotifications.length === 0}
				<div
					class="rounded-lg border border-green-200 bg-green-50 p-6 text-center dark:border-green-800 dark:bg-green-900/20"
				>
					<p class="font-medium text-green-800 dark:text-green-200">All caught up!</p>
					<p class="text-sm text-green-600 dark:text-green-400">No unread notifications</p>
				</div>
			{:else}
				<div class="space-y-3">
					{#each unreadNotifications as notification (notification.id)}
						<div
							class="rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm dark:border-blue-800 dark:bg-blue-900/20"
						>
							<div class="flex items-start justify-between gap-4">
								<div class="flex flex-1 items-start gap-3">
									<div class="flex-1">
										<p class="font-medium text-gray-900 dark:text-white">
											{notification.message}
										</p>
										<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
											{formatTimestamp(notification.timestamp)}
										</p>
									</div>
								</div>
								<div class="flex items-center gap-2">
									<Button
										onclick={() => markAsRead(notification.id)}
										class="rounded-lg p-2 text-blue-600 transition-colors hover:bg-blue-100 dark:hover:bg-blue-800"
										title="Mark as read"
										variant="outline"
									>
										<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M5 13l4 4L19 7"
											></path>
										</svg>
									</Button>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Read Notifications Toggle -->
		<div class="mb-4">
			<button
				on:click={() => (showRead = !showRead)}
				class="flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
			>
				<svg
					class="h-4 w-4 transition-transform {showRead ? 'rotate-90' : ''}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"
					></path>
				</svg>
				<span>Read Notifications ({readNotifications.length})</span>
			</button>
		</div>

		<!-- Read Notifications -->
		{#if showRead}
			<div>
				{#if readNotifications.length === 0}
					<div
						class="rounded-lg border border-gray-200 bg-gray-50 p-6 text-center dark:border-gray-700 dark:bg-gray-800"
					>
						<p class="text-gray-500 dark:text-gray-400">No read notifications</p>
					</div>
				{:else}
					<div class="space-y-3">
						{#each readNotifications as notification (notification.id)}
							<div
								class="rounded-lg border border-gray-200 bg-white p-4 opacity-75 shadow-sm dark:border-gray-700 dark:bg-gray-800"
							>
								<div class="flex items-start justify-between gap-4">
									<div class="flex flex-1 items-start gap-3">
										<div class="flex-1">
											<p class="text-gray-700 dark:text-gray-300">
												{notification.message}
											</p>
											<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
												{formatTimestamp(notification.timestamp)}
											</p>
										</div>
									</div>
									<div class="flex items-center gap-2">
										<Button
											onclick={() => markAsUnread(notification.id)}
											class="rounded-lg p-2 text-blue-600 transition-colors hover:bg-blue-100 dark:hover:bg-blue-800"
											title="Mark as unread"
											variant="outline"
										>
											<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M3 8l7.89 7.89a2 2 0 002.83 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
												></path>
											</svg>
										</Button>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</main>
