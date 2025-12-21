import type { PageLoad } from './$types';
import client from '$lib/api';

export const load: PageLoad = async ({ params, fetch }) => {
	const movie = client.GET('/api/v1/movies/{movie_id}', {
		fetch: fetch,
		params: {
			path: {
				movie_id: params.movieId
			}
		}
	});
	const files = client.GET('/api/v1/movies/{movie_id}/files', {
		fetch: fetch,
		params: {
			path: {
				movie_id: params.movieId
			}
		}
	});

	return { movie: await movie.then((x) => x.data), movieFiles: await files.then((x) => x.data) };
};
