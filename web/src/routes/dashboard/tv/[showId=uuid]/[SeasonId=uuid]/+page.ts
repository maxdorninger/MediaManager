import type { PageLoad } from './$types';
import client from '$lib/api';

export const load: PageLoad = async ({ fetch, params }) => {
	const season = client.GET('/api/v1/tv/seasons/{season_id}', {
		fetch: fetch,
		params: {
			path: {
				season_id: params.SeasonId
			}
		}
	});
	const episodeFiles = client.GET('/api/v1/tv/seasons/{season_id}/files', {
		fetch: fetch,
		params: {
			path: {
				season_id: params.SeasonId
			}
		}
	});
	return {
		files: await episodeFiles.then((x) => x.data),
		season: await season.then((x) => x.data)
	};
};
