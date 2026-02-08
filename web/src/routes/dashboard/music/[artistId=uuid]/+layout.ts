import type { LayoutLoad } from './$types';
import client from '$lib/api';

export const load: LayoutLoad = async ({ params, fetch }) => {
	const artist = client.GET('/api/v1/music/artists/{artist_id}', {
		fetch: fetch,
		params: { path: { artist_id: params.artistId } }
	});
	const torrents = client.GET('/api/v1/music/artists/{artist_id}/torrents', {
		fetch: fetch,
		params: { path: { artist_id: params.artistId } }
	});

	return {
		artistData: await artist.then((x) => x.data),
		torrentsData: await torrents.then((x) => x.data)
	};
};
