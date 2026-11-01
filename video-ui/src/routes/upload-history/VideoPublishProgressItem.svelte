<script lang="ts">
    // import type { VideoDetail } from "$lib/types/VideoDetail";
    import type { VideoList } from '$lib/types/VideoList';
    import { resolve } from "$app/paths"
	// Adjust the optional fields below to match your API response.
	type Props = {
		video: VideoList & {
			thumbnail_url?: string | null;
			duration_seconds?: number | null;
			url?: string | null;
		};
	};

    let { video }: Props = $props();
    console.log(video);
    const href = $derived(video.url ?? `/video/${video.id}`);

    const duration = $derived.by(() => {
		const s = video.duration_seconds;
		if (s == null) return null;
		const h = Math.floor(s / 3600);
		const m = Math.floor((s % 3600) / 60);
		const sec = String(Math.floor(s % 60)).padStart(2, '0');
		return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`;
	});

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
</script>

<article class="flex flex-col gap-3 sm:flex-row">
	<a
		// {resolve({href})}
        {href}
		class="relative block aspect-video w-full shrink-0 overflow-hidden rounded-xl bg-[#e5e5e5] sm:w-60"
		aria-label={video.title}
	>
		{#if video.thumbnail_object_key}
			<img
				src={video.thumbnail_object_key}
				alt=""
				loading="lazy"
				class="h-full w-full object-cover"
			/>
		{/if}
		{#if duration}
			<span
				class="absolute right-1.5 bottom-1.5 rounded bg-black/80 px-1 py-0.5 text-xs font-medium text-white"
			>
				{duration}
			</span>
		{/if}
	</a>
 
	<div class="min-w-0 flex-1">
		<h2 class="line-clamp-2 text-base leading-snug font-medium">
			<a {href} class="hover:underline">{video.title}</a>
		</h2>
 
		<p class="mt-1 text-xs text-[#606060]">
			{statusLabel}{#if dateText}&nbsp;•&nbsp;{dateText}{/if}
		</p>
 
		{#if video.publication_status === 'draft'}
			<span class="mt-2 inline-block rounded bg-[#f2f2f2] px-1.5 py-0.5 text-xs text-[#606060]">
				Not visible to viewers
			</span>
		{:else if video.publication_status === 'archived'}
			<span class="mt-2 inline-block rounded bg-[#f2f2f2] px-1.5 py-0.5 text-xs text-[#606060]">
				Hidden
			</span>
		{/if}
	</div>
</article>
