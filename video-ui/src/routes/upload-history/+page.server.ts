
export async function load({ fetch }) {

    const response = await fetch('http://127.0.0.1:8000/api/list/videos');

    if (!response.ok) {
        throw new Error(
            `Failed to fetch videos: ${response.status}`
        );
    }

    return {
		videos: await response.json()
	};
}