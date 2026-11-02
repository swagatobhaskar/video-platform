import type { VideoView } from "$lib/types/VideoView";

/** 3725 -> "PT1H2M5S" (ISO 8601 duration, as schema.org expects). */
function isoDuration(totalSeconds: number): string {
    const t = Math.max(0, Math.round(totalSeconds));
    const h = Math.floor(t / 3600);
    const m = Math.floor((t % 3600) / 60);
    const s = t % 60;
    return `PT${h ? `${h}H` : ''}${m ? `${m}M` : ''}${s || (!h && !m) ? `${s}S` : ''}`;
}

interface Options {
    /** Absolute URL of the watch page. */
    pageUrl: string;
    /** Absolute URL of the thumbnail image. */
    thumbnailUrl?: string | null;
    /** Absolute URL of the playable video/manifest. */
    contentUrl?: string | null;
}

export function VideoJsonLd(video: VideoView, { pageUrl, thumbnailUrl, contentUrl }: Options ){
    // JSON.stringify drops undefined values, so missing fields simply vanish.
    return {
        '@context': 'https://schema.org',
        '@type': 'VideoObject',
        name: video.title,
        description: video.meta_description || video.description || video.title,
        thumbnailUrl: thumbnailUrl ? [thumbnailUrl] : undefined,
        uploadDate: video.published_at ?? undefined,
        duration: video.duration_seconds != null ? isoDuration(video.duration_seconds) : undefined,
        contentUrl: contentUrl ?? undefined,
        inLanguage: video.language ?? undefined,
        url: pageUrl,
        interactionStatistic: {
            '@type': 'InteractionCounter',
            interactionType: {'@type': 'WatchAction'},
            userInteractionCount: video.view_count
        }
    };
}

/** Serialize for inline <script>; escaping "<" stops a "</script>" in your data from breaking out. */
export function serializeJsonLd(data: unknown): string {
    return JSON.stringify(data).replace(/</g, '\\u003c');
}
