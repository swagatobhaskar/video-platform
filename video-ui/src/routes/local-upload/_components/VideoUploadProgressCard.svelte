<script lang="ts">

    import { createTranscodedFolderUploader } from '$lib/services/transcodedFolderUploader.svelte'

    let { uploader } = $props<{ uploader: ReturnType<typeof createTranscodedFolderUploader>; }>();

    import { formatETA, formatSpeed } from '$lib/helpers/multipartUploadHelper';
	// import UploadProgressSkleton from "$lib/components/ui/uploadProgressSkleton.svelte";
	import UploadCompleteBar from "$lib/components/ui/uploadCompleteBar.svelte";

    import VideoProcessingProgress from './VideoProcessingProgress.svelte';
	// import VideoPicker from './VideoPicker.svelte';

    function handlePauseUpload() {
        uploader.pause();
    }

    function handleResumeUpload() {
        uploader.resume();
    }

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

                {#if uploader.state.uploading && !uploader.state.paused}
                    <button
                        class="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-4 py-2 text-sm
                            font-medium text-white transition hover:bg-black active:scale-[0.98]"
                        onclick={handlePauseUpload}
                        disabled={uploader.state.pausing}
                    >
                        Pause
                    </button>
                {/if}

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

    {#if uploader.state.paused}
        <div class="space-y-5">

            <!-- LIVE STATUS -->
			<div class="flex items-center gap-3">
				<div class="relative">
					<div class="h-3 w-3 rounded-full bg-yellow-500"></div>
					<div class="absolute inset-0 animate-ping rounded-full bg-green-400"></div>
				</div>

				<p class="text-sm font-medium text-gray-600">
					Upload Paused
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
                        <div class="absolute inset-0 bg-linear-to-r from-value-500 via-yellow-500 to-amber-600"
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
                                0
                            </span>
                        </div>

                        <div>
                            <span class="text-gray-400">ETA</span>
                            <span class="ml-1 font-medium text-gray-700">
                                unknown
                            </span>
                        </div>
                    </div>

                    <p class="font-medium text-gray-700">
                        {uploader.state.progress}% uploaded
                    </p>
                </div>
            </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center gap-3 pt-2">
            <button
                class="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-4 py-2 text-sm
                    font-medium text-white transition hover:bg-black active:scale-[0.98]"
                onclick={handleResumeUpload}
                disabled={uploader.state.resuming}
            >
                Resume
            </button>

            <button
                class="inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm border-red-200
                    bg-red-50 font-medium text-red-600 transition hover:bg-red-100 active:scale-[0.98]"
                onclick={() => {
                    if ( uploader.state.paused ) cancelUpload();
                }}
            >
                X Cancel
            </button>
        </div>
    {/if}

    {#if uploader.state.complete}
        <div class="flex flex-col">
            <UploadCompleteBar uploader={uploader} />
            <VideoProcessingProgress />
        </div>
    {/if}

</div>

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
