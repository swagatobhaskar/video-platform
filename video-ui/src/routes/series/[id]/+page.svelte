<script lang="ts">
    let { data } = $props();

    import { capitalize } from '$lib/utils/TextUtils.js';
    import { formatDate } from '$lib/utils/DateUtils.js';
	import type { Category } from '$lib/types/Category.js';
    
    let series: Category = $derived(data.series);
</script>

<div class="w-1/3 mx-auto">
    <h2 class="my-5 text-3xl font-semibold">Videos in {capitalize(series.name)} series</h2>
    {#if series.videos.length === 0}
        <p class="text-gray-600 text-xl">No video</p>
    {:else}
        {#each series.videos as video (video.id)}
            <div class="p-2 border border-gray-300 rounded-md">
                <h2 class="text-lg">{capitalize(video.title)}</h2>
            </div>
        {/each}
    {/if}
</div>