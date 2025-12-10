import client from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const tvShows = await client.GET('/api/v1/tv/shows', { fetch: fetch });

	return { tvShows: tvShows.data };
};
