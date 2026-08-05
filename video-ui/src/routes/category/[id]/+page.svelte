<script lang="ts">
    let { data } = $props();

    import { capitalize } from '$lib/utils/TextUtils.js';
    import { formatDate } from '$lib/utils/DateUtils.js';
	import type { Category } from '$lib/types/Category.js';
    
    let category: Category = $derived(data.category);
    let editName = $state<boolean>(false);
    let newName = $state<string>('');
    let nameChangeError = $state<string>('');

    function handleEditName() {
        editName = true;
        newName = data.category.name;
    }

    const handleNameChange = async () => {
        if (!newName.trim()) return;

        // It has to be FormData since the backend accepts it as Form
        // It doesn't require setting header in request
        const formData = new FormData();
        formData.append('name', newName);

        try {
            const resp = await fetch(`http://127.0.0.1:8000/api/category/${data.category.id}`, {
                method: 'PATCH',
                body: formData
            });

            if (!resp.ok) {
                const error = await resp.json();
                nameChangeError = error.detail ?? 'Update failed';
                return;
            }

            const updatedCategory = await resp.json();

            category.name = updatedCategory.name;
            category.updated_at = updatedCategory.updated_at;

            editName = false;
        } catch (err) {
            nameChangeError = err instanceof Error ? err.message : String(err);
        }
    }

</script>

<div class="w-4/5 mx-auto mt-5">
    <div class="flex flex-row">

        <!-- Left Section: Image + Name with edit and delete option -->
        <section class="w-1/4 h-screen">
            <div class="relative">
                <img 
                    src={category.r2_category_image_key}
                    alt={category.name }
                    height="600"
                    width="600"
                    class="flex-none aspect-square w-full object-cover rounded-md"
                />
                <div class="absolute bottom-5 right-5 z-50 p-2 bg-white rounded-md">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
                    </svg>
                </div>
            </div>

            <div class="space-y-3 mt-2">
                {#if editName}
                    <div class="flex items-center gap-3 w-full my-1">
                        <input
                            type="text"
                            bind:value={newName}
                            class="border rounded px-2 py-1"
                        />

                        <button class="bg-indigo-500 text-white px-3 py-1 rounded" onclick={handleNameChange}>
                            Save
                        </button>

                        <button
                            class="bg-gray-600 text-white px-3 py-1 rounded"
                            onclick={() => editName = false}
                        >
                            Cancel
                        </button>
                        {#if nameChangeError}
                            {nameChangeError}
                        {/if}
                    </div>
                {:else}
                    <h1 class="font-bold text-gray-700 text-4xl flex flex-row space-x-10 relative">
                        {capitalize(category.name)}
                        <button aria-label="Edit category name" onclick={handleEditName} class="absolute left-40 p-2 bg-white rounded-md shadow-sm shadow-gray-300">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                                <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
                            </svg>
                        </button>
                    </h1>
                {/if}
                <p>Created at: {formatDate(category.created_at)}</p>
                <p>Updated at: {formatDate(category.updated_at)}</p>
            </div>
        </section>

        <!-- Right section: Linked Videos -->
        <section class="w-3/4 ml-10 text-left">
            <p class="text-4xl font-semibold">Videos in {capitalize(category.name)} category</p>
            {#each category.videos as video (video.id)}
                <div class="">
                    <img src={video.thumbnail_object_key} alt="thumbnail" />
                    <p>{video.id}</p>
                    <p>{video.title}</p>
                </div>
            {/each}
        </section>
    </div>
    
</div>