<script lang="ts">
    let { src, poster = undefined, autoplay = false } : { src: string; poster?: string; autoplay?: boolean } = $props();

    let video = $state<HTMLVideoElement>();

    $effect(() => {
        if (!video) return;

        let player: any;
        let cancelled = false;
        const el = video;
        const url = src; // read here so the effect re-runs when src changes

        (async () => {
            // dynamic import keeps dash.js out of SSR (it touches window/MediaSource)
            const mod = await import('dashjs');
            if (cancelled) return;
            const dashjs = (mod as any).default ?? mod;
            player = dashjs.MediaPlayer().create();
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
