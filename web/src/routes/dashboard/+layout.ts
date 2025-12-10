import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { resolve } from '$app/paths';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import client from '$lib/api';

export const load: LayoutLoad = async ({ fetch }) => {
	const { data, error } = await client.GET('/api/v1/users/me', { fetch: fetch });

	if (error) {
		console.log('unauthorized, redirecting to login');
		if (browser) {
			await goto(resolve('/login', {}));
		} else {
			throw redirect(303, resolve('/login', {}));
		}
	}
	return {
		user: data,
		tvShows: await client.GET('/api/v1/tv/shows', { fetch: fetch }).then((res) => res.data),
		movies: await client.GET('/api/v1/movies', { fetch: fetch }).then((res) => res.data)
	};
};
