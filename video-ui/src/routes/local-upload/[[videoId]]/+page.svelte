<script lang="ts">
    import { page } from '$app/state';
    import { goto } from "$app/navigation";
    import { resolve } from '$app/paths';

    import FolderUploadModal from '../_components/FolderUploadModal.svelte';
    import FormComponent from '../_components/FormComponent.svelte';
    import ThumbnailCard from '../_components/ThumbnailCard.svelte';
    import VideoUploadProgressCard from '../_components/VideoUploadProgressCard.svelte';

    // Only the thumbnail still needs this controller; folder selection now goes
    // through transcodedFolderSelection.ts, so folderInputController is gone.
    import { fileInputController } from '$lib/controllers/fileInputController.svelte';
    // const folderInputController = fileInputController({uploadFileType: "transcoded-directory"});
    const thumbnailInputController = fileInputController({uploadFileType: "image"})

    import {
        entriesFromInput,
        entriesFromDrop,
        prepareTranscodedFolder,
        type FolderEntry,
        type PreparedFolder,
    } from "$lib/helpers/transcodedFolderSelection";

    import { createTranscodedFolderUploader } from '$lib/services/transcodedFolderUploader.svelte'
    const uploader = createTranscodedFolderUploader();

    // Phase 1 (select): prepared holds the parsed folder until the user clicks Upload.
    let prepared = $state<PreparedFolder | null>(null);
    let selectionError = $state<string | null>(null);
    let initiatingUpload = $state(false);

    // unused in latest version
    // let folderInput: HTMLInputElement;
    // let dragging = $state(false);

    // import { thumbnailUploadService } from '$lib/services/thumbnailUploadService.svelte';
    // const thumbnailUploader = thumbnailUploadService();

    // const videoId = $derived(!page.params.videoId);
    const videoId = $derived(page.params.videoId);
    const modalOpen = $derived(videoId === undefined);

    async function selectFromEntries(entries: FolderEntry[]) {
        selectionError = null;
        prepared = null;
 
        try {
            prepared = await prepareTranscodedFolder(entries);
        } catch (error) {
            selectionError = error instanceof Error ? error.message : "Could not read the selected folder.";
        }
    }

    function handlePick(event: Event) {
        const input = event.currentTarget as HTMLInputElement;
        const entries = entriesFromInput(input.files ?? []);
        input.value = ""; // lets the user re-pick the same folder after cancelling
        selectFromEntries(entries);
    }

    async function handleDrop(event: DragEvent) {
        event.preventDefault();
        if (!event.dataTransfer) return;
        // entriesFromDrop must be called directly here: it reads the dropped items
        // synchronously, before the first await.
        selectFromEntries(await entriesFromDrop(event.dataTransfer));
    }

    function cancelSelection() {
        prepared = null;
        selectionError = null;
    }

    // Phase 2 (upload): create the video + session (with title and probe metadata), then start.
    async function handleUploadWithNewSession() {
        // Create new upload_session and fetch the id
        if (!prepared || initiatingUpload) return;
            const folder = prepared;
            initiatingUpload = true;

        try {
            const response = await fetch(
                // 'http://127.0.0.1:8000/api/video/transcoded-upload/new-upload-record',
                '/api/video/transcoded-upload/new-upload-record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: folder.folderName, ...folder.probe }),
            });

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

            // const transcodedFiles = folderInputController.state.selectedDirFiles;
            
            // Because selectedDirFiles is always an array, use the following instead of- if (transcodedFiles) {}
            // if (transcodedFiles.length > 0) {
            //     uploader.start(transcodedFiles, {
            //         videoId: videoId,
            //         transcodedUploadSessionId: transcodedUploadSessionId,
            //         // concurrency, batchSize, maxRetries all optional, defaults are sane
            //     });
            // }

            // Not awaited on purpose: start() runs for the whole upload and reports
            // its own failures through uploader.state.
            uploader.start(
                folder.uploadEntries, {
                    videoId: videoId,
                    transcodedUploadSessionId: transcodedUploadSessionId,
                    folderName: folder.folderName,
                })
                .catch(error => console.error(error));

            prepared = null;

	    } catch (err) {
            console.error(err);
            selectionError = "Could not start the upload. Please try again.";
        } finally {
            initiatingUpload = false;
        }
    }
</script>

<FolderUploadModal
    open={modalOpen} // was !modalOpen
    {prepared}
    {selectionError}
    {initiatingUpload}
    onUploadClick={handleUploadWithNewSession}
    onCancelSelection={cancelSelection}
    {handleDrop}
    {handlePick}
/>

<div class="w-5/6 mx-auto h-100vh"> 
    <!-- Form Area -->
    <!-- {#if uploader.state.status === "completed"} -->
        <section class="flex flex-row justify-evenly">
            <FormComponent videoId={videoId} />

            <div class="h-screen w-1/3 flex flex-col justify-evenly">
                <ThumbnailCard controller={thumbnailInputController} />
                <!-- Video Viewer -->
                 <!-- <VideoViewer /> -->
                <ThumbnailCard controller={thumbnailInputController} />
            </div>
        </section>
    <!-- {:else} -->
        <!-- Upload Progress & Thumbnail -->
        <!-- <section class="w-2/3 mx-auto"> -->
            <!-- Upload Progress -->
            <!-- <VideoUploadProgressCard uploader={uploader} /> -->
        <!-- </section> -->
    <!-- {/if} -->
</div>
