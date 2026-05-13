<script lang="ts">
    import VideoCard from "$lib/components/ui/VideoCard.svelte";
</script>

<!-- Categories Buttons -->
<section id="category-buttons" class="w-full h-16 py-4 flex flex-row items-center justify-evenly bg-mauve-500 text-white/60 font-medium">
    <p class="py-2 px-3 bg-gray-400/40 rounded-sm">Hindi</p>
    <p class="py-2 px-3 bg-gray-400/40 rounded-sm">Bengali</p>
    <p class="py-2 px-3 bg-gray-400/40 rounded-sm">English</p>
</section>

<section id="video-list" class="p-12 grid grid-cols-5 gap-8">
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
    <VideoCard />
</section>
