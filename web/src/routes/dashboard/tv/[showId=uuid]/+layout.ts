import type { LayoutLoad } from './$types';
import client from '$lib/api';

export const load: LayoutLoad = async ({ params, fetch }) => {
	const show = await client.GET('/api/v1/tv/shows/{show_id}', {
		fetch: fetch,
		params: { path: { show_id: params.showId } }
	});
	const torrents = await client.GET('/api/v1/tv/shows/{show_id}/torrents', {
		fetch: fetch,
		params: { path: { show_id: params.showId } }
	});

	return {
		showData: show.data,
		torrentsData: torrents.data
	};
};
