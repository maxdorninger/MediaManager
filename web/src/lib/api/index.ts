import createClient from "openapi-fetch";
import type { paths } from "./api.d.ts";
import { env } from '$env/dynamic/public';

const client = createClient<paths>({ baseUrl: env.PUBLIC_API_URL });
export default client;