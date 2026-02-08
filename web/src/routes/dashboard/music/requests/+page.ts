import type { PageLoad } from './$types';
import client from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	const { data } = await client.GET('/api/v1/music/albums/requests', { fetch: fetch });
	return {
		requestsData: data
	};
};
