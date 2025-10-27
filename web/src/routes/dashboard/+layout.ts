import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { resolve } from '$app/paths';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import client from '$lib/api';

export const load: LayoutLoad = async ({ fetch }) => {
	const { data, response } = await client.GET('/api/v1/users/me', { fetch: fetch });

	if (!response.ok) {
		console.log('unauthorized, redirecting to login');
		if (browser) {
			await goto(resolve('/login', {}));
		} else {
			throw redirect(303, resolve('/login', {}));
		}
	}
	return { user: data };
};
