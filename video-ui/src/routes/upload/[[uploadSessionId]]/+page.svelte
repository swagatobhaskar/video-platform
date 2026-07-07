<script lang="ts">
    
    // import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { goto } from "$app/navigation";
    import { resolve } from '$app/paths';

    import VideoDropModal from '../_components/VideoDropModal.svelte';
    import FormComponent from '../_components/FormComponent.svelte';
    import ThumbnailCard from '../_components/ThumbnailCard.svelte';
    import VideoUploadProgressCard from '../_components/VideoUploadProgressCard.svelte';

    import { fileInputController } from '$lib/controllers/fileInputController.svelte';
    const videoInputController = fileInputController({uploadFileType: "video"})
    
    import { createVideoUploadSession } from '$lib/services/videoUploadSession.svelte'
    const uploader = createVideoUploadSession();

    const uploadSessionId = $derived(page.params.uploadSessionId);

    let modalOpen = $state(true);

    async function handleNewUploadSession() {
        // Get new upload_session_id
        try {
            const response = await fetch(
                'http://127.0.0.1:8000/api/video/uploads/new-upload-session',
                {
                    method: 'POST'
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // remove any existing uploadSessionId from cookies
            cookieStore.delete("uploadSessionId");

            // Set uploadSessionId in cookies
            cookieStore.set("uploadSessionId", data.upload_session_id)

            // Close the modal
            modalOpen = false;

            // Add the upload_session_id to the URL
            await goto(
                resolve(`/upload/${data.upload_session_id}`), {
                replaceState: true,
                noScroll: true,
                keepFocus: true,
            });

	    } catch (err) {
            console.error(err);
        }
    }
    // onMount(() => {
    //     videoDropModalOpen = true;
    // })
    $effect(() => {
        console.log("selectedFile:", videoInputController.state.selectedFile);
    });
</script>


<VideoDropModal
    open={modalOpen}
    // open={modalOpen}
    {videoInputController}
    onUploadClick={handleNewUploadSession}
/>

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
        <VideoUploadProgressCard
            uploader={uploader}
            videoFile={videoInputController.state.selectedFile}
        />
        
        <!-- Thumbnail -->
        <ThumbnailCard />
    </section>
</div>