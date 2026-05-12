<script lang="ts">
    let { workflow } = $props();

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
</script>

<div class="h-full border-2 border-gray-200 rounded-lg shadow-md shadow-gray-200 p-8 flex flex-col justify-evenly">

    <!-- Video Title -->
    <label for="title" class="">
        Title
        <input
            type="text"
            name="title"
            placeholder="Video title"
            required
            class="w-full border-2 border-gray-300 rounded-md p-2 mt-1 focus:outline-none
                focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            bind:value={formController.formData.title}
        />
    </label>

    <!-- Video Description -->
    <label for="title" class="">
        Description
        <textarea
            name="description"
            placeholder="Video description"
            maxlength="400"
            required
            class="w-full h-32 overflow-y-auto resize-none border-2 border-gray-300
                rounded-md p-2 mt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            bind:value={formController.formData.description}
        ></textarea>
    </label>

    <!-- Video Category -->
    <label for="title" class="">
        Category
        <select
            name="category"
            required
            class="w-full border-2 border-gray-300 rounded-md p-2 mt-1 focus:outline-none
                focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            bind:value={formController.formData.category}
        >
            <option value="">Select a category</option>
            <option value="technology">Technology</option>
            <option value="music">Music</option>
            <option value="gaming">Gaming</option>
        </select>
    </label>

    <!-- SEO Tags -->
    <div class="relative w-full">
        <label for="seoTags" class="block mb-1">SEO Tags</label>

        <div class="flex gap-2 items-stretch">
            <input
                type="text"
                name="seoTag"
                bind:value={seoTagEntry}
                placeholder="Add an item for SEO"
                class="flex-1 border-2 border-gray-300 rounded-md p-2 pr-36 mt-1 focus:outline-none
                    focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onkeydown={(e) => e.key === 'Enter' && addItemToSEOList()}
            />
            <button
                type="button"
                class="px-3 py-2 bg-blue-500 text-white rounded-md text-sm
                    hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
                onclick={addItemToSEOList}
                disabled={!seoTagEntry.trim()}
                onkeydown={(e) => e.key === 'Enter' && addItemToSEOList()}
            >
                Add tag
            </button>
        </div>
       
        <div class="mt-2 flex flex-wrap items-start gap-2 border border-gray-200 rounded-md p-2 min-h-32 max-h-max">
            {#if selectedSEOTagsList.length === 0}
                <p class="text-gray-500">No SEO tags added yet.</p>
            {:else}
                
                {#each selectedSEOTagsList as tag (tag.id)}
                    <div class="flex items-center bg-indigo-200 rounded-sm p-1.5">
                        <span>{tag.value}</span>

                        <button
                            type="button"
                            class="ml-2 text-gray-500 hover:text-gray-700 text-2xl"
                            onclick={() => removeItemFromSEOList(tag.id)}
                        >
                            &times;
                        </button>
                    </div>
                {/each}

            {/if}
        </div>
    </div>

</div>