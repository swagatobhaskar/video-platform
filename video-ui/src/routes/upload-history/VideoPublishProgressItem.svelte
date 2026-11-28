<script lang="ts">
    // import type { VideoDetail } from "$lib/types/VideoDetail";
	import { onMount } from "svelte";
    import type { VideoList } from '$lib/types/VideoList';
    import { resolve } from "$app/paths";

	// Adjust the optional fields below to match your API response.
	type Props = {
		video: VideoList & {
			thumbnail_url?: string | null;
			duration_seconds?: number | null;
			url?: string | null;
		};
	};

	type PublishErrors = {
		processing: string[];
		thumbnail: string[];
		metadata: string[];
		seo: string[];
	};

	type PublishReadiness = {
		can_publish: boolean;  // snake_case at the backend
		errors: PublishErrors;
	}

    let { video }: Props = $props();	

    // const duration = $derived.by(() => {
	// 	const s = video.duration_seconds;
	// 	if (s == null) return null;
	// 	const h = Math.floor(s / 3600);
	// 	const m = Math.floor((s % 3600) / 60);
	// 	const sec = String(Math.floor(s % 60)).padStart(2, '0');
	// 	return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`;
	// });

    const dateText = $derived.by(() => {
		if (!video.published_at) return null;
		return new Date(video.published_at).toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	});

    const statusLabel = $derived(
		video.publication_status === 'draft'
			? 'Draft'
			: video.publication_status === 'archived'
				? 'Archived'
				: 'Published'
	);

	let loadingPublishReadiness = $state(false);
	let publishReadiness = $state<PublishReadiness | null>(null);
	let publishReadinessError = $state<string | null>(null);

	const fetchPublishErrors = async (videoId: string) => {
		loadingPublishReadiness = true;
    	publishReadinessError = null;
		
		try {
			const res = await fetch(`http://localhost:8000/api/video/${videoId}/publish-readiness`);
			if (!res.ok) throw new Error("Failed to fetch publish readiness status!")
			publishReadiness = await res.json();
			// console.log(publishReadiness);
		} catch (err) {
			// console.error(err);
			publishReadinessError = err instanceof Error ? err.message : "Something went wrong.";
		} finally {
			loadingPublishReadiness = false;
		}
	};

	onMount(async () => {
		fetchPublishErrors(video.id);
	});

	const fieldLabels: Record<string, string> = {
		description: "Video description",
		slug: "Video URL slug",
		category_id: "Video category",
		search_intent: "Search intent",
		focus_keywords: "Focus keywords",
		seo_summary_en: "SEO summary",
		secondary_keywords: "Secondary keywords",
		thumbnail_alt_text: "Thumbnail alt text",
		meta_description: "Meta description",
		meta_title: "Meta title"
	};

	const getFieldLabel = (field: string) =>
		fieldLabels[field] ?? field.replaceAll("_", " ");
</script>


<section class="flex flex-col gap-3 sm:flex-row">
	<a
        href={resolve(`/video/${video.id}`)}
		class="relative block aspect-video w-full shrink-0 self-start overflow-hidden rounded-xl bg-[#e5e5e5] sm:w-80"
		aria-label={video.title}
	>
		{#if video.thumbnail_object_key}
			<img
				src={video.thumbnail_object_key}
				alt=""
				loading="lazy"
				class="absolute inset-0 h-full w-full object-cover"
			/>
		{/if}
		<!-- {#if duration}
			<span
				class="absolute right-1.5 bottom-1.5 rounded bg-black/80 px-1 py-0.5 text-xs font-medium text-white"
			>
				{duration}
			</span>
		{/if} -->
	</a>
 
	<div class="min-w-0 flex-1">
		<h2 class="line-clamp-2 text-base leading-snug font-medium">
			<a
				href={resolve(`/video/${video.id}`)}
				class="hover:underline"
			>
				{video.title}
			</a>
		</h2>
 
		<p class="mt-1 text-xs text-[#606060]">
			{statusLabel}{#if dateText}&nbsp;•&nbsp;{dateText}{/if}
		</p>
 
		{#if video.publication_status === 'draft'}
			<span class="mt-2 inline-block rounded bg-[#ffdbdb] border border-[#f8b8b8] px-1.5 py-0.5 text-xs text-[#606060]">
				Can not be published yet! Not visible to viewers.
			</span>

			<div class="mt-3">
				{#if loadingPublishReadiness}
					<p class="text-sm text-gray-500">
						Checking publish readiness...
					</p>

				{:else if publishReadinessError}
					<p class="text-sm text-red-600">
						{publishReadinessError}
					</p>

				{:else if publishReadiness}
					{#if publishReadiness.can_publish}
						<div class="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 p-3">
							<span class="text-green-600">✓</span>
							<p class="text-sm font-medium text-green-700">
								Video is ready to publish!
							</p>
						</div>

					{:else}
						<div class="rounded-lg border border-amber-200 bg-amber-50 p-3">
							<div class="flex items-start gap-2">
								<span class="text-amber-600">⚠</span>

								<div>
									<p class="text-sm font-semibold text-amber-900">
										Video isn't ready to publish
									</p>

									<p class="mt-0.5 text-xs text-amber-700">
										Complete the following tasks before publishing.
									</p>
								</div>
							</div>

							<div class="mt-3 space-y-3">

								{#if publishReadiness.errors.processing.length > 0}
									<div>
										<h4 class="text-xs font-semibold uppercase tracking-wide text-gray-600">Processing</h4>

										{#each publishReadiness.errors.processing as error (error)}
											<p class="mt-1 text-sm text-red-600">• {error}</p>
										{/each}
									</div>
								{/if}

								{#if publishReadiness.errors.thumbnail.length > 0}
									<div>
										<h4 class="text-xs font-semibold uppercase tracking-wide text-gray-600">Thumbnail</h4>

										{#each publishReadiness.errors.thumbnail as error (error)}
											<p class="mt-1 text-sm text-red-600">• {error}</p>
										{/each}
									</div>
								{/if}

								{#if publishReadiness.errors.metadata.length > 0}
									<div>
										<h4 class="text-xs font-semibold uppercase tracking-wide text-gray-600">
											Missing video details
										</h4>

										<div class="mt-1 flex flex-wrap gap-1.5">
											{#each publishReadiness.errors.metadata as field (field)}
												<span class="rounded bg-white px-2 py-1 text-xs font-medium text-gray-700 ring-1 ring-amber-200">
													{getFieldLabel(field)}
												</span>
											{/each}
										</div>
									</div>
								{/if}

								{#if publishReadiness.errors.seo.length > 0}
									<div>
										<h4 class="text-xs font-semibold uppercase tracking-wide text-gray-600">
											Missing SEO information
										</h4>

										<div class="mt-1 flex flex-wrap gap-1.5">
											{#each publishReadiness.errors.seo as field (field)}
												<span class="rounded bg-white px-2 py-1 text-xs font-medium text-gray-700 ring-1 ring-amber-200">
													{getFieldLabel(field)}
												</span>
											{/each}
										</div>
									</div>
								{/if}

							</div>
						</div>
					{/if}
				{/if}
			</div>
		{:else if video.publication_status === 'archived'}
			<span class="mt-2 inline-block rounded bg-[#f2f2f2] px-1.5 py-0.5 text-xs text-[#606060]">
				Hidden
			</span>
		{/if}
	</div>
</section>
