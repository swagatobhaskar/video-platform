import type { PageLoad } from "./$types";
import { error } from "@sveltejs/kit";

// Since this page is purely client-side (File APIs, XHR, dashjs), turn SSR off for it.
export const ssr = false;

export const load: PageLoad = async ({ params, fetch, depends }) => {
    const videoId = params.videoId;

    if (!videoId) return { videoId: undefined, video: null, formData: null}; //, upload: null };

    // lets us re-run load manually via invalidate()
    depends(`app:video:${videoId}`);

    const [viewRes, formRes] = await Promise.all([  // , uploadRes
        fetch(`/api/video/view/${videoId}`),
        fetch(`/api/video/${videoId}`),
        // fetch(`/api/video/transcoded-upload/${videoId}/status`),
        // backend already has the answer: TranscodedUploadSession.status.
        // Add it to the /api/video/view/{id} response, along with the counts for a resume message:
    ]);

    // if (!viewRes.ok || !formRes.ok) throw error(viewRes.status || 500, 'Could not load video');

    if (!viewRes.ok) error(viewRes.status, 'Could not load video');
    if (!formRes.ok) error(formRes.status, 'Could not load video form data');

    return {
        videoId,
        video: await viewRes.json(),
        formData: await formRes.json(),
        // upload: uploadRes.ok ? await uploadRes.json() : null,
    };
};
