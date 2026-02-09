import type { LayoutLoad } from './$types';
import client from '$lib/api';

export const load: LayoutLoad = async ({ params, fetch }) => {
	const author = client.GET('/api/v1/books/authors/{author_id}', {
		fetch: fetch,
		params: { path: { author_id: params.authorId } }
	});
	const torrents = client.GET('/api/v1/books/authors/{author_id}/torrents', {
		fetch: fetch,
		params: { path: { author_id: params.authorId } }
	});

	return {
		authorData: await author.then((x) => x.data),
		torrentsData: await torrents.then((x) => x.data)
	};
};
