<script lang="ts">
    // let { workflow } = $props();

    type SEOTag = {
        id: string;
        value: string;
    };

    let selectedSEOTagsList = $state<SEOTag[]>([]);
    let seoTagEntry = $state<string>('');
    
    import {
        MetadataFormController
    } from "$lib/controllers/metadataFormController.svelte";

    const formController = MetadataFormController();

    const addItemToSEOList = () => {
        const trimmed = seoTagEntry.trim();
        if (!trimmed) return;

        const newTag: SEOTag = {
            id: crypto.randomUUID(),
            value: trimmed
        }
        
        selectedSEOTagsList = [...selectedSEOTagsList, newTag];
        seoTagEntry = '';
    }

    const removeItemFromSEOList = (id: string) => {
        selectedSEOTagsList = selectedSEOTagsList.filter(tag => tag.id !== id);
    }

    // Periodically sync formController's data with DB and switch step
    // $effect(() => {

    // });
</script>

<div class="h-full w-5/6 mx-auto p-8 space-y-8">
    <!-- Header -->
    <!-- <div>
        <h2 class="text-2xl font-bold text-gray-900">
            Video Details
        </h2>

        <p class="mt-1 text-sm text-gray-500">
            Fill out information for your upload
        </p>
    </div> -->

    <!-- Publish / Draft Buton -->
    <div class="w-2/3 border border-gray-200 shadow-md shadow-gray-100 rounded-xl p-5">
        <button class="px-3 py-2 bg-blue-500 text-white rounded-md font-medium cursor-pointer focus:bg-blue-600">Publish</button>
    </div>

    <!-- Video Title -->
    <div class="space-y-2">
        <label
            for="title"
            class="block text-sm font-semibold tracking-wide text-gray-700"
        >
            Video Title
        </label>
        
        <input
            type="text"
            name="title"
            placeholder="Enter the video title"
            required
            bind:value={formController.formData.title}
            class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                transition-all duration-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                focus:outline-none"
        />
    
    </div>

    <!-- Video Description -->
    <div class="space-y-2">
        <div class="flex items-center justify-between">
            <label
                for="description"        
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Description
            </label>

            <span class="text-xs text-gray-400">
                {formController.formData.description.length}/400
            </span>
        </div>

        <textarea
            name="description"
            placeholder="Tell viewers about your video..."
            bind:value={formController.formData.description}
            maxlength="400"
            required
            class="w-full h-36 resize-none rounded-xl border border-gray-300
                bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                transition-all duration-200 focus:border-blue-500 focus:bg-white
                focus:ring-4 focus:ring-blue-100 focus:outline-none"
            // class="w-full h-32 overflow-y-auto resize-none border-2 border-gray-300
            //     rounded-md p-2 mt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        ></textarea>
    </div>


    <!-- Video Category -->
    <div class="space-y-2">
        <label
            for="category"
            class="block text-sm font-semibold tracking-wide text-gray-700"
        >
            Category
        </label>

        <select
            name="category"
            bind:value={formController.formData.category}
            required
            class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3
            text-gray-800 transition-all duration-200
            focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
            focus:outline-none"
        >
            <option value="">Select a category</option>
            <option value="technology">Technology</option>
            <option value="music">Music</option>
            <option value="gaming">Gaming</option>
        </select>
    </div>

    <!-- SEO Tags -->
    <div class="space-y-3">
    
        <div>
            <label
                for="seoTags"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                SEO Tags
            </label>

            <p class="mt-1 text-xs text-gray-500">
                Add keywords to improve discoverability
            </p>
        </div>

        <div class="flex gap-3">
            <input
                type="text"
                name="seoTag"
                bind:value={seoTagEntry}
                placeholder="Add a SEO keyword..."
                onkeydown={(e) =>
                    e.key === 'Enter' && addItemToSEOList()
                }
                class="flex-1 rounded-xl border border-gray-300 bg-gray-50
                px-4 py-3 text-gray-800 placeholder:text-gray-400
                transition-all duration-200
                focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                focus:outline-none"
            />

            <button
                type="button"
                onclick={addItemToSEOList}
                disabled={!seoTagEntry.trim()}
                class="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white
                shadow-lg shadow-blue-200 transition-all duration-200
                hover:bg-blue-700 hover:shadow-blue-300
                disabled:cursor-not-allowed disabled:opacity-40"
            >
                Add
            </button>
        </div>
               
        <!-- Tags Container -->
        <div
            class="flex min-h-30 flex-wrap items-start gap-3 rounded-xl
            border border-dashed border-gray-300 bg-gray-50 p-4"
        >
            {#if selectedSEOTagsList.length === 0}
                <div class="flex items-center text-sm text-gray-400">
                    No SEO tags added yet
                </div>
            {:else}
                {#each selectedSEOTagsList as tag (tag.id)}
                    <div
                        class="group flex items-center gap-2 rounded-lg
                        bg-linear-to-r from-indigo-500 to-blue-500
                        px-4 py-2 text-sm font-medium text-white
                        shadow-md transition-transform duration-200
                        hover:scale-105"
                    >
                        <span>{tag.value}</span>

                        <button
                            type="button"
                            onclick={() => removeItemFromSEOList(tag.id)}
                            class="text-white/80 transition hover:text-white"
                        >
                            &times;
                        </button>
                    </div>
                {/each}
            {/if}
        </div>
    </div>
</div>