import type { PageLoad } from './$types';
import client from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	const importable = await client.GET('/api/v1/movies/importable', { fetch: fetch });
	const movies = await client.GET('/api/v1/movies', { fetch: fetch });

	return { movies: movies.data, importable: importable.data };
};
