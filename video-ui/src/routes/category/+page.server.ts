import type { PageServerLoad } from './$types';
// import { API_URL } from '$env/static/private';
// import { env } from '$env/dynamic/private';

export const load: PageServerLoad = async ({fetch}) => {
    // const response = await fetch('http://127.0.0.1:8000/api/category');
    const response = await fetch('http://backend:8000/api/category');

    if (!response.ok) {
        throw new Error('Failed to fetch categories');
    }

    const categories = await response.json();

    return {
        categories
    };
};