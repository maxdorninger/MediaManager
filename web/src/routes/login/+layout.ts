import type {LayoutLoad} from './$types';
import {env} from '$env/dynamic/public';

const apiUrl = env.PUBLIC_API_URL;

export const load: LayoutLoad = async ({fetch}) => {
    const response = await fetch(apiUrl + '/auth/metadata', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    });

    return {oauthProvider: await response.json()};
};