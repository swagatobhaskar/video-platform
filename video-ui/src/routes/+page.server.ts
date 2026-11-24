import type { PageServerLoad } from "./$types";
import { error } from "@sveltejs/kit";

export const load: PageServerLoad = async () => {

    try {
        const response = await fetch('http://backend:8000/api/video?status=published');

        if (!response.ok) {
            console.error('Backend returned:', response.status, await response.text());

            error(response.status, 'Could not load videos');
        }

        const videos = await response.json();

        return { videos };

    } catch (err) {
        console.error('Video API request failed:', err);

        if (err && typeof err === 'object' && 'status' in err) {
            throw err;
        }

        error(500, 'Could not connect to video API');
    }
};
