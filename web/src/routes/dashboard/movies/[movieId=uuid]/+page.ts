import type { PageLoad } from './$types';
import { env } from '$env/dynamic/public';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params, fetch }) => {
	const res = await fetch(`${env.PUBLIC_API_URL}/movies/${params.movieId}`, {
		credentials: 'include'
	});
	if (!res.ok) throw error(res.status, `Failed to load movie`);
	const movieData = await res.json();
	console.log('got movie data', movieData);
	return { movie: movieData };
};
