<script lang="ts">
    import { createVideoUploadSession } from "$lib/services/videoUploadSession.svelte";
    import { formatETA, formatSpeed } from '$lib/helpers/multipartUploadHelper';
	import UploadProgressSkleton from "$lib/components/ui/uploadProgressSkleton.svelte";

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


    // let progress = $state(0);
	// let uploading = $state(false);
	// let speed = $state(0);
	// let eta = $state(0);

    // const mockUploader = () => {
    //     progress = 0;
    //     uploading = true;

    //     const interval = setInterval(() => {
    //         if (progress >= 100) {
    //             clearInterval(interval);
    //             uploading = false;
    //             progress = 100;
    //             speed = 0;
	// 			eta = 0;
    //             return;
    //         }
    //         progress += 10;
    //         speed = +(Math.random() * 5 + 1).toFixed(2); // Mock speed between 1-6 MB/s
    //         eta = +(((100 - progress) / 10) * (Math.random() * 2 + 1)).toFixed(1); // Mock ETA
    //     }, 2000);
    // };

    // console.log("Selected file: ", workflow.workflowProgress.selectedVideoFile);
    // console.log("Video Session UUID: ", workflow.workflowProgress.videoSessionId);

    // Start uploading th video as soon as we land on this page
    $effect(() => {
        const timer = setTimeout(() => {
            if (workflow.workflowProgress.selectedVideoFile) {
                uploadVideoFile();
                // mockUploader();
            }
        }, 500); // slight delay to ensure UI has updated

        // Clean-up function to cancel upload if user navigates away before upload starts
        return () => clearTimeout(timer);
    });
</script>


<div class="min-h-52 relative overflow-hidden rounded-2xl border border-white/20 bg-white/70
    backdrop-blur-xl shadow-[0_10px_40px_rgba(0,0,0,0.08)] p-6"
>
    
    {#if uploader.uploading}
        
        <div class="space-y-5">

            <!-- LIVE STATUS -->
			<div class="flex items-center gap-3">
				<div class="relative">
					<div class="h-3 w-3 rounded-full bg-green-500"></div>
					<div class="absolute inset-0 animate-ping rounded-full bg-green-400"></div>
				</div>

				<p class="text-sm font-medium text-gray-600">
					Uploading...
				</p>
			</div>
            
            <!-- Header -->
            <div class="flex items-start justify-between gap-4">
                <div class="min-w-0">
                    <!-- <p class="text-sm text-gray-500 mb-1">
                        Uploading Video
                    </p> -->

                    <h3 class="truncate font-semibold text-gray-900 text-lg">
                        {workflow.workflowProgress.selectedVideoFile?.name}
                    </h3>
                </div>

                <!-- Percentage badge -->
                <div
                    class="shrink-0 rounded-full bg-blue-50 border border-blue-100
                    px-3 py-1 text-sm font-medium texxt-blue-600"
                >
                    {uploader.progress}%
                </div>
            </div>

            <!-- Progress bar -->
            <div>
                <div class="relative h-3 overflow-hidden rounded-full bg-gray-200/80">

                    <!-- Filled Portion -->
                    <div
                        class="relative h-full overflow-hidden rounded-full transition-all duration-500 ease-out"
                        style={`width:${uploader.progress}%`}
                    >
                        <!-- Gradient fill -->
                        <div class="absolute inset-0 bg-linear-to-r from-value-500 via-indigo-500 to-purple-500"
                        ></div>

                        <!-- Animated Shine -->
                        <div
                            class="absolute inset-0 animate-[shimmer_2s_linear_infinite]
                            bg-[linear-gradient(110deg,transparent,rgba(255,255,255,0.45),transparent)]
                            bg-size-[200%_100%]"
                        ></div>
                    </div>
                </div>

                <!-- Meta -->
                <div class="mt-3 flex items-center justify-between text-sm">
                    <div class="flex items-center gap-4 text-gray-500">
                        <div>
                            <span class="text-gray-400">Speed</span>
                            <span class="ml-1 font-medium text-gray-700">
                                {formatSpeed(uploader.speed)} MB/s
                            </span>
                        </div>

                        <div>
                            <span class="text-gray-400">ETA</span>
                            <span class="ml-1 font-medium text-gray-700">
                                {formatETA(uploader.eta)}s
                            </span>
                        </div>
                    </div>

                    <p class="font-medium text-gray-700">
                        {uploader.progress}% uploaded
                    </p>
                </div>
            </div>

            <!-- Actions: Pause/Resume, Cancel -->
            <div class="flex items-center gap-3 pt-2">
                <button
                    class="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-4 py-2 text-sm
                        font-medium text-white transition hover:bg-black active:scale-[0.98]"
                    onclick={() => {
                        if (uploader.uploading) handleUploadPlayPause();
                    }}
                >
                    Pause
                </button>

                <button
                    class="inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm border-red-200
                        bg-red-50 font-medium text-red-600 transition hover:bg-red-100 active:scale-[0.98]"
                    onclick={() => {
                        if (uploader.uploading) cancelUpload();
                    }}
                >
                    X Cancel
                </button>
            </div>

            <!-- Error -->
            {#if uploader.error}
                <div class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                    {uploader.error}
                </div>
            {/if}
        </div>
    {:else}
        <UploadProgressSkleton />
    {/if}
</div>


<!-- {#if videoUploaded && videoTranscoding}
    // show complete uploaded bar
    // show transcode progress bar
{/if}

{#if videoReady}
    // show video preview from R2 link
{/if} -->


<style>
    @keyframes shimmer {
        0% {
            background-position: 200% 0;
        }

        100% {
            background-position: -200% 0;
        }
    }
</style>
