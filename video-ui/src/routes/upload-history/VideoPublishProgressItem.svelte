<script lang="ts">
    // import type { VideoDetail } from "$lib/types/VideoDetail";

    let { video } = $props();

    
</script>

<main class="my-5 p-4 min-h-28 border border-gray-300 rounded-lg">
    <div class="flex flex-col justify-evenly">
        <p
            class={[
                "rounded-sm px-2 py-1 w-fit text-sm font-medium",
                {
                    "bg-green-100 text-green-700": video.publication_status === "published",
                    "bg-yellow-100 text-yellow-700": video.publication_status === "draft",
                    "bg-gray-200 text-gray-700": video.publication_status === "archived"
                }
            ]}
        >
            {video.publication_status}
        </p>
        <p class="text-lg font-semibold">{video.title}</p>
        <p class="text-sm text-gray-600">Published at: {new Date(video.published_at).toLocaleString()}</p>
    </div>
</main>
