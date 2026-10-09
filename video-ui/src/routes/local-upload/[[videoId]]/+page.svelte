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
    const thumbnailInputController = fileInputController({uploadFileType: "image"})

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
                // 'http://127.0.0.1:8000/api/video/transcoded-upload/new-upload-record',
                '/api/video/transcoded-upload/new-upload-record',
                {
                    method: 'POST',
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const { videoId, transcodedUploadSessionId } = await response.json();

            await goto(
                resolve(`/local-upload/${videoId}`), {
                replaceState: true,
                noScroll: true,
                keepFocus: true,
            });

            const transcodedFiles = folderInputController.state.selectedDirFiles;
            
            // Because selectedDirFiles is always an array, use the following instead of- if (transcodedFiles) {}
            if (transcodedFiles.length > 0) {
                uploader.start(transcodedFiles, {
                    videoId: videoId,
                    transcodedUploadSessionId: transcodedUploadSessionId,
                    // concurrency, batchSize, maxRetries all optional, defaults are sane
                });
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


<div class="w-5/6 mx-auto h-100vh"> 
    <!-- Form Area -->
    {#if uploader.state.status === "completed"}
        <section class="flex flex-row justify-evenly">
            <FormComponent />
            <ThumbnailCard controller={thumbnailInputController} />
        </section>
    {:else}
        <!-- Upload Progress & Thumbnail -->
        <section class="w-2/3 mx-auto">
            <!-- Upload Progress -->
            <VideoUploadProgressCard uploader={uploader} />
        </section>
    {/if}
</div>
