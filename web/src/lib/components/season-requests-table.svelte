<script lang="ts">
	import { getFullyQualifiedMediaName, getTorrentQualityString } from '$lib/utils.js';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import type { components } from '$lib/api/api';

	import * as Table from '$lib/components/ui/table/index.js';
	import { getContext } from 'svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import client from '$lib/api';

	let {
		requests,
		filter = () => true,
		isShow = true
	}: {
		requests: (
			| components['schemas']['RichSeasonRequest']
			| components['schemas']['RichMovieRequest']
		)[];
		filter?: (
			request:
				| components['schemas']['RichSeasonRequest']
				| components['schemas']['RichMovieRequest']
		) => boolean;
		isShow: boolean;
	} = $props();
	const user: () => components['schemas']['UserRead'] = getContext('user');

	async function approveRequest(requestId: string, currentAuthorizedStatus: boolean) {
		let response;
		if (isShow) {
			const data = await client.PATCH('/api/v1/tv/seasons/requests/{season_request_id}', {
				params: {
					path: {
						season_request_id: requestId
					},
					query: {
						authorized_status: !currentAuthorizedStatus
					}
				}
			});
			response = data.response;
		} else {
			const data = await client.PATCH('/api/v1/movies/requests/{movie_request_id}', {
				params: {
					path: {
						movie_request_id: requestId
					},
					query: {
						authorized_status: !currentAuthorizedStatus
					}
				}
			});
			response = data.response;
		}
		if (response.ok) {
			const requestIndex = requests.findIndex((r) => r.id === requestId);
			if (requestIndex !== -1) {
				let newAuthorizedStatus = !currentAuthorizedStatus;
				requests[requestIndex]!.authorized = newAuthorizedStatus;
				requests[requestIndex]!.authorized_by = newAuthorizedStatus ? user() : undefined;
			}
			toast.success(
				`Request ${!currentAuthorizedStatus ? 'approved' : 'unapproved'} successfully.`
			);
		} else {
			const errorText = await response.text();
			console.error(`Failed to update request status ${response.statusText}`, errorText);
			toast.error(`Failed to update request status: ${response.statusText}`);
		}
	}

	async function deleteRequest(requestId: string) {
		if (
			!window.confirm(
				'Are you sure you want to delete this season request? This action cannot be undone.'
			)
		) {
			return;
		}
		let response;
		if (isShow) {
			const data = await client.DELETE('/api/v1/tv/seasons/requests/{request_id}', {
				params: {
					path: {
						request_id: requestId
					}
				}
			});
			response = data.response;
		} else {
			const data = await client.DELETE('/api/v1/movies/requests/{movie_request_id}', {
				params: {
					path: {
						movie_request_id: requestId
					}
				}
			});
			response = data.response;
		}
		if (response.ok) {
			// remove the request from the list
			const index = requests.findIndex((r) => r.id === requestId);
			if (index > -1) {
				requests.splice(index, 1);
			}
			toast.success('Request deleted successfully');
		} else {
			console.error(`Failed to delete request ${response.statusText}`, await response.text());
			toast.error('Failed to delete request');
		}
	}
</script>

<Table.Root>
	<Table.Caption>A list of all requests.</Table.Caption>
	<Table.Header>
		<Table.Row>
			<Table.Head>{isShow ? 'Show' : 'Movie'}</Table.Head>
			{#if isShow}
				<Table.Head>Season</Table.Head>
			{/if}
			<Table.Head>Minimum Quality</Table.Head>
			<Table.Head>Wanted Quality</Table.Head>
			<Table.Head>Requested by</Table.Head>
			<Table.Head>Approved</Table.Head>
			<Table.Head>Approved by</Table.Head>
			<Table.Head>Actions</Table.Head>
		</Table.Row>
	</Table.Header>
	<Table.Body>
		{#each requests as request (request.id)}
			{#if filter(request)}
				<Table.Row>
					<Table.Cell>
						{#if isShow}
							{getFullyQualifiedMediaName(
								(request as components['schemas']['RichSeasonRequest']).show
							)}
						{:else}
							{getFullyQualifiedMediaName(
								(request as components['schemas']['RichMovieRequest']).movie
							)}
						{/if}
					</Table.Cell>
					{#if isShow}
						<Table.Cell>
							{(request as components['schemas']['RichSeasonRequest']).season.number}
						</Table.Cell>
					{/if}
					<Table.Cell>
						{getTorrentQualityString(request.min_quality)}
					</Table.Cell>
					<Table.Cell>
						{getTorrentQualityString(request.wanted_quality)}
					</Table.Cell>
					<Table.Cell>
						{request.requested_by?.email ?? 'N/A'}
					</Table.Cell>
					<Table.Cell>
						<CheckmarkX state={request.authorized} />
					</Table.Cell>
					<Table.Cell>
						{request.authorized_by?.email ?? 'N/A'}
					</Table.Cell>
					<!-- TODO: ADD DIALOGUE TO MODIFY REQUEST -->
					<Table.Cell class="flex max-w-[150px] flex-col gap-1">
						{#if user().is_superuser}
							<Button
								class=""
								size="sm"
								onclick={() => approveRequest(request.id!, request.authorized)}
							>
								{request.authorized ? 'Unapprove' : 'Approve'}
							</Button>
							{#if isShow}
								<Button
									class=""
									size="sm"
									variant="outline"
									onclick={() =>
										goto(
											base +
												'/dashboard/tv/' +
												(request as components['schemas']['RichSeasonRequest']).show.id
										)}
								>
									Download manually
								</Button>
							{:else}
								<Button
									class=""
									size="sm"
									variant="outline"
									onclick={() =>
										goto(
											base +
												'/dashboard/movies/' +
												(request as components['schemas']['RichMovieRequest']).movie.id
										)}
								>
									Download manually
								</Button>
							{/if}
						{/if}
						{#if user().is_superuser || user().id === request.requested_by?.id}
							<Button variant="destructive" size="sm" onclick={() => deleteRequest(request.id!)}
								>Delete
							</Button>
						{/if}
					</Table.Cell>
				</Table.Row>
			{/if}
		{:else}
			<Table.Row>
				<Table.Cell colspan={8} class="text-center">There are currently no requests.</Table.Cell>
			</Table.Row>
		{/each}
	</Table.Body>
</Table.Root>
