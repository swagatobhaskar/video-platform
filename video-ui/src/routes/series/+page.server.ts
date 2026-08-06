import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({fetch}) => {
    const response = await fetch('http://127.0.0.1:8000/api/series');

    if (!response.ok) {
        throw new Error('Failed to fetch series');
    }

    const series = await response.json();

    return {
        series
    };
};