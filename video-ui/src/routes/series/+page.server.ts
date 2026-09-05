import type { PageServerLoad } from './$types';
import { API_URL } from '$env/static/private';

export const load: PageServerLoad = async ({fetch}) => {
    const response = await fetch(`${API_URL}/series`);

    if (!response.ok) {
        throw new Error('Failed to fetch series');
    }

    const series = await response.json();

    return {
        series
    };
};