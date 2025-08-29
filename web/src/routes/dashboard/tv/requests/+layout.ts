import { env } from '$env/dynamic/public';
import type { LayoutLoad } from './$types';
import client from "$lib/api";

const apiUrl = env.PUBLIC_API_URL;
export const load: LayoutLoad = async ({ fetch }) => {
	const { data, error } = await client.GET('/api/v1/tv/seasons/requests', { fetch: fetch });
	return {
		requestsData: data
	};
};
