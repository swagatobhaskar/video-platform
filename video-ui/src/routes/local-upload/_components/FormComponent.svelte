<script lang="ts">
    let { videoId, initialData } = $props();

    import { onMount, untrack, onDestroy } from 'svelte';  // onMount is for fetching Category, Series, Language, etc.
    import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';

    import KeywordInput from './KeywordInput.svelte';

    type Category = { id: number; name: string; };

    type Series = { id: number; name: string; };

    let categories = $state<Category[]>([]);
    let seriesList = $state<Series[]>([]);

    let loading = $state(true);
    let error = $state('');

    // snapshot helper function so the comparison with lastSavedSnapshot always uses the same shape
    function buildSnapshot(): string {
        // publication_status is display-only; only the publish endpoint changes it.
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { publication_status, ...autosaveFields } = formController.formData;
        return JSON.stringify(autosaveFields);
    }

    let lastSavedSnapshot = buildSnapshot();

    onMount(async () => {
        void checkReadiness();

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
    
    let activeTab = $state("video");

    import {
        MetadataFormController
    } from "$lib/controllers/metadataFormController.svelte";

    const formController = MetadataFormController();
    
    // One-time initialisation: the parent recreates this component via
    // {#key data.videoId}, so later changes to `initialData` are intentionally ignored.
    formController.populate(untrack(() => initialData));

    // you can use  `svelte-ignore state_referenced_locally` to suppress the warning
    // However, I used untrack to read initialData inside a closure
    // formController.populate(initialData); // This reference only captures the initial value of `initialData`. Did you mean to reference it inside a closure instead?

    // let lastSavedSnapshot = JSON.stringify(formController.formData);

    let saveStatus = $state<"idle" | "saving" | "saved" | "error">("idle");

    // Plain variables: these don't need to trigger Svelte effects.
    
    let saveVersion = 0;
    let debounceTimer: ReturnType<typeof setTimeout> | undefined;

    let publishErrors = $state<Record<string, string[]> | null>(null); // null = unknown yet
   
    let publishing = $state(false);
    let publishMessage = $state('');

    const isDraft = $derived(formController.formData.publication_status === 'draft');
    const readyToPublish = $derived(
        isDraft && publishErrors !== null && Object.keys(publishErrors).length === 0
    );

    let readinessRequest = 0; // ignore out-of-order responses

    async function checkReadiness() {
        if (!videoId) return;
        const request = ++readinessRequest;
        try {
            const resp = await fetch(`/api/video/${videoId}/publish-readiness`);
            if (!resp.ok) throw new Error('readiness check failed');
            const data = await resp.json();
            if (request === readinessRequest) publishErrors = data.errors;
        } catch (err) {
            if (request === readinessRequest) publishErrors = null; // unknown, so hide the button
            console.error(err);
        }
    }

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
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: snapshot,
            });

            if (!resp.ok) throw new Error("Save failed");

            // Only the latest save may update the UI state.
            if (version !== saveVersion) return;

            lastSavedSnapshot = snapshot;
            saveStatus = "saved";
            void checkReadiness();
        } catch (err) {
            if (version !== saveVersion) return;
            saveStatus = "error";
            console.error(err);
        }
    }

    function saveNow() {
        if (!videoId) return;

        clearTimeout(debounceTimer); // cancel any pending autosave
        void save(videoId, buildSnapshot());
    }

    // Debounced autosave.
    $effect(() => {
        if (!videoId) return;

        const currentVideoId = videoId;

        // Read formData here (top level of the effect) so it stays tracked.
        const snapshot = buildSnapshot(); // still tracked: it reads formData synchronously

        // Don't save unchanged data
        if (snapshot === lastSavedSnapshot) return;

        debounceTimer = setTimeout(() => save(currentVideoId, snapshot), 800);
        return () => clearTimeout(debounceTimer);
    });

    // Edits are lost if the form is destroyed within 800 ms
    // The debounce effect’s cleanup runs clearTimeout when the component is destroyed.
    // If the user types and the form unmounts before the timer fires (for example {#key data.videoId} recreating it,
    // or in-app navigation), the last edit is silently dropped. Flush it on destroy:
    onDestroy(() => {
        if (!videoId) return;
        const snapshot = buildSnapshot();
        if (snapshot === lastSavedSnapshot) return;

        // Fire-and-forget: the SPA stays alive after navigation, so this completes.
        void fetch(`/api/video/${videoId}/autosave-formdata`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: snapshot,
        });
    });

    async function publish() {
        if (!videoId || publishing) return;
        publishing = true;
        publishMessage = '';
        clearTimeout(debounceTimer);

        try {
            await save(videoId, buildSnapshot());
            if (saveStatus === 'error') {
                publishMessage = 'Could not save your latest changes.';
                return;
            }

            const resp = await fetch(`/api/video/${videoId}/publish`, { method: 'PATCH' });

            if (resp.status === 400) {
                const body = await resp.json();
                publishErrors = body.errors ?? null; // button disappears, state corrected
                publishMessage = 'This video is not ready to publish yet.';
                return;
            }
            if (!resp.ok) throw new Error('Publish failed');

            formController.formData.publication_status = 'published';
            // Navigate to video view page
            await goto(resolve(`/video/${videoId}`));
        } catch (err) {
            console.error(err);
            publishMessage = 'Publishing failed. Please try again.';
        } finally {
            publishing = false;
        }
    }

</script>

<!-- Thumbnail and video uploads happen outside this form, so also re-check when the user returns to the tab -->
<svelte:window onfocus={checkReadiness} />

<div class="h-full w-2/3 p-10 space-y-8">

    <!-- status badge -->
    <div class="flex flex-row items-center justify-between">
        <div class="flex items-center gap-3">
            {#if isDraft}
                <span class="inline-block px-2 py-1 rounded-md bg-amber-500 text-white text-sm">Draft</span>
            {:else}
                <span class="inline-block px-2 py-1 rounded-md bg-green-500 text-white text-sm">Published</span>
            {/if}

            {#if readyToPublish}
                <span class="text-sm text-green-700">Ready to publish</span>
                <button
                    type="button"
                    onclick={publish}
                    disabled={publishing || saveStatus === "saving"}
                    class="py-1 px-4 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm
                        disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                    {publishing ? 'Publishing…' : 'Publish'}
                </button>
            {/if}
        </div>

        <div>
            <p aria-live="polite">...</p>
        </div>

        {#if publishMessage}
            <p class="text-sm text-red-600" role="alert">{publishMessage}</p>
        {/if}

        <div>
            <p aria-live="polite">
                {#if saveStatus === "saving"}
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
                id="title"
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
                    id="description"
                    for="description"        
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    Description
                </label>

                <span class="text-xs text-gray-400">
                    {formController.formData.description?.length}/400
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
                id="category"
                for="category"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Category
            </label>

            <select
                id="category"
                name="category"
                bind:value={formController.formData.category_id}
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
                id="language"
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
                id="series"
                for="series"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Series (Optional)
            </label>

            <select
                id="series"
                name="series"
                bind:value={formController.formData.series_id}
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
        {#if formController.formData.series_id}
            <div class="space-y-2">
                <label
                    id="episode-number"
                    for="episode-number"
                    class="block text-sm font-semibold tracking-wide text-gray-700"
                >
                    Episode Number (Optional. Must, if a Series is selected.)
                </label>

                <p id="episode-number-help" class="text-sm text-gray-600">
                    Only add Episode Number if the video is part of a Series.
                </p>

                <select
                    name="episode-number"
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
                id="transcript-code"
                for="transcript-code"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Transcript Code
            </label>

            <p id="transcript-code-help" class="text-sm text-gray-600">
                This is the language of the transcript. Available options are: Hindi (Hi), Bengali (Bn). Default is Bengali.
            </p>

            <select
                name="transcript-code"
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
                id="transcript"
                for="transcript"        
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
        <KeywordInput
            id="focusKeywords"
            label="Focus Keywords"
            help="This is your collection of keywords for this video. These keywords must be included in the Title,
                Meta Title, Description, Meta Description, Thumbnail Alt Text, Transcript. Keep a list of 2-3 focus keywords."
            bind:keywords={formController.formData.focus_keywords}
        />

        <KeywordInput
            id="secondaryKeywords"
            label="Secondary Keywords (Optional)"
            help="This is your collection of related or long-tailed keywords.Include them in the Description,
                Meta Description, Transcript. Keep a list of 1-2 secondary keywords."
            bind:keywords={formController.formData.secondary_keywords}
        />

        <!-- Search Intent -->
        <div class="space-y-2">
            <label
                id="search-intent"
                for="search-intent"
                class="block text-sm font-semibold tracking-wide text-gray-700"
            >
                Search Intent
            </label>
            
            <p id="search-intent-help" class="text-sm text-gray-600">
                Enter the search term user is likely to enter on Google.
            </p>

            <input
                type="text"
                name="search-intent"
                placeholder="Enter probable search intent"
                required
                aria-describedby="search-intent-help"
                bind:value={formController.formData.search_intent}
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            />
        
        </div>

        <!-- Meta Title -->
        <div class="space-y-2">
            <label
                id="meta-title"
                for="meta-title"
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
                name="meta-title"
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
                id="meta-description"
                for="meta-description"
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
                name="meta-description"
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
                id="thumbnail-alt-text"
                for="thumbnail-alt-text"
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
                name="thumbnail-alt-text"
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
                id="seo-summary-en"
                for="seo-summary-en"
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
                name="seo-summary-en"
                placeholder="Enter Summary of the Entire Video Story in English (for SEO)"
                required
                aria-describedby="seo-summary-en-help"
                bind:value={formController.formData.seo_summary_en}
                class="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-gray-800 placeholder:text-gray-400
                    transition-all duration-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100
                    focus:outline-none"
            />
        </div>

    {/if}

    <!-- status badge -->
    <div class="flex items-center gap-3">
        {#if readyToPublish}
            <span class="text-sm text-green-700">Ready to publish</span>
            <button
                type="button"
                onclick={publish}
                disabled={publishing || saveStatus === "saving"}
                class="py-1 px-4 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm
                    disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
                {publishing ? 'Publishing…' : 'Publish'}
            </button>
        {/if}
    </div>

    {#if publishMessage}
        <p class="text-sm text-red-600" role="alert">{publishMessage}</p>
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
            disabled={saveStatus === "saving"}
            class="py-2 px-8 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-lg
                disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            onclick={saveNow}
        >
            Save
        </button>
    </div>
</div>
