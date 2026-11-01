<script lang="ts">
    import DashPlayer from '$lib/components/DashPlayer.svelte';
    import { page } from '$app/state';

    let videoId = $derived(page?.params?.videoId);
</script>

<main>
    <DashPlayer {videoId} />
</main>
