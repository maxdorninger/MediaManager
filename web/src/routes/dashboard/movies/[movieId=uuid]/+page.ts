import type { PageLoad } from './$types';
import { env } from '$env/dynamic/public';
import { error } from '@sveltejs/kit';
import client from "$lib/api";

export const load: PageLoad = async ({ params, fetch }) => {
	const { data } = await client.GET('/api/v1/movies/{movie_id}', {
		fetch: fetch,
		params: {
			path: {
				movie_id: params.movieId
			},
		}
	});

	return { movie: data };
};
