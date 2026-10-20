<script lang="ts">
    // let { videoId } = $props<{ videoId: string | null }>();
    let { videoId }: { videoId?: string | null } = $props();
    
    type SEOKeyword = {
        id: string;
        value: string;
    };

    let selectedSEOTagsList = $state<SEOKeyword[]>([]);
    let seoTagEntry = $state<string>('');

    let focusKeywordEntry = $state<string>('');
    let selectedFocusKeywordsList = $state<SEOKeyword[]>([]);
    
    let secondaryKeywordEntry = $state<string>('');
    let selectedSecondaryKeywordsList = $state<SEOKeyword[]>([]);
    
    let activeTab = $state("video");

    import {
        MetadataFormController
    } from "$lib/controllers/metadataFormController.svelte";

    const formController = MetadataFormController();

    const addItemToSEOList = () => {
        const trimmed = seoTagEntry.trim();
        if (!trimmed) return;

        const newTag: SEOKeyword = {
            id: crypto.randomUUID(),
            value: trimmed
        }
        
        selectedSEOTagsList = [...selectedSEOTagsList, newTag];
        seoTagEntry = '';
    }

    const removeItemFromSEOList = (id: string) => {
        selectedSEOTagsList = selectedSEOTagsList.filter(tag => tag.id !== id);
    }

    const addItemToFocusKeywordsList = () => {
        const trimmed = focusKeywordEntry.trim();
        if (!trimmed) return;

        const newFocusKeyword: SEOKeyword = {
            id: crypto.randomUUID(),
            value: trimmed
        }
        
        selectedFocusKeywordsList = [...selectedFocusKeywordsList, newFocusKeyword];
        focusKeywordEntry = '';
    }

    const removeItemFromFocusKeywordsList = (id: string) => {
        selectedFocusKeywordsList = selectedFocusKeywordsList.filter(tag => tag.id !== id);
    }

    const addItemToSecondaryKeywordsList = () => {
        const trimmed = secondaryKeywordEntry.trim();
        if (!trimmed) return;

        const newSecondaryKeyword: SEOKeyword = {
            id: crypto.randomUUID(),
            value: trimmed
        }
        
        selectedSecondaryKeywordsList = [...selectedSecondaryKeywordsList, newSecondaryKeyword];
        secondaryKeywordEntry = '';
    }

    const removeItemFromSecondaryKeywordsList = (id: string) => {
        selectedSecondaryKeywordsList = selectedSecondaryKeywordsList.filter(tag => tag.id !== id);
    }

    // Periodically sync formController's data with DB and switch step
    $effect(() => {
        if (!videoId) return;

        // prevents outdated work from updating state
        let isCurrent = true;
        const abortController = new AbortController();

        async function fetchFormData() {
            try {
                const resp = await fetch(`/api/video/${videoId}`, {
                    signal: abortController.signal,
                });

                if (!resp.ok) {
                    throw new Error(`Failed to fetch video: ${resp.status}`);
                }
                const data = await resp.json();

                // Never update the form for an obsolete request.
                if (!isCurrent) return;

                formController.populate(data);
            } catch (error) {
                // Cancellation is expected; don't report it as an error.
                if (!isCurrent || abortController.signal.aborted) return;
                console.error("Failed to load video data:", error);
            }
        }

        void fetchFormData();

        // Runs when videoId changes or this effect is destroyed.
        return () => {
            isCurrent = false;
            abortController.abort();
        };
    });
</script>

<div class="h-full w-2/3 p-10 space-y-8">

    <!-- Publication status badge -->
    <div class="mb-3">
        <p class="block text-sm fornt-semibold tracking-wide text-gray-700">
            Status:
            {#if formController.formData.publication_status === "draft"}
                <span class="inline-block px-2 py-1 rounded-md bg-amber-500 text-white">
                    Draft
                </span>
            {:else}
                <span class="inline-block px-2 py-1 rounded-md bg-green-500 text-white">
                    Published
                </span>
            {/if}
        </p>
    </div>

    <div class="mb-6 flex gap-2 border-b border-gray-200">
        <button
            type="button"
            onclick={() => activeTab = 'video'}
            class={`px-4 py-3 text-sm font-semibold transition ${
                activeTab === 'video'
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-500 hover:text-gray-800'
            }`}
        >
            Video Data
        </button>

        <button
            type="button"
            onclick={() => activeTab = 'seo'}
            class={`px-4 py-3 text-sm font-semibold transition ${
                activeTab === 'seo'
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-500 hover:text-gray-800'
            }`}
        >
            SEO
        </button>
    </div>

    <!-- Video fields -->
    {#if activeTab === 'video'}

        <!-- Video Title -->
        <div class="space-y-2">
            <label
                for="title"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Video Title
            </label>
            
            <!-- bind:value={formController.formData.title} -->
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

        <!-- Language -->
        <div class="space-y-2">
            <label
                for="language"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Language
            </label>

            <select
                name="language"
                bind:value={formController.formData.language}
                required
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3
                    text-gray-800 transition-all duration-200
                    focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            >
                <option value="">Select a Language</option>
                <option value="hindi">Hindi</option>
                <option value="bengali">Bengali</option>
            </select>
        </div>

        <!-- Video Series -->
        <div class="space-y-2">
            <label
                for="series"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Series
            </label>

            <select
                name="series"
                bind:value={formController.formData.series}
                // required
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3
                    text-gray-800 transition-all duration-200
                    focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            >
                <option value="">Select a Series</option>
                <option value="technology">Technology</option>
                <option value="music">Music</option>
                <option value="gaming">Gaming</option>
            </select>
        </div>

        <!-- Series Episode Number -->
        <div class="space-y-2">
            <label
                for="Episode Number"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Episode Number
            </label>

            <select
                name="series"
                bind:value={formController.formData.episode_number}
                // required
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3
                    text-gray-800 transition-all duration-200
                    focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            >
                <option value="">Select Episode Number</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5</option>
                <option value="6">6</option>
                <option value="7">7</option>
                <option value="8">8</option>
            </select>
        </div>

        <!-- Transcript code -->
        <div class="space-y-2">
            <label
                for="transcript_code"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Transcript Code
            </label>

            <select
                name="series"
                bind:value={formController.formData.transcript_code}
                // required
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3
                    text-gray-800 transition-all duration-200
                    focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            >
                <option value="">Select a Langauge Code</option>
                <option value="hindi">Hi</option>
                <option value="bengali">Bn</option>
            </select>
        </div>

        <!-- Video Transcript -->
        <div class="space-y-2">
            <div class="flex items-center justify-between">
                <label
                    for="description"        
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    Transcript
                </label>

                <span class="text-xs text-gray-400">
                    {formController.formData.transcript.length}
                </span>
            </div>

            <textarea
                name="transcript"
                placeholder="Add the video transcript here..."
                bind:value={formController.formData.transcript}
                // maxlength="400"
                // required
                class="w-full h-36 resize-none rounded-xl border border-gray-300
                    bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white
                    focus:ring-4 focus:ring-blue-100 focus:outline-none"
                // class="w-full h-32 overflow-y-auto resize-none border-2 border-gray-300
                //     rounded-md p-2 mt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            ></textarea>
        </div>

    {:else if activeTab === "seo"}

        <!-- Meta Title -->
        <div class="space-y-2">
            <label
                for="meta_title"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                SEO Meta Title
            </label>
            
            <input
                type="text"
                name="meta_title"
                placeholder="Enter video meta title for SEO"
                required
                bind:value={formController.formData.meta_title}
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            />
        
        </div>

        <!-- Meta Description -->
        <div class="space-y-2">
            <div class="flex items-center justify-between">
                <label
                    for="meta_description"        
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    SEO Meta Description
                </label>

                <span class="text-xs text-gray-400">
                    {formController.formData.meta_description.length}/400
                </span>
            </div>

            <textarea
                name="description"
                placeholder="Enter video meta description for SEO"
                bind:value={formController.formData.meta_description}
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

        <!-- Thumbnail Alt Text -->
        <div class="space-y-2">
            <label
                for="thumbnail_alt_text"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                SEO Thumbnail Alt Text
            </label>
            
            <input
                type="text"
                name="thumbnail_alt_text"
                placeholder="Enter alternative text for thumbnail (for SEO)"
                required
                bind:value={formController.formData.thumbnail_alt_text}
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            />
        </div>

        <!-- SEO Summary En -->
        <div class="space-y-2">
            <label
                for="seo_summary_en"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                SEO Summary En
            </label>
            
            <input
                type="text"
                name="seo_summary_en"
                placeholder="Enter Summary of the Entire Video Story in English (for SEO)"
                required
                bind:value={formController.formData.seo_summary_en}
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            />
        </div>

        <!-- SEO Tags / keywords -->
        <div class="space-y-3">
        
            <div>
                <label
                    for="seo_tags"
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
                    name="seo_tags"
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

        <!-- Focus Keywords -->
        <div class="space-y-3">
            <div>
                <label
                    for="focusKeywords"
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    Focus Keywords
                </label>

                <p class="mt-1 text-xs text-gray-500">
                    Add focus keywords to improve discoverability
                </p>
            </div>

            <div class="flex gap-3">
                <input
                    type="text"
                    name="focusKeyword"
                    bind:value={focusKeywordEntry}
                    placeholder="Add a focus keyword..."
                    onkeydown={(e) =>
                        e.key === 'Enter' && addItemToFocusKeywordsList()
                    }
                    class="flex-1 rounded-xl border border-gray-300 bg-gray-50
                    px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200
                    focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
                />

                <button
                    type="button"
                    onclick={addItemToFocusKeywordsList}
                    disabled={!focusKeywordEntry.trim()}
                    class="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white
                    shadow-lg shadow-blue-200 transition-all duration-200
                    hover:bg-blue-700 hover:shadow-blue-300
                    disabled:cursor-not-allowed disabled:opacity-40"
                >
                    Add
                </button>
            </div>
                
            <!-- Focus Keywords Container -->
            <div
                class="flex min-h-30 flex-wrap items-start gap-3 rounded-xl
                border border-dashed border-gray-300 bg-gray-50 p-4"
            >
                {#if selectedFocusKeywordsList.length === 0}
                    <div class="flex items-center text-sm text-gray-400">
                        No focus keywords added yet
                    </div>
                {:else}
                    {#each selectedFocusKeywordsList as tag (tag.id)}
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
                                onclick={() => removeItemFromFocusKeywordsList(tag.id)}
                                class="text-white/80 transition hover:text-white"
                            >
                                &times;
                            </button>
                        </div>
                    {/each}
                {/if}
            </div>
        </div>

        <!-- Secondary Keywords -->
        <div class="space-y-3">
            <div>
                <label
                    for="secondaryKeywords"
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    Secondary Keywords
                </label>

                <p class="mt-1 text-xs text-gray-500">
                    Add keywords to improve discoverability
                </p>
            </div>

            <div class="flex gap-3">
                <input
                    type="text"
                    name="secondaryKeyword"
                    bind:value={secondaryKeywordEntry}
                    placeholder="Add a secondary keyword..."
                    onkeydown={(e) =>
                        e.key === 'Enter' && addItemToSecondaryKeywordsList()
                    }
                    class="flex-1 rounded-xl border border-gray-300 bg-gray-50
                    px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200
                    focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
                />

                <button
                    type="button"
                    onclick={addItemToSecondaryKeywordsList}
                    disabled={!secondaryKeywordEntry.trim()}
                    class="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white
                    shadow-lg shadow-blue-200 transition-all duration-200
                    hover:bg-blue-700 hover:shadow-blue-300
                    disabled:cursor-not-allowed disabled:opacity-40"
                >
                    Add
                </button>
            </div>
                
            <!-- Secondary Keywords Container -->
            <div
                class="flex min-h-30 flex-wrap items-start gap-3 rounded-xl
                border border-dashed border-gray-300 bg-gray-50 p-4"
            >
                {#if selectedSecondaryKeywordsList.length === 0}
                    <div class="flex items-center text-sm text-gray-400">
                        No secondary keywords added yet
                    </div>
                {:else}
                    {#each selectedSecondaryKeywordsList as tag (tag.id)}
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
                                onclick={() => removeItemFromSecondaryKeywordsList(tag.id)}
                                class="text-white/80 transition hover:text-white"
                            >
                                &times;
                            </button>
                        </div>
                    {/each}
                {/if}
            </div>
        </div>
    {/if}
</div>
