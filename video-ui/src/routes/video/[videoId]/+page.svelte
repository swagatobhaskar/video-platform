<script lang="ts">
    import DashPlayer from '$lib/components/DashPlayer.svelte';
    import VideoSuggestions from '$lib/components/VideoSuggestions.svelte';
    // import type { VideoView } from '$lib/types/VideoView';
	import { page } from '$app/state';
	import { VideoJsonLd, serializeJsonLd } from '$lib/seo/VideoJsonLd.js';

    let { data } = $props();
	let video = $derived(data.video);

    // import { page } from '$app/state';  // no longer reading videoId from URL parameter
    // let videoId = $derived(page?.params?.videoId);

	// --- Strucured data (JSON-LD) ---
	let jsonLd = $derived(
		serializeJsonLd(
			VideoJsonLd(video, {
				pageUrl: page.url.href,
				thumbnailUrl: video.thumbnail_object_key,  // must be an absolute URL
				contentUrl: video.hls_manifest_key // or dash ?  // must be an absolute URL
			})
		)
	);

    // --- formatting ---
	const numberFmt = new Intl.NumberFormat('en');
	const dateFmt = new Intl.DateTimeFormat('en', { dateStyle: 'medium' });
 
	let publishedLabel = $derived(video.published_at ? dateFmt.format(new Date(video.published_at)) : null);

	// --- like / dislike (local state only; wire to your API where marked) ---
	let reaction = $state<'like' | 'dislike' | null>(null);
	let likes = $derived(video.like_count + (reaction === 'like' ? 1 : 0));
	let dislikes = $derived(video.dislike_count + (reaction === 'dislike' ? 1 : 0));
 
	function react(kind: 'like' | 'dislike') {
		reaction = reaction === kind ? null : kind;
		// TODO: POST the reaction to your FastAPI backend here.
	}

	// --- share ---
	let copied = $state(false);
	async function share() {
		const url = window.location.href;
		try {
			if (navigator.share) {
				await navigator.share({ title: video.title, url });
				return;
			}
			await navigator.clipboard.writeText(url);
			copied = true;
			setTimeout(() => (copied = false), 2000);
		} catch {
			/* share dialog dismissed */
		}
	}

    // --- transcript ---
	let transcripts = $derived(video.video_transcripts ?? []);
	let langIndex = $state(0);
	let activeTranscript = $derived(transcripts[langIndex] ?? transcripts[0]);
</script>

<svelte:head>
	<title>{video.meta_title || video.title}</title>
	{#if video.meta_description}
		<meta name="description" content={video.meta_description} />
	{/if}
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<!-- 1200px is 7xl, 1400px is 350, 1600px is 400. Increase it to increase player width -->
<main class="mx-auto grid max-w-[1600px] gap-6 px-4 py-4 lg:grid-cols-[minmax(0,1fr)_380px] lg:px-6">
    <!-- Primary Column -->
    <div class="min-w-0">
        <div class="overflow-hidden rounded bg-black">
            <DashPlayer src={video.dash_manifest_key} poster={video.thumbnail_object_key} />
        </div>

        <!-- Title + meta -->
        <h1 class="mt-3 text-xl font-semibold leading-snug text-neutral-900">{video.title}</h1>
        <p class="mt-1 text-sm text-neutral-600">
			{numberFmt.format(video.view_count)} views
			{#if publishedLabel}&nbsp;·&nbsp;{publishedLabel}{/if}
			{#if video.series}
				&nbsp;·&nbsp;{video.series.name}{#if video.episode_number != null}, Episode {video.episode_number}{/if}
			{/if}
        </p>

        <!-- Under-video bar: category (left), actions (right) -->
        <div class="mt-3 flex items-center justify-between gap-4 border-t border-neutral-200 pt-3">
            <div class="flex min-w-0 items-center gap-2">
                {#if video.category}
                    {#if video.category.r2_category_image_key}
                        <img
							src={video.category.r2_category_image_key}
							alt=""
							class="size-6 shrink-0 rounded-full bg-neutral-200 object-cover"
						/>
                    {:else}
                        <span
                            class="flex size-6 shrink-0 items-center justify-center rounded-full bg-neutral-200 text-xs font-medium text-neutral-600"
                            aria-hidden="true"    
                        >
                            {video.category.name.charAt(0).toUpperCase()}
                        </span>
                    {/if}
                    <span class="truncate text-sm font-medium text-neutral-900">{video.category.name}</span>
                {/if}
            </div>

            <div class="flex shrink-0 items-center gap-2">
                <div class="flex overflow-hidden rounded border border-neutral-300">
                    <button
						type="button"
						onclick={() => react('like')}
						aria-pressed={reaction === 'like'}
						aria-label="Like"
						class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-neutral-800 hover:bg-neutral-100"
					>
						<svg viewBox="0 0 24 24" class="size-4" fill={reaction === 'like' ? 'currentColor' : 'none'}
							stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
						>
							<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
						</svg>
						<span>{numberFmt.format(likes)}</span>
					</button>
					<button
						type="button"
						onclick={() => react('dislike')}
						aria-pressed={reaction === 'dislike'}
						aria-label="Dislike"
						class="flex items-center gap-1.5 border-l border-neutral-300 px-3 py-1.5 text-sm text-neutral-800 hover:bg-neutral-100"
					>
						<svg viewBox="0 0 24 24" class="size-4" fill={reaction === 'dislike' ? 'currentColor' : 'none'} stroke="currentColor"
							stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
						>
							<path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/>
						</svg>
						<span>{numberFmt.format(dislikes)}</span>
					</button>
                </div>

                <button
					type="button"
					onclick={share}
					aria-label="Share"
					class="flex items-center gap-1.5 rounded border border-neutral-300 px-3 py-1.5 text-sm text-neutral-800 hover:bg-neutral-100"
				>
					<svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
						<circle cx="18" cy="5" r="3" />
						<circle cx="6" cy="12" r="3" />
						<circle cx="18" cy="19" r="3" />
						<line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
						<line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
					</svg>
					<span>{copied ? 'Link copied' : 'Share'}</span>
				</button>
            </div>
        </div>

        <!-- Description -->
		{#if video.description}
			<div class="mt-4 rounded bg-neutral-100 p-3 text-sm leading-6 whitespace-pre-line text-neutral-800">
				{video.description}
			</div>
		{/if}

        <!-- Transcript dropdown -->
		{#if transcripts.length > 0}
			<details class="group mt-4 rounded border border-neutral-300">
				<summary
					class="flex cursor-pointer list-none items-center justify-between px-3 py-2 text-sm font-medium
                    text-neutral-900 select-none hover:bg-neutral-50 [&::-webkit-details-marker]:hidden"
				>
					<span>Transcript</span>
					<svg viewBox="0 0 24 24" class="size-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor"
						stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
					>
						<polyline points="6 9 12 15 18 9" />
					</svg>
				</summary>

                <div class="border-t border-neutral-300 p-3">
					{#if transcripts.length > 1}
						<label class="mb-3 flex items-center gap-2 text-sm text-neutral-700">
							Language
							<select
								bind:value={langIndex}
								class="rounded border border-neutral-300 bg-white px-2 py-1 text-sm"
							>
								{#each transcripts as t, i (t.id ?? i)}
									<option value={i}>{t.language_code ?? `Transcript ${i + 1}`}</option>
								{/each}
							</select>
						</label>
					{/if}
 
					<div class="max-h-80 overflow-y-auto text-sm leading-6 whitespace-pre-wrap text-neutral-800">
						{activeTranscript?.transcript_text ?? 'Transcript not available.'}
					</div>
				</div>
			</details>
        {/if}
    </div>

    <!-- Right column: suggestions placeholder -->
	<VideoSuggestions />

</main>