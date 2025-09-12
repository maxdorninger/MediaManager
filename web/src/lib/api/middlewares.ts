import { handleLogout } from '$lib/utils.ts';
import type { Middleware } from 'openapi-fetch';

export const loggingMiddleware: Middleware = {
	async onRequest({ request }) {
		console.log(`Requesting ${request.method} ${request.url}`);
		return request;
	},
	async onResponse({ request, response }) {
		if (!response.ok) {
			console.error(`Request to ${request.url} failed with status ${response.status}`);
		} else {
			console.log(`Request to ${request.url} succeeded with status ${response.status}`);
		}
		return response;
	},
	async onError({ error }) {
		return new Error('Oops, fetch failed', { cause: error });
	}
};

export const autoLogoutMiddleware: Middleware = {
	async onResponse({ request, response }) {
		if (response.status === 401 && !request.url.endsWith('/auth/cookie/logout')) {
			console.log(`Request to ${request.url} returned HTTP Error Code 401, logging out...`);
			await handleLogout();
		}
		if (response.status === 403) {
			console.log(
				`Request to ${request.url} returned HTTP Error Code 403, this shouldn't happen, consider opening a bug report!`
			);
		}
		return response;
	}
};
