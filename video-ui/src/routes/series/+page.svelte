<script lang="ts">
    let { data } = $props();
    import { resolve } from "$app/paths";

    import { capitalize } from '$lib/utils/TextUtils.js';
    import { formatDate } from '$lib/utils/DateUtils.js';
	import type { Series } from '$lib/types/Series.js';
    
    let series: Series[] = $derived(data.series);
</script>

<div class="w-2/3 mx-auto mt-5">
    <h1 class="text-4xl font-semibold">All Series</h1>
    {#each series as s (s.id)}
        <a
            href={resolve(`/series/${s.id}`)}
            data-sveltekit-preload-data="hover"
            class=""
        >
            <div class="my-4 border border-gray-300 rounded-md p-2 w-1/3">
                <h2 class="text-xl">{capitalize(s.name)}</h2>
                <p class="text-sm text-gray-400">Created at: {formatDate(s.created_at)}</p>
            </div>
        </a>
    {/each}
</div>