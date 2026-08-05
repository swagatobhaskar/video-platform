import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({fetch}) => {
    const response = await fetch('http://127.0.0.1:8000/api/category');

    if (!response.ok) {
        throw new Error('Failed to fetch users');
    }

    const categories = await response.json();

    return {
        categories
    };
};