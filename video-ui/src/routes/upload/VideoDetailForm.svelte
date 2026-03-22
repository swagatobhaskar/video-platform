<script lang="ts">
    let title = $state<string>('');
    let description = $state<string>('');
    let currentTag = $state("");
    let seoTags = $state<string[]>([]);
    
    let category = $state<string>('');
    // 1. Define your categories (usually fetched from FastAPI)
	const categories = [
		{ id: 1, name: 'Technology' },
		{ id: 2, name: 'Lifestyle' },
		{ id: 3, name: 'Education' }
	];

	// 2. State for the selected ID
	let selectedCategoryId = $state<number | string>("");

	// 3. Derived state (optional) to get the full object if needed
	let selectedCategory = $derived(
		categories.find(c => c.id === Number(selectedCategoryId))
	);

    function addTag() {
        const trimmedCurrentTag = currentTag.trim();
        // Prevent empty tags or duplicates
        if (trimmedCurrentTag && !seoTags.includes(trimmedCurrentTag)) {
            seoTags.push(trimmedCurrentTag);
            currentTag = ""; // Clear input after adding
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') {
            e.preventDefault(); // Stop form from submitting
            addTag();
	    }
	}

    async function handleFormSubmit(e: Event) {
        e.preventDefault();
        // Here you would typically send the form data to your FastAPI backend
        const formData = {
            title,
            description,
            category_id: selectedCategoryId,
            seoTags
        };
        console.log("Form submitted with data:", formData);

    }

    async function handleSaveDraft() {

    }
</script>

<div class="p-8 max-w-lg mx-auto bg-white rounded-xl shadow-md space-y-4">
    <h2 class="text-2xl font-bold text-gray-800">Video Metadata</h2>

    <form onsubmit={handleFormSubmit} class="flex flex-col gap-y-2 w-full px-3 items-center">
        <label for="title">
            <span class="">Video Title</span>
            <input
                type="text"
                name="title"
                required
                placeholder="Add video title the user will see"
                bind:value={title}
                class=""
            />
        </label>

        <label>
            <span class="">Description</span>
            <textarea
                name="description"
                placeholder="Add a short video description"
                bind:value={description}
                class=""
            ></textarea>
        </label>

        <label for="category">
            <span class="">Category</span>
            <select
                id="category"
                bind:value={selectedCategoryId}
                class=""
            >
                <option value="" disabled>-- Choose a category --</option>
                {#each categories as category}
                    <option value={category.id}>
                        {category.name}
                    </option>
                {/each}
            </select>
        </label>

        <!-- SEO Tags -->
        <div class="">
            <label for="tag-select">Enter SEO tags</label>

            <div class="input-group">
                <input
                    id="tag-input"
                    type="text"
                    name="tag"
                    bind:value={currentTag}
                    placeholder="Enter an SEO tag"
                    onkeydown={handleKeydown}
                />
                <button type="button" onclick={addTag} class="">Add Tag</button>
            </div>

            <div class="tag-list">
                {#if seoTags.length === 0}
                    <p>Tag list is empty. Add few tags.</p>
                {:else}
                    {#each seoTags as tag, index}
                        <span class="">
                            {tag}
                            <button type="button" onclick={() => seoTags.splice(index, 1)} class="">x</button>
                        </span>
                    {/each}
                {/if}
            </div>
        </div>

        <div class="">
            <button class="" type="submit">Publish</button>
            <button class="" type="button" onclick={handleSaveDraft}>Save Draft</button>
        </div>
    </form>
</div>