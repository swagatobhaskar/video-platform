<script lang="ts">
    import VideoCard from "$lib/components/ui/VideoCard.svelte";
</script>

<!-- Categories Buttons -->
<section id="category-buttons" class="w-full md:w-1/6 h-10 ml-auto mr-5 my-2">
    <div class="flex flex-row items-center gap-2 text-white font-medium py-1">
        <p class="flex-1 text-center py-2 px-3 bg-mauve-400/90 hover:bg-mauve-500 rounded-sm">Hindi</p>
        <p class="flex-1 text-center py-2 px-3 bg-mauve-400/90 hover:bg-mauve-500 rounded-sm">Bengali</p>
        <p class="flex-1 text-center py-2 px-3 bg-mauve-400/90 hover:bg-mauve-500 rounded-sm">All</p>
    </div>
</section>

<section id="video-list" class="p-10 grid grid-cols-5 gap-8">
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
