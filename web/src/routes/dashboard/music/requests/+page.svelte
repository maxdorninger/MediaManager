<script lang="ts">
	import { page } from '$app/state';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { resolve } from '$app/paths';
	import { getAudioQualityString } from '$lib/utils';
	import type { components } from '$lib/api/api';
	import { getContext } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import client from '$lib/api';
	import { toast } from 'svelte-sonner';

	let requests: components['schemas']['RichAlbumRequest'][] = $derived(page.data.requestsData);
	let user: () => components['schemas']['UserRead'] = getContext('user');

	async function authorizeRequest(requestId: string, authorized: boolean) {
		const { response } = await client.PATCH('/api/v1/music/albums/requests/{album_request_id}', {
			params: {
				path: { album_request_id: requestId },
				query: { authorized_status: authorized }
			}
		});
		if (response.ok) {
			toast.success(authorized ? 'Request authorized.' : 'Request de-authorized.');
		} else {
			toast.error('Failed to update request.');
		}
	}

	async function deleteRequest(requestId: string) {
		const { response } = await client.DELETE('/api/v1/music/albums/requests/{album_request_id}', {
			params: {
				path: { album_request_id: requestId }
			}
		});
		if (response.ok) {
			toast.success('Request deleted.');
		} else {
			toast.error('Failed to delete request.');
		}
	}
</script>

<svelte:head>
	<title>Album Requests - MediaManager</title>
	<meta content="View and manage album download requests in MediaManager" name="description" />
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
					<Breadcrumb.Link href={resolve('/dashboard/music', {})}>Music</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>Album Requests</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<main class="mx-auto flex w-full flex-1 flex-col gap-4 p-4 md:max-w-[80em]">
	<h1 class="scroll-m-20 text-center text-4xl font-extrabold tracking-tight lg:text-5xl">
		Album Requests
	</h1>
	<Card.Root>
		<Card.Header>
			<Card.Title>Requests</Card.Title>
			<Card.Description>All album download requests.</Card.Description>
		</Card.Header>
		<Card.Content class="w-full overflow-x-auto">
			<Table.Root>
				<Table.Caption>All album requests.</Table.Caption>
				<Table.Header>
					<Table.Row>
						<Table.Head>Artist</Table.Head>
						<Table.Head>Album</Table.Head>
						<Table.Head>Wanted Quality</Table.Head>
						<Table.Head>Min Quality</Table.Head>
						<Table.Head>Requested By</Table.Head>
						<Table.Head>Authorized</Table.Head>
						{#if user().is_superuser}
							<Table.Head>Actions</Table.Head>
						{/if}
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#if requests && requests.length > 0}
						{#each requests as request (request.id)}
							<Table.Row>
								<Table.Cell>
									<a
										href={resolve('/dashboard/music/[artistId]', {
											artistId: request.artist.id
										})}
										class="underline"
									>
										{request.artist.name}
									</a>
								</Table.Cell>
								<Table.Cell>{request.album.name}</Table.Cell>
								<Table.Cell>{getAudioQualityString(request.wanted_quality)}</Table.Cell>
								<Table.Cell>{getAudioQualityString(request.min_quality)}</Table.Cell>
								<Table.Cell>{request.requested_by?.email ?? 'Unknown'}</Table.Cell>
								<Table.Cell>{request.authorized ? 'Yes' : 'No'}</Table.Cell>
								{#if user().is_superuser}
									<Table.Cell class="flex gap-2">
										{#if !request.authorized}
											<Button
												size="sm"
												variant="outline"
												onclick={() => authorizeRequest(request.id, true)}
											>
												Authorize
											</Button>
										{:else}
											<Button
												size="sm"
												variant="outline"
												onclick={() => authorizeRequest(request.id, false)}
											>
												Revoke
											</Button>
										{/if}
										<Button
											size="sm"
											variant="destructive"
											onclick={() => deleteRequest(request.id)}
										>
											Delete
										</Button>
									</Table.Cell>
								{/if}
							</Table.Row>
						{/each}
					{:else}
						<Table.Row>
							<Table.Cell colspan={user().is_superuser ? 7 : 6} class="text-center">
								No album requests yet.
							</Table.Cell>
						</Table.Row>
					{/if}
				</Table.Body>
			</Table.Root>
		</Card.Content>
	</Card.Root>
</main>
