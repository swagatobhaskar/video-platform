<script lang="ts">
    import { invalidate } from '$app/navigation';
    import { page } from '$app/state';
    import { goto } from "$app/navigation";
    import { resolve } from '$app/paths';

    import FolderUploadModal from '../_components/FolderUploadModal.svelte';
    import FormComponent from '../_components/FormComponent.svelte';
    import ThumbnailCard from '../_components/ThumbnailCard.svelte';
    import VideoUploadProgressCard from '../_components/VideoUploadProgressCard.svelte';
    import DashPlayer from '$lib/components/DashPlayer.svelte';

    let { data } = $props();

    import {
        entriesFromInput,
        entriesFromDrop,
        prepareTranscodedFolder,
        type FolderEntry,
        type PreparedFolder,
    } from "$lib/helpers/transcodedFolderSelection";

    import { createTranscodedFolderUploader } from '$lib/services/transcodedFolderUploader.svelte'
    const uploader = createTranscodedFolderUploader();

    // const uploadDone = $derived(uploader.state.status === "completed" || data.upload?.status === "completed")

    const showDetails = $derived(
        uploader.state.status === "completed" || (
            uploader.state.status === "idle" && data.video?.upload_status === "COMPLETED"
        )
    );

    // Phase 1 (select): prepared holds the parsed folder until the user clicks Upload.
    let prepared = $state<PreparedFolder | null>(null);
    let selectionError = $state<string | null>(null);
    let initiatingUpload = $state(false);

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

    let resumeError = $state<string | null>(null);

    // Handle reselecting same folder after browser crash or some other issue that breaks the upload
    async function handleResumePick(event: Event) {
        const input = event.currentTarget as HTMLInputElement;
        const entries = entriesFromInput(input.files ?? []);
        input.value = '';
        resumeError = null;

        const session = data.video;
        if (!data.videoId || session) return;

        try {
            const folder = await prepareTranscodedFolder(entries);

            // Cheap sanity check that this is the same folder.
            if (folder.uploadEntries.length !== session.total_files) {
                throw new Error(
                    `This folder has ${folder.uploadEntries.length} files, but the interrupted upload had ${session.total_files}. Pick the same folder.`
                );
            }

            uploader.start(folder.uploadEntries, {
                videoId: data.videoId,
                transcodedUploadSessionId: session.upload_session_id,
                folderName: folder.folderName,
            }).catch(error => console.error('Unexpected uploader error:', error));
        } catch (error) {
            resumeError = error instanceof Error ? error.message : 'Could not read the selected folder.';
        }
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
                .catch(error => console.error("Unexpected uploader error:", error));

            prepared = null;

	    } catch (err) {
            console.error(err);
            selectionError = "Could not start the upload. Please try again.";
        } finally {
            initiatingUpload = false;
        }
    }

    // After the upload finishes, the backend has set object_key, so refetch for the manifest URL.
    $effect(() => {
        if (uploader.state.status === "completed" && data.videoId) {
            invalidate(`app:video:${data.videoId}`);
        }
    });

    // // 1. Fetch the available details of a video
    // let video = $state<VideoView | undefined>(undefined);
    // let videoError = $state<string | null>(null);

    // $effect(() => {
    //     // Immediate clearing of stale video data.
    //     // Proper cancellation when navigating between video IDs.
    //     // Explicit error state for the UI.
    //     // No accidental display of the previous video's thumbnail or manifest.
    //     const id = videoId;

    //     if (!id) {
    //         video = undefined;
    //         videoError = null;
    //         console.error("Video Id Not found in the VideoPlayer!");
    //         return;
    //     }

    //     const abortController = new AbortController();

    //     // Clear previous video's data immediately.
    //     video = undefined;
    //     videoError = null;

    //     (async () => {
    //         try {
    //             const resp = await fetch(`/api/video/view/${id}`, {
    //                 signal: abortController.signal,
    //             });

    //             if (!resp.ok) {
    //                 throw new Error(`Failed to fetch object key: ${resp.status}`);
    //             }
    //             const data: VideoView = await resp.json();
    //             // video = data;
    //             if (!abortController.signal.aborted) {
    //                 video = data;
    //             }

    //         } catch (error) {
    //             if (abortController.signal.aborted) return; // expected on cleanup
    //             console.error("Failed to fetch video:", error);
    //             videoError = "Could not load video details.";
    //         }
    //     }) ();

    //     // Runs when videoId changes or this effect is destroyed.
    //     return () => abortController.abort();
    // });
</script>

<FolderUploadModal
    open={modalOpen} // was modalOpen. !modalOpen is to disable the video selection modal temporarily
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
    {#if showDetails}
        <section class="flex flex-row justify-evenly">
            <!--
            wrapper recreates the component when the ID changes, so reading the prop once is intentional.
            Svelte may warn about referencing props locally; that’s fine here -->
            {#key data.videoId}
                <FormComponent videoId={data.videoId} initialData={data.formData} />
            {/key}

            <div class="h-screen w-1/3 flex flex-col justify-evenly">
                <ThumbnailCard videoId={data.videoId} />
                <!-- Video Player -->
                <DashPlayer src={data.video?.dash_manifest_key} poster={data.video?.thumbnail_object_key} />
            </div>
        </section>
    {:else}
        <section class="w-2/3 mx-auto">
            <!-- Upload Progress -->
            <VideoUploadProgressCard
                serverUpload={data.video}
                uploader={uploader}
                resumeError={resumeError}
                onResumeSelect={handleResumePick}
            /> 
        </section>
    {/if}
</div>
