import type { PageLoad } from './$types';
import client from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	const movies = await client.GET('/api/v1/movies', { fetch: fetch });

	return { movies: movies.data };
};
