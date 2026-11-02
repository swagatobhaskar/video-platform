<script lang="ts">
    import type { MediaPlayerClass } from 'dashjs';
    // let { videoId, poster = undefined, autoplay = false } : { videoId: string | undefined; poster?: string; autoplay?: boolean } = $props();

    let {
        src,
        poster = undefined,
        autoplay = false
    }: { src?: string | null; poster?: string | null; autoplay?: boolean } = $props();

    let video = $state<HTMLVideoElement>();

    $effect(() => {
        const el = video;
        const url = src; //dashManifestKey; // read here so the effect re-runs when src changes
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
    poster = {poster ?? undefined}
    controls
    playsinline
    // class="w-full backdrop:gray-900/80 rounded-md shadow-lg"
    // class="aspect-video w-full mx-auto bg-black"
    class="aspect-video max-h-[calc(100vh-9rem)] w-full bg-black"
></video>
