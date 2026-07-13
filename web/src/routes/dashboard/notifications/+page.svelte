<script lang="ts">
	import { onMount } from 'svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';

	import client from '$lib/api';
	import type { Notification } from '$lib/api/api';
	import { resolve } from '$app/paths';

	// The notification table grows without bound (a live instance had ~437k rows),
	// so the page only ever holds the pages it has explicitly loaded.
	const PAGE_SIZE = 50;

	let unreadNotifications: Notification[] = [];
	let readNotifications: Notification[] = [];
	// Totals come from the X-Total-Count header, so "load more" knows when to stop.
	let unreadTotal = 0;
	let readTotal = 0;
	let loading = true;
	let loadingMoreUnread = false;
	let loadingMoreRead = false;
	let showRead = false;
	let markingAllAsRead = false;

	$: hasMoreUnread = unreadNotifications.length < unreadTotal;
	$: hasMoreRead = readNotifications.length < readTotal;

	function totalCountOf(response: Response, fallback: number): number {
		const header = response.headers.get('X-Total-Count');
		if (!header) return fallback;
		const total = Number(header);
		return Number.isFinite(total) ? total : fallback;
	}

	function timeOf(notification: Notification): number {
		return new Date(notification.timestamp ?? 0).getTime();
	}

	/** Insert into a newest-first list, keeping it ordered. */
	function insertNewestFirst(
		notifications: Notification[],
		notification: Notification,
		hasMore: boolean
	): Notification[] {
		const index = notifications.findIndex((n) => timeOf(n) < timeOf(notification));
		if (index === -1) {
			// Older than everything loaded: if further pages exist it belongs to one
			// of them, so leave it to be fetched in order rather than tacking it on.
			return hasMore ? notifications : [...notifications, notification];
		}
		return [...notifications.slice(0, index), notification, ...notifications.slice(index)];
	}

	// The 30s poll and a "Load More" click both write unreadNotifications, so they
	// are queued rather than run concurrently: overlapping, whichever landed last
	// would win, dropping a page or repeating an id in the keyed {#each}. Queuing
	// also means each request reads its offset only once the one before it is done.
	let unreadQueue: Promise<void> = Promise.resolve();

	function loadUnread({ reset = false } = {}): Promise<void> {
		const fetchPage = async () => {
			const offset = reset ? 0 : unreadNotifications.length;
			const { data, response } = await client.GET('/api/v1/notification/unread', {
				params: { query: { limit: PAGE_SIZE, offset } }
			});
			if (!data) return;

			unreadNotifications = reset ? data : [...unreadNotifications, ...data];
			unreadTotal = totalCountOf(response, unreadNotifications.length);
		};

		unreadQueue = unreadQueue.then(fetchPage, fetchPage);
		return unreadQueue;
	}

	async function loadRead({ reset = false } = {}) {
		const offset = reset ? 0 : readNotifications.length;
		const { data, response } = await client.GET('/api/v1/notification', {
			params: { query: { limit: PAGE_SIZE, offset, read: true } }
		});
		if (!data) return;

		readNotifications = reset ? data : [...readNotifications, ...data];
		readTotal = totalCountOf(response, readNotifications.length);
	}

	async function loadMoreUnread() {
		loadingMoreUnread = true;
		try {
			await loadUnread();
		} finally {
			loadingMoreUnread = false;
		}
	}

	async function loadMoreRead() {
		loadingMoreRead = true;
		try {
			await loadRead();
		} finally {
			loadingMoreRead = false;
		}
	}

	async function toggleShowRead() {
		showRead = !showRead;
		// Read notifications are the bulk of the table, so they are not fetched at
		// all until the section is opened.
		if (showRead && readNotifications.length === 0) {
			loadingMoreRead = true;
			try {
				await loadRead({ reset: true });
			} finally {
				loadingMoreRead = false;
			}
		}
	}

	async function markAsRead(notificationId: string) {
		const { response } = await client.PATCH('/api/v1/notification/{notification_id}/read', {
			params: { path: { notification_id: notificationId } }
		});
		if (!response.ok) return;

		const notification = unreadNotifications.find((n) => n.id === notificationId);
		if (!notification) return;

		notification.read = true;
		unreadNotifications = unreadNotifications.filter((n) => n.id !== notificationId);
		unreadTotal = Math.max(0, unreadTotal - 1);
		readTotal += 1;
		if (showRead) {
			readNotifications = insertNewestFirst(readNotifications, notification, hasMoreRead);
		}
	}

	async function markAsUnread(notificationId: string) {
		const { response } = await client.PATCH('/api/v1/notification/{notification_id}/unread', {
			params: { path: { notification_id: notificationId } }
		});
		if (!response.ok) return;

		const notification = readNotifications.find((n) => n.id === notificationId);
		if (!notification) return;

		notification.read = false;
		readNotifications = readNotifications.filter((n) => n.id !== notificationId);
		readTotal = Math.max(0, readTotal - 1);
		unreadTotal += 1;
		unreadNotifications = insertNewestFirst(unreadNotifications, notification, hasMoreUnread);
	}

	async function markAllAsRead() {
		if (unreadTotal === 0) return;

		try {
			markingAllAsRead = true;
			// One request: the client no longer holds every notification, so it cannot
			// mark them all read by looping over the ones it happens to have.
			const { response } = await client.PATCH('/api/v1/notification/read');
			if (!response.ok) return;

			unreadNotifications = [];
			unreadTotal = 0;
			readNotifications = [];
			readTotal = 0;
			if (showRead) await loadRead({ reset: true });
		} catch (error) {
			console.error('Failed to mark all notifications as read:', error);
		} finally {
			markingAllAsRead = false;
		}
	}

	onMount(() => {
		loading = true;
		loadUnread({ reset: true }).finally(() => (loading = false));

		const interval = setInterval(() => {
			if (loading || markingAllAsRead || loadingMoreUnread) return;
			// Only refresh while a single page is shown, so polling cannot discard
			// pages the user has loaded.
			if (unreadNotifications.length > PAGE_SIZE) return;
			loadUnread({ reset: true });
		}, 30000);
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
					<Breadcrumb.Link href={resolve('/dashboard', {})}>MediaManager</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Link href={resolve('/dashboard', {})}>Home</Breadcrumb.Link>
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
		{#if unreadTotal > 0}
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
					Unread Notifications
					{#if unreadTotal > 0}:
						{unreadTotal}
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
											{new Date(notification.timestamp ?? 0).toLocaleDateString()}
										</p>
									</div>
								</div>
								<div class="flex items-center gap-2">
									<Button
										onclick={() => markAsRead(notification.id ?? '')}
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

				{#if hasMoreUnread}
					<div class="mt-4 flex flex-col items-center gap-2">
						<Button
							onclick={() => loadMoreUnread()}
							disabled={loadingMoreUnread}
							variant="outline"
							class="flex items-center gap-2"
						>
							{#if loadingMoreUnread}
								<div class="h-4 w-4 animate-spin rounded-full border-b-2 border-current"></div>
							{/if}
							Load More
						</Button>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							Showing {unreadNotifications.length} of {unreadTotal}
						</p>
					</div>
				{/if}
			{/if}
		</div>

		<!-- Read Notifications Toggle -->
		<div class="mb-4">
			<button
				on:click={() => toggleShowRead()}
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
				<span>Read Notifications{showRead ? ` (${readTotal})` : ''}</span>
			</button>
		</div>

		<!-- Read Notifications -->
		{#if showRead}
			<div>
				{#if readNotifications.length === 0}
					{#if loadingMoreRead}
						<div class="flex items-center justify-center py-6">
							<div class="h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600"></div>
						</div>
					{:else}
						<div
							class="rounded-lg border border-gray-200 bg-gray-50 p-6 text-center dark:border-gray-700 dark:bg-gray-800"
						>
							<p class="text-gray-500 dark:text-gray-400">No read notifications</p>
						</div>
					{/if}
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
												{new Date(notification.timestamp ?? 0).toLocaleDateString()}
											</p>
										</div>
									</div>
									<div class="flex items-center gap-2">
										<Button
											onclick={() => markAsUnread(notification.id ?? '')}
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

					{#if hasMoreRead}
						<div class="mt-4 flex flex-col items-center gap-2">
							<Button
								onclick={() => loadMoreRead()}
								disabled={loadingMoreRead}
								variant="outline"
								class="flex items-center gap-2"
							>
								{#if loadingMoreRead}
									<div class="h-4 w-4 animate-spin rounded-full border-b-2 border-current"></div>
								{/if}
								Load More
							</Button>
							<p class="text-sm text-gray-500 dark:text-gray-400">
								Showing {readNotifications.length} of {readTotal}
							</p>
						</div>
					{/if}
				{/if}
			</div>
		{/if}
	{/if}
</main>
