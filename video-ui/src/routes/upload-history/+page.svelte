<script lang="ts">

    // let { data } = $props();
    // const videos = $derived(data.uploads);

    import { onMount } from "svelte";

    // const filters = ['draft', 'published', 'archived'];

    type Video = {
        id: string;
        title: string;
        object_key: string;
        publication_status: string;
        created_at: Date;
    }

    let videos = $state<Video[]>([]);
    let loading = $state(false);
	let error = $state<string | null>(null);

    const fetchAllVideos = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/video', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
            });

            if (!response.ok) {
				throw new Error(
					`Failed to fetch videos: ${response.status}`
				);
			}

            videos = await response.json();
            // console.log(videos);
        } catch(err) {
            console.error(err);
            error = err instanceof Error
				? err.message
				: "Unknown error";
        }
    };

    onMount(fetchAllVideos);
</script>

<main class="">
    {#if loading}
        <p>Loading videos...</p>
    {:else if error}
        <p>{error}</p>
    {:else}
        {#each videos as video (video.id)}
            <p>{video.id}</p>
            <p>{video.title}</p>
            <p>{video.publication_status}</p>
            <p>{video.created_at}</p>
        {/each}
    {/if}    
</main>
