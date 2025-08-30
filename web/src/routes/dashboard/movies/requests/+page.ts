import {env} from '$env/dynamic/public';
import type {PageLoad} from './$types';
import client from "$lib/api";

const apiUrl = env.PUBLIC_API_URL;
export const load: PageLoad = async ({fetch}) => {
    const {data} = await client.GET('/api/v1/movies/requests', {fetch: fetch});

    return {
        requestsData: data
    };
};
