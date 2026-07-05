<script lang="ts">
    
    import { onMount } from 'svelte';

    import VideoDropModal from './_components/VideoDropModal.svelte';
    import FormComponent from './_components/FormComponent.svelte';
    import ThumbnailCard from './_components/ThumbnailCard.svelte';
    import VideoUploadProgressCard from './_components/VideoUploadProgressCard.svelte';

    let videoDropModalOpen = $state(false);

    onMount(() => {
        videoDropModalOpen = true;
    })
</script>


<VideoDropModal open={videoDropModalOpen} />

<div class="w-5/6 mx-auto h-100vh flex flex-row">
    <!-- Form Area -->
    <section class="flex-2/3">
        <!-- Form Component -->
         <FormComponent />
        <!-- End of Form Component -->
    </section>
    
    <!-- Upload Progress & Thumbnail -->
    <section class="flex-1/3 flex flex-col justify-evenly">
        <!-- Upload Progress -->
        <VideoUploadProgressCard />
        <!-- Thumbnail -->
        <ThumbnailCard />
    </section>
</div>