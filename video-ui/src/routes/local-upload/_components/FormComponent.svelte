<script lang="ts">
    let { videoId }: { videoId?: string | null } = $props();
    
    import { onMount } from 'svelte';  // for fetching Category, Series, Language, etc.

    type Category = {
        id: number;
        name: string;
    };

    type Series = {
        id: number;
        name: string;
    };

    let categories = $state<Category[]>([]);
    let seriesList = $state<Series[]>([]);

    let loading = $state(true);
    let error = $state('');

    onMount(async () => {
        try {
            const [categoriesResponse, seriesResponse] = await Promise.all([
                fetch('/api/category'),
                fetch('/api/series'),
            ]);

            if (!categoriesResponse.ok || !seriesResponse.ok) {
                throw new Error('Failed to fetch dropdown data');
            }

            const [categoriesData, seriesData] = await Promise.all([
                categoriesResponse.json(),
                seriesResponse.json()
            ]);

            categories = categoriesData;
            seriesList = seriesData;
        } catch (err) {
            console.error('Error loading dropdown data:', err);
            error = 'Could not load form options. Please try again.';
        } finally {
            loading = false;
        }
    });

    type SEOKeyword = {
        id: string;
        value: string;
    };

    // let selectedSEOTagsList = $state<SEOKeyword[]>([]);
    // let seoTagEntry = $state<string>('');

    let focusKeywordEntry = $state<string>('');
    let selectedFocusKeywordsList = $state<SEOKeyword[]>([]);
    
    let secondaryKeywordEntry = $state<string>('');
    let selectedSecondaryKeywordsList = $state<SEOKeyword[]>([]);
    
    let activeTab = $state("video");

    import {
        MetadataFormController
    } from "$lib/controllers/metadataFormController.svelte";

    const formController = MetadataFormController();

    // const addItemToSEOList = () => {
    //     const trimmed = seoTagEntry.trim();
    //     if (!trimmed) return;

    //     const newTag: SEOKeyword = {
    //         id: crypto.randomUUID(),
    //         value: trimmed
    //     }
        
    //     selectedSEOTagsList = [...selectedSEOTagsList, newTag];
    //     seoTagEntry = '';
    // }

    // const removeItemFromSEOList = (id: string) => {
    //     selectedSEOTagsList = selectedSEOTagsList.filter(tag => tag.id !== id);
    // }

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

    // Auto-save
    let isLoaded = $state(false);
    let saveStatus = $state<"idle" | "saving" | "saved" | "error">("idle");

    // Plain variables: these don't need to trigger Svelte effects.
    let lastSavedSnapshot = "";
    let saveVersion = 0;
    let debounceTimer: ReturnType<typeof setTimeout> | undefined;

    async function save(currentVideoId: string, snapshot: string) {
        // Nothing changed since the last successful save.
        if (snapshot === lastSavedSnapshot) {
            saveStatus = "saved";
            return;
        }

        const version = ++saveVersion;
        saveStatus = "saving";

        try {
            const resp = await fetch(`/api/video/${currentVideoId}/autosave-formdata`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: snapshot,
            });

            if (!resp.ok) throw new Error("Save failed");

            // Only the latest save may update the UI state.
            if (version !== saveVersion) return;

            lastSavedSnapshot = snapshot;
            saveStatus = "saved";
        } catch (error) {
            if (version !== saveVersion) return;
            saveStatus = "error";
            console.error(error);
        }
    }

    function saveNow() {
        if (!isLoaded || !videoId) return;

        clearTimeout(debounceTimer); // cancel any pending autosave
        void save(videoId, JSON.stringify({ ...formController.formData }));
    }

    // Periodically sync formController's data with DB and switch step
    $effect(() => {
        if (!videoId) {
            console.error("Video Id Not found!");
            return;
        }

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

                // Record the initial state so loading isn't treated as an edit.
                lastSavedSnapshot = JSON.stringify(formController.formData);
                isLoaded = true;
                saveStatus = "idle";
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

    // Debounced autosave.
    $effect(() => {
        if (!isLoaded || !videoId) return;

        const currentVideoId = videoId;

        // Read formData here (top level of the effect) so it stays tracked.
        const snapshot = JSON.stringify({ ...formController.formData });

        // Don't save unchanged data or the initial fetch.
        if (snapshot === lastSavedSnapshot) return;

        debounceTimer = setTimeout(() => save(currentVideoId, snapshot), 800);
        return () => clearTimeout(debounceTimer);
    });

</script>

<div class="h-full w-2/3 p-10 space-y-8">

    <!-- Publication status badge -->
    <div class="flex flex-row justify-between">
        <div class="mb-3">
            <p class="block text-sm fornt-semibold tracking-wide text-gray-700">
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

        <div>
            <p aria-live="polite">
                {#if !isLoaded}
                    Loading form…
                {:else if saveStatus === "saving"}
                    Saving…
                {:else if saveStatus === "saved"}
                    All changes saved
                {:else if saveStatus === "error"}
                    Save failed. Please try again.
                {/if}
            </p>
        </div>
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

        {#if loading}
            <p>Loading form options...</p>
        {:else if error}
            <p class="text-red-600">{error}</p>
        {/if}

        <!-- Video Title -->
        <div class="space-y-2">
            <label
                for="title"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Video Title
            </label>
            
            <p id="title-help" class="text-sm text-gray-600">
                Enter a clear, descriptive title for your video.
            </p>

            <input
                type="text"
                name="title"
                placeholder="Enter the video title"
                required
                aria-describedby="title-help"
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
                id="category"
                name="category"
                bind:value={formController.formData.category}
                required
                disabled={loading || !!error}
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3
                    text-gray-800 transition-all duration-200
                    focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            >
                <option value="">Select a category</option>
                <!-- <option value="technology">Technology</option>
                <option value="music">Music</option>
                <option value="gaming">Gaming</option> -->
                {#each categories as category (category.id)}
                    <option value={category.name}>
                        {category.name}
                    </option>
                {/each}
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

            <p id="language-help" class="text-sm text-gray-600">
                For viewers only. Available options are Hindi & Bengali. Default is Bengali.
            </p>

            <select
                name="language"
                bind:value={formController.formData.language}
                required
                aria-describedby="language-help"
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
                Series (Optional)
            </label>

            <select
                id="series"
                name="series"
                bind:value={formController.formData.series}
                disabled={loading || !!error}
                // required
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3
                    text-gray-800 transition-all duration-200
                    focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            >
                <option value="">Select a Series</option>
                <!-- <option value="technology">Technology</option>
                <option value="music">Music</option>
                <option value="gaming">Gaming</option> -->
                {#each seriesList as series (series.id)}
                    <option value={series.id}>
                        {series.name}
                    </option>
                {/each}
            </select>
        </div>

        <!-- Series Episode Number. Show Episode Number only if a Series is selected. -->
        {#if formController.formData.series}
            <div class="space-y-2">
                <label
                    for="Episode Number"
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    Episode Number (Optional. Must, if a Series is selected.)
                </label>

                <p id="episode-number-help" class="text-sm text-gray-600">
                    Only add Episode Number if the video is part of a Series.
                </p>

                <select
                    name="series"
                    bind:value={formController.formData.episode_number}
                    // required
                    aria-describedby="episode-number-help"
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
        {/if}

        <!-- Transcript code -->
        <div class="space-y-2">
            <label
                for="transcript_code"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Transcript Code
            </label>

            <p id="transcript-code-help" class="text-sm text-gray-600">
                This is the language of the transcript. Available options are: Hindi (Hi), Bengali (Bn). Default is Bengali.
            </p>

            <select
                name="series"
                bind:value={formController.formData.transcript_code}
                // required
                aria-describedby="transcript-code-help"
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
            <label
                for="description"        
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Transcript
            </label>

            <div class="flex items-center justify-between">
                <p id="transcript-help" class="text-sm text-gray-600">
                    Copy and paste the entire transcript text. 
                </p>

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
                aria-describedby="transcript-help"
                class="w-full h-36 resize-none rounded-xl border border-gray-300
                    bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white
                    focus:ring-4 focus:ring-blue-100 focus:outline-none"
                // class="w-full h-32 overflow-y-auto resize-none border-2 border-gray-300
                //     rounded-md p-2 mt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            ></textarea>
        </div>

    {:else if activeTab === "seo"}

        <!-- Focus Keywords -->
        <div class="space-y-3">
            <div>
                <label
                    for="focusKeywords"
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    Focus Keywords
                </label>

                <p id="focus-keywords-help" class="text-sm text-gray-600">
                    This is your collection of keywords for this video. These keywords must be included in the Title, Meta Title, Description, Meta Description,
                    Thumbnail Alt Text, Transcript. Keep a list of 2-3 focus keywords.
                </p>
            </div>

            <div class="flex gap-3">
                <input
                    type="text"
                    name="focusKeyword"
                    aria-describedby="focus-keywords-help"
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
                    Secondary Keywords (Optional)
                </label>

                <p id="secondary-keywords-help" class="text-sm text-gray-600">
                    This is your collection of related or long-tailed keywords for this video. Include them in the Description, Meta Description, Transcript.
                    Keep a list of 1-2 secondary keywords.
                </p>
            </div>

            <div class="flex gap-3">
                <input
                    type="text"
                    name="secondaryKeyword"
                    bind:value={secondaryKeywordEntry}
                    placeholder="Add a secondary keyword..."
                    aria-describedby="secondary-keywords-help"
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

        <!-- Meta Title -->
        <div class="space-y-2">
            <label
                for="meta_title"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                SEO Meta Title (Must for SEO)
            </label>
            
            <p id="meta-title-help" class="text-sm text-gray-600">
                This shown on Google Search Results Page as the title. This can be the same with Video Title.
                <br/>
                However, you must include the Keywords in the Meta Title.
            </p>

            <input
                type="text"
                name="meta_title"
                placeholder="Enter video meta title for SEO"
                required
                aria-describedby="meta-title-help"
                bind:value={formController.formData.meta_title}
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            />
        
        </div>

        <!-- Meta Description -->
        <div class="space-y-2">
            <label
                for="meta_description"        
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                SEO Meta Description
            </label>

            <div class="flex items-center justify-between">
                <p id="meta-description-help" class="text-sm text-gray-600">
                    This shown on Google Search Results Page as the description. This can be the same with Video Description.
                    <br/>
                    You must include the Keywords in the Meta Description.
                </p>

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
                aria-describedby="meta-description-help"
                class="w-full h-36 resize-none rounded-xl border border-gray-300
                    bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white
                    focus:ring-4 focus:ring-blue-100 focus:outline-none"
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
            
            <p id="thumbnail-alt-text-help" class="text-sm text-gray-600">
                Explain what the thumbnail represents or what the video covers. Try to include the main topic or keyword when relevant.
                <br/>
                For example, if the video is about learning Bengali, use: "Learn Bengali for beginners - video thumbnail".
            </p>
            <input
                type="text"
                name="thumbnail_alt_text"
                placeholder="Enter alternative text for thumbnail"
                aria-describedby="thumbnail-alt-text-help"
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
            
            <p id="seo-summary-en-help" class="text-sm text-gray-600">
                English summary for the entire Bengali/Hindi Video story. Helps in English language discoverability.
                Must include the main topic or keyword when relevant.
            </p>

            <input
                type="text"
                name="seo_summary_en"
                placeholder="Enter Summary of the Entire Video Story in English (for SEO)"
                required
                aria-describedby="seo-summary-en-help"
                bind:value={formController.formData.seo_summary_en}
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            />
        </div>

        <!-- keywords -->
        <!-- <div class="space-y-3">
        
            <div>
                <label
                    for="keywords"
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    General Keywords Specific to this Video
                </label>

                <p id="keywords-help" class="text-sm text-gray-600">
                    English summary for the entire Bengali/Hindi Video story. Helps in English language discoverability.
                    Must include the main topic or keyword when relevant.
                </p>
            </div>

            <div class="flex gap-3">
                <input
                    type="text"
                    name="keywords"
                    aria-describedby="keywords-help"
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
            </div> -->
                
            <!-- Keyword items Container -->
            <!-- <div
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
            </div> -->
        <!-- </div> -->

    {/if}

    <!-- Save Button for User Satisfaction-->
    <div class="mt-5 flex items-center justify-end gap-4">
        <span class="text-sm text-gray-400">
            {#if saveStatus === "saving"} Saving...
            {:else if saveStatus === "saved"} Saved
            {:else if saveStatus === "error"} Save Failed
            {/if}
        </span>
        <button
            type="button"
            disabled={!isLoaded || saveStatus === "saving"}
            class="py-2 px-8 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-lg
                disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            onclick={saveNow}
        >
            Save
        </button>
    </div>
</div>
