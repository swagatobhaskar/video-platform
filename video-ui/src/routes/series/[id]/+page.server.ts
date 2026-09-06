import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, fetch }) => {
    const res = await fetch(
        `http://backend:8000/api/series/${params.id}`
    );

    if (!res.ok) {
        throw new Error('Failed to fetch series');
    }

    const series = await res.json();

    return {
        series
    };
};