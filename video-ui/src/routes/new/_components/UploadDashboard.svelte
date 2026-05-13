<script lang="ts">
    let { workflow } = $props();

    import VideoUploadProgressCard from './VideoUploadProgressCard.svelte'
    import ThumbnailCard from './ThumbnailCard.svelte'
    import MetadataFormCard from './MetadataFormCard.svelte'
</script>

<div class="h-[calc(100vh-3rem)] md:h-[calc(100vh-4rem)] flex">

    <main class="w-11/12 h-[95%] m-auto p-10">

        <section class="grid grid-cols-2 gap-16 h-full min-h-0">
            <!-- Left Column -->
            <div class="flex flex-col gap-8 h-full min-h-0">
                <VideoUploadProgressCard />
                <ThumbnailCard {workflow} />
            </div>

            <!-- Right Column - Form -->
             <MetadataFormCard {workflow} />
        </section>

    </main>
</div>
