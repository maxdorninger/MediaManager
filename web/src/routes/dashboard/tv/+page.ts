import client from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const { data } = await client.GET('/api/v1/tv/shows', { fetch: fetch });
	return { tvShows: data };
};
