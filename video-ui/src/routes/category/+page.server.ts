import type { PageServerLoad } from './$types';
import { API_URL } from '$env/static/private';

export const load: PageServerLoad = async ({fetch}) => {
    // const response = await fetch('http://127.0.0.1:8000/api/category');
    // console.log("API_URL: ", API_URL);
    const response = await fetch(`${API_URL}/category`);  // backend is docker compose service name

    if (!response.ok) {
        throw new Error('Failed to fetch categories');
    }

    const categories = await response.json();

    return {
        categories
    };
};