import createClient from 'openapi-fetch';
import type { paths } from './api.d.ts';
import { env } from '$env/dynamic/public';
import { autoLogoutMiddleware, loggingMiddleware } from '$lib/api/middlewares.ts';

const client = createClient<paths>({ baseUrl: env.PUBLIC_API_URL, credentials: 'include' });
client.use(loggingMiddleware, autoLogoutMiddleware);

export default client;
