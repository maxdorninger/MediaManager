import type { PageLoad } from './$types';
import client from '$lib/api';

export const load: PageLoad = async ({ params, fetch }) => {
	const book = client.GET('/api/v1/books/books/{book_id}', {
		fetch: fetch,
		params: {
			path: {
				book_id: params.bookId
			}
		}
	});
	const files = client.GET('/api/v1/books/books/{book_id}/files', {
		fetch: fetch,
		params: {
			path: {
				book_id: params.bookId
			}
		}
	});

	return {
		book: await book.then((x) => x.data),
		bookFiles: await files.then((x) => x.data)
	};
};
