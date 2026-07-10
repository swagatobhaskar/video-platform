<script lang="ts">

    import { createVideoUploadSession } from '$lib/services/videoUploadSession.svelte'

    let { uploader } = $props<{ uploader: ReturnType<typeof createVideoUploadSession>; }>();

    import { formatETA, formatSpeed } from '$lib/helpers/multipartUploadHelper';
	// import UploadProgressSkleton from "$lib/components/ui/uploadProgressSkleton.svelte";
	import UploadCompleteBar from "$lib/components/ui/uploadCompleteBar.svelte";

    import VideoProcessingProgress from './VideoProcessingProgress.svelte';
	import VideoPicker from './VideoPicker.svelte';

    function handleUploadPlayPause() {}

    let uploadCancelled = $state<boolean>(false);
    
    function cancelUpload() {
        // show alert
        const confirmed = confirm("Are you sure you want to cancel the upload?");
        
        if (!confirmed) {
            return; // User chose No, keep uploading
        }
        
        uploader.cancel();
        uploader.state.file = null;
        uploadCancelled = true;
    }

    // let progress = $state(0);
	// let uploading = $state(false);
	// let speed = $state(0);
	// let eta = $state(0);
    // let complete = $state(false);
    // 
    // const mockUploader = () => {
    //     progress = 0;
    //     uploading = true;
    // 
    //     const interval = setInterval(() => {
    //         if (progress >= 100) {
    //             clearInterval(interval);
    //             uploading = false;
    //             progress = 100;
    //             speed = 0;
	// 			eta = 0;
    //             complete = true;
    //             return;
    //         }
    //         progress += 10;
    //         speed = +(Math.random() * 5 + 1).toFixed(2); // Mock speed between 1-6 MB/s
    //         eta = +(((100 - progress) / 10) * (Math.random() * 2 + 1)).toFixed(1); // Mock ETA
    //     }, 500);
    // };

    // Start uploading the video as soon as we land on this page
    // $effect(() => {
    //     const file = videoFile; // dependency is tracked here
        
    //     console.log("File in UploadProgressComponent $effect: ", videoFile);

    //     if (!file) return;

    //     const timer = setTimeout(() => {
    //         uploader.upload(file);
    //     }, 500);

    //     return () => clearTimeout(timer);
    // });
</script>

<div class="h-80 relative overflow-hidden border border-gray-200 p-6">

    {#if uploader.state.uploading}
    <!-- {#if uploading} -->
        
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
            <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                    <h3 class="truncate font-semibold text-gray-900 text-lg">
                        {uploader.state.file?.name}
                    </h3>
                </div>

                <!-- Percentage badge -->
                <div
                    class="shrink-0 rounded-full bg-blue-50 border border-blue-100
                    px-3 py-1 text-sm font-medium texxt-blue-600"
                >
                    {uploader.state.progress}%
                </div>
            </div>

            <!-- Progress bar -->
            <div>
                <div class="relative h-3 overflow-hidden rounded-full bg-gray-200/80">

                    <!-- Filled Portion -->
                    <div
                        class="relative h-full overflow-hidden rounded-full transition-all duration-500 ease-out"
                        style={`width:${uploader.state.progress}%`}
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
                                {formatSpeed(uploader.state.speed)}
                            </span>
                        </div>

                        <div>
                            <span class="text-gray-400">ETA</span>
                            <span class="ml-1 font-medium text-gray-700">
                                {formatETA(uploader.state.eta)}
                            </span>
                        </div>
                    </div>

                    <p class="font-medium text-gray-700">
                        {uploader.state.progress}% uploaded
                    </p>
                </div>
            </div>

            <!-- Actions: Pause/Resume, Cancel -->
            <div class="flex items-center gap-3 pt-2">
                <button
                    class="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-4 py-2 text-sm
                        font-medium text-white transition hover:bg-black active:scale-[0.98]"
                    onclick={() => {
                        if (uploader.state.uploading) handleUploadPlayPause();
                    }}
                >
                    Pause
                </button>

                <button
                    class="inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm border-red-200
                        bg-red-50 font-medium text-red-600 transition hover:bg-red-100 active:scale-[0.98]"
                    onclick={() => {
                        if (uploader.state.uploading) cancelUpload();
                    }}
                >
                    X Cancel
                </button>
            </div>

            <!-- Error -->
            {#if uploader.error}
                <div class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                    {uploader.state.error}
                </div>
            {/if}
        </div>
    {/if}

    <!-- {#if !uploader.state.uploading && !uploader.state.complete}
        <UploadProgressSkleton />
    {/if} -->

    <!-- If upload cancelled show file picker -->
    {#if uploadCancelled}
        <!-- <VideoPicker uploader={uploader}/> -->

        <!-- Instead, ask whether user will upload another video, then Show the modal again, or exit-->
    {/if}

    {#if uploader.state.complete}
        <div class="flex flex-col">
            <UploadCompleteBar uploader={uploader} />
            <VideoProcessingProgress />
        </div>
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
