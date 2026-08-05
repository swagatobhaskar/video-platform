<script lang="ts">

    import { onMount } from "svelte";
    import type { VideoList } from "$lib/types/VideoList"
    import VideoPublishProgressItem from "./VideoPublishProgressItem.svelte";

    const tabs = ["all", "draft", "published", "archived"];
    let activeTab = $state(tabs[0]);    // Default: Draft

    let allVideos = $state<VideoList[]>([]);
    
    let loading = $state(false);
	let error = $state<string | null>(null);

    const filteredVideos = $derived.by(() => {
        if (activeTab === "all") return allVideos;

        return allVideos.filter(
            video => video.publication_status === activeTab
        );
    });

    const handleTab = (tab: string) => {
        activeTab = tab;
    };

    const fetchAllVideos = async () => {
        try {
            loading = true;
            const response = await fetch('http://127.0.0.1:8000/api/video');

            if (!response.ok) {
				throw new Error(
					`Failed to fetch videos: ${response.status}`
				);
			}

            allVideos = await response.json();
            // console.log(videos);
        } catch(err) {
            console.error(err);
            error = err instanceof Error
				? err.message
				: "Unknown error";
        } finally {
            loading = false;
        }
    };

    onMount(fetchAllVideos);
</script>

<main class="w-2/4 mx-auto">
    <div class="flex justify-center py-6">
        <div class="flex w-full max-w-4xl border-x border-gray-400">
            {#each tabs as tab (tab)}
                <button
                    onclick={() => handleTab(tab)} //activeTab = tab}
                    class="relative flex-1 py-3 text-lg transition-colors
                           border-r last:border-r-0 border-gray-400 cursor-pointer"
                >
                    {tab}

                    {#if activeTab === tab}
                        <span
                            class="absolute bottom-0 left-0 h-0.5 w-full bg-black"
                        ></span>
                    {/if}
                </button>
            {/each} 
        </div>
    </div>
    <section class="p-4 w-full h-[calc(100%-5rem)] overflow-y-auto">
        {#if loading}
            <p>Loading videos...</p>
        {:else if error}
            <p>{error}</p>
        {:else if filteredVideos.length === 0}
            <p class="items-center text-center font-semibold text-3xl text-gray-400">No video</p>
        {:else}
            {#each filteredVideos as video (video.id)}
                <VideoPublishProgressItem {video} />
            {/each}
        {/if}
    </section>
</main>