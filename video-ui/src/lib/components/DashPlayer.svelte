<script lang="ts">
    import type { MediaPlayerClass } from 'dashjs';
    // let { videoId, poster = undefined, autoplay = false } : { videoId: string | undefined; poster?: string; autoplay?: boolean } = $props();
    let { poster = undefined, autoplay = false } : { poster?: string; autoplay?: boolean } = $props();

    let video = $state<HTMLVideoElement>();
    let dashManifestKey = $state<string | undefined>(undefined);

    const videoId = "13c7c8b4-0a35-4840-9fe8-5b3c9333d65b";

    // 1. Fetch the object key whenever videoId changes
    $effect(() => {
        if (!videoId) {
            console.error("Video Id Not found!");
            return;
        }

        const abortController = new AbortController();
        dashManifestKey = undefined; // clear the previous video's key

        (async () => {
            try {
                const resp = await fetch(`/api/video/${videoId}`, {
                    signal: abortController.signal,
                });

                if (!resp.ok) {
                    throw new Error(`Failed to fetch object key: ${resp.status}`);
                }
                const data = await resp.json();
                dashManifestKey = data.dash_manifest_key;

            } catch (error) {
                if (abortController.signal.aborted) return; // expected on cleanup
                console.error("Failed to get object key:", error);
            }
        }) ();

        // Runs when videoId changes or this effect is destroyed.
        return () => abortController.abort();
    });

    // 2. Create the player once we have both the <video> element and the URL
    $effect(() => {
        const el = video;
        const url = dashManifestKey; // read here so the effect re-runs when src changes
        if (!el || !url) return;

        let player: MediaPlayerClass | undefined;
        let cancelled = false;

        (async () => {
            // dynamic import keeps dash.js out of SSR (it touches window/MediaSource)
            const { MediaPlayer } = await import('dashjs');
            if (cancelled) return;
            player = MediaPlayer().create();
            player.initialize(el, url, autoplay);
        }) ();

        return () => {
            cancelled = true;
            player?.destroy();
        };
    });
</script>

<video
    bind:this={video}
    {poster}
    controls
    playsinline
    class="w-full"
>
</video>
