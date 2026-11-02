import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import type { VideoView } from '$lib/types/VideoView';
 
export const load: PageServerLoad = async ({ params, fetch }) => {
	const res = await fetch(`http://backend:8000/api/video/view/${params.videoId}`);
	if (res.status === 404) error(404, 'Video not found');
	if (!res.ok) error(res.status, 'Could not load this video');
 
	const video: VideoView = await res.json();
	return { video };
};
