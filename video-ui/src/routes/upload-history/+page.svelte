<script lang="ts">
    import type { VideoList } from "$lib/types/VideoList"
    import VideoPublishProgressItem from "./VideoPublishProgressItem.svelte";

    let { data }: { data: { videos: VideoList[] } } = $props();

    const tabs = [
		{ id: 'all', label: 'All' },
		{ id: 'draft', label: 'Drafts' },
		{ id: 'published', label: 'Published' },
		{ id: 'archived', label: 'Archived' }
	] as const;

    let activeTab = $state<(typeof tabs)[number]['id']>('all');

    const filteredVideos = $derived(
		activeTab === 'all'
			? data.videos
			: data.videos.filter((v) => v.publication_status === activeTab)
	);

    const counts = $derived(
		Object.fromEntries(
			tabs.map((t) => [
				t.id,
				t.id === 'all'
					? data.videos.length
					: data.videos.filter((v) => v.publication_status === t.id).length
			])
		) as Record<string, number>
	);
</script>

<main class="mx-auto w-full max-w-4xl px-4 py-6 text-[#0f0f0f]">
	<h1 class="mb-4 text-xl font-medium">Your videos</h1>
 
	<div class="mb-6 flex gap-3 overflow-x-auto border-b border-[#e5e5e5] pb-3" role="tablist">
		{#each tabs as tab (tab.id)}
			<button
				role="tab"
				aria-selected={activeTab === tab.id}
				onclick={() => (activeTab = tab.id)}
				class={[
					'shrink-0 cursor-pointer rounded-sm px-3 py-1.5 text-sm font-medium whitespace-nowrap',
					activeTab === tab.id
						? 'bg-[#0f0f0f] text-white'
						: 'bg-[#f2f2f2] text-[#0f0f0f] hover:bg-[#e5e5e5]'
				]}
			>
				{tab.label}
				<span class={activeTab === tab.id ? 'text-white/70' : 'text-[#606060]'}>
					{counts[tab.id]}
				</span>
			</button>
		{/each}
	</div>
 
	{#if filteredVideos.length === 0}
		<p class="py-24 text-center text-[#606060]">No videos here yet.</p>
	{:else}
		<ul class="flex flex-col gap-4">
			{#each filteredVideos as video (video.id)}
				<li><VideoPublishProgressItem {video} /></li>
			{/each}
		</ul>
	{/if}
</main>
