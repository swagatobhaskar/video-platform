<script lang="ts">
    import { createVideoUploadSession } from "$lib/services/videoUploadSession.svelte";
    import { formatETA, formatSpeed } from '$lib/helpers/multipartUploadHelper';

    let { workflow } = $props();
    const uploader = createVideoUploadSession();

    async function uploadVideoFile() {
        let videoFile = workflow.workflowProgress.selectedVideoFile;
        if (!videoFile) return;

        uploader.upload(videoFile);

        // videoFile = null;
    }

    function handleUploadPlayPause() {}
    
    function cancelUpload() {
        uploader.cancel();
        workflow.workflowProgress.selectedVideoFile = null;
        // workflow.workflowProgress.videoSessionId = null;
        // if (workflow.workflowProgress.thumbnailUploaded) {
            // modal -> cancel upload / upload new video
        // }
        // workflow.goToStep("video-drop");
    }

    console.log("Selected file: ", workflow.workflowProgress.selectedVideoFile);
    console.log("Video Session UUID: ", workflow.workflowProgress.videoSessionId);

    // Start uploading th video as soon as we land on this page
    $effect(() => {
        const timer = setTimeout(() => {
            if (workflow.workflowProgress.selectedVideoFile) {
                uploadVideoFile();
            }
        }, 500); // slight delay to ensure UI has updated

        // Clean-up function to cancel upload if user navigates away before upload starts
        return () => clearTimeout(timer);
    });
</script>

<div class="flex-1 shadow-gray-200 p-8 relative border border-gray-200 bg-white/90
    backdrop-blur-sm rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.06)]"
>
    <p class="text-gray-600">{workflow.workflowProgress.selectedVideoFile?.name}</p>

    {#if uploader.uploading}
    <div class="w-full bg-gray-200 rounded-full h-2.5 mb-2">
        <div class="bg-blue-500 h-2.5 rounded-full" style="width: {uploader.progress}%" ></div>
        <p>Progress: {uploader.progress}%</p>
        <p>Speed: {formatSpeed(uploader.speed)}</p>
        <p>ETA: {formatETA(uploader.eta)}</p>
    </div>
    {/if}

    <!-- Pause/Resume Yet to implement -->
     <button
        class="bg-gray-500 text-white py-2 px-4 rounded cursor-pointer"
        onclick={() => {
            if (uploader.uploading) handleUploadPlayPause();
        }}
    >
        Pause Upload
    </button>

    <button
        class="bg-gray-500 text-white py-2 px-4 rounded cursor-pointer"
        onclick={() => {
            if (uploader.uploading) cancelUpload();
        }}
    >
        Cancel Upload
    </button>


    {#if uploader.error}
        <p class="text-red-500 mt-2">{uploader.error}</p>
    {/if}

</div>
