// import { API_URL } from '$env/static/private';

export async function load({ fetch }) {

    const response = await fetch('/api/video/upload-history');

    if (!response.ok) {
        throw new Error(
            `Failed to fetch video upload history: ${response.status}`
        );
    }

    return {
		videos: await response.json()
	};
}