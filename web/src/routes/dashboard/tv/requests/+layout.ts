import type { LayoutLoad } from './$types';
import client from '$lib/api';

export const load: LayoutLoad = async ({ fetch }) => {
	const { data } = await client.GET('/api/v1/tv/seasons/requests', { fetch: fetch });
	return {
		requestsData: data
	};
};
