<script lang="ts">
    import { page } from '$app/state';
    import { goto } from "$app/navigation";
    import { resolve } from '$app/paths';

    import FolderUploadModal from '../_components/FolderUploadModal.svelte';
    import FormComponent from '../_components/FormComponent.svelte';
    import ThumbnailCard from '../_components/ThumbnailCard.svelte';
    import VideoUploadProgressCard from '../_components/VideoUploadProgressCard.svelte';

    import { fileInputController } from '$lib/controllers/fileInputController.svelte';
    const folderInputController = fileInputController({uploadFileType: "transcoded-directory"});
    // const thumbnailInputController = fileInputController({uploadFileType: "image"})

    import { createTranscodedFolderUploader } from '$lib/services/transcodedFolderUploader.svelte'
    const uploader = createTranscodedFolderUploader();

    // import { thumbnailUploadService } from '$lib/services/thumbnailUploadService.svelte';
    // const thumbnailUploader = thumbnailUploadService();

    // const videoId = $derived(!page.params.videoId);
    const videoId = $derived(page.params.videoId);
    const modalOpen = $derived(videoId === undefined);

    async function handleUploadWithNewSession() {
        // Create new upload_session and fetch the id

        try {
            const response = await fetch(
                // 'http://127.0.0.1:8000/api/video/upload/new-upload-record',
                '/api/video/transcoded-upload/new-upload-record',
                {
                    method: 'POST'
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // Add the upload_session_id to the URL
            await goto(
                resolve(`/local-upload/${data.videoId}`), {
                replaceState: true,
                noScroll: true,
                keepFocus: true,
            });

            // Start the upload
            const transcodedFiles = folderInputController.state.selectedDirFiles;
            
            // Because selectedDirFiles is always an array, use the following instead of- if (transcodedFiles) {}
            if (transcodedFiles.length > 0) {
                // await uploader.upload(transcodedFiles, data.videoId, data.uploadSessionId);
                // it has to batched file upload, not the same as multi-part upload
            }

	    } catch (err) {
            console.error(err);
        }
    }
</script>

<FolderUploadModal
    open={modalOpen}
    {folderInputController}
    onUploadClick={handleUploadWithNewSession}
/>


<div class="w-5/6 mx-auto h-100vh flex flex-row">
    <!-- Form Area -->
    <section class="flex-2/3">
         <FormComponent />
    </section>
    
    <!-- Upload Progress & Thumbnail -->
    <section class="flex-1/3 flex flex-col justify-evenly">
        <!-- Upload Progress -->
        <VideoUploadProgressCard uploader={uploader} />
        
        <ThumbnailCard controller={thumbnailInputController} />
    </section>
</div>
