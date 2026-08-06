import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, fetch }) => {
    const res = await fetch(
        `http://127.0.0.1:8000/api/series/${params.id}`
    );

    if (!res.ok) {
        throw new Error('Failed to fetch series');
    }

    const series = await res.json();

    return {
        series
    };
};