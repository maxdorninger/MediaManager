import type { PageLoad } from './$types';
import client from '$lib/api';

export const load: PageLoad = async ({ params, fetch }) => {
	const album = client.GET('/api/v1/music/albums/{album_id}', {
		fetch: fetch,
		params: {
			path: {
				album_id: params.albumId
			}
		}
	});
	const files = client.GET('/api/v1/music/albums/{album_id}/files', {
		fetch: fetch,
		params: {
			path: {
				album_id: params.albumId
			}
		}
	});

	return {
		album: await album.then((x) => x.data),
		albumFiles: await files.then((x) => x.data)
	};
};
