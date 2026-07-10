<script lang="ts">

    let { uploader } = $props();

    import { fileInputController } from "$lib/controllers/fileInputController.svelte";
    const videoInputController = fileInputController({uploadFileType: "video"})

    let videoFileInputEl = $state<HTMLInputElement | null>(null);

    function openVideoFileDialog() {
        videoFileInputEl?.click();
    }
    
    let videoPreviewUrl: string | null = $state(null);

    let initiatingUpload: boolean = $state(false);

    $effect(() => {
        const videoFile = videoInputController.state.selectedFile;
        if (!videoFile) {
            videoPreviewUrl = null;
            return;
        };
        const url = URL.createObjectURL(videoFile);
        videoPreviewUrl = url;
        
        // clean-up when file changes
        return () => URL.revokeObjectURL(url);
    })
</script>

<div
    class="absolute inset-0 rounded-3xl p-3 border-2 border-dashed border-gray-400 flex items-center justify-center text-center"
    role="button"
    tabindex="0"
    ondragenter={videoInputController.handleDragEnter}
    ondragleave={videoInputController.handleDragLeave}
    ondragover={videoInputController.handleDragOver}
    ondrop={videoInputController.handleDrop}
    class:border-blue-500={videoInputController.state.isDragging}
    class:bg-blue-50={videoInputController.state.isDragging}
    onclick={openVideoFileDialog}
    
    onkeydown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openVideoFileDialog();
        }
    }}
>
    <!-- Show input options if file isn't selcted -->
    {#if !videoInputController.state.selectedFile}
        <div class="flex flex-col items-center gap-3">

            <svg fill="#C4C4C4" viewBox="-2.1 -2.1 39.20 39.20" version="1.1" xmlns="http://www.w3.org/2000/svg" stroke="#C4C4C4" stroke-width="0.00035">
                <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
                <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round" stroke="#CCCCCC" stroke-width="0.7"></g>
                <g id="SVGRepo_iconCarrier">
                    <title>upload1</title>
                    <path d="M29.426 15.535c0 0 0.649-8.743-7.361-9.74-6.865-0.701-8.955 5.679-8.955 5.679s-2.067-1.988-4.872-0.364c-2.511 1.55-2.067 4.388-2.067
                    4.388s-5.576 1.084-5.576 6.768c0.124 5.677 6.054 5.734 6.054 5.734h9.351v-6h-3l5-5 5 5h-3v6h8.467c0 0 5.52 0.006 6.295-5.395 0.369-5.906-5.336-7.070-5.336-7.070z"></path>
                </g>
            </svg>

            <p>
                Drop video here
                <br />
                or
            </p>

            <button
                type="button"
                onclick={openVideoFileDialog}
                class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
            >
                Browse from device
            </button>

            <input
                type="file"
                accept="video/*"
                class="hidden"
                bind:this={videoFileInputEl}
                onchange={videoInputController.handleFileSelect}
            />
        </div>
    {:else}
        {#if videoPreviewUrl }
            <!-- Show video preview -->
            <div class="w-full h-full flex flex-col">

                <!-- Large video preview -->
                <div class="flex-1 min-h-0 overflow-hidden rounded-2xl bg-black">
                    <!-- svelte-ignore a11y_media_has_caption -->
                    <video
                        src={videoPreviewUrl}
                        controls
                        class="w-full h-full object-contain bg-black"
                    ></video>
                </div>

                <!-- Bottom info panel / Video metadata -->
                <div class="pt-5 flex flex-col gap-4">
                    <!-- Metadata -->
                    <div class="text-sm text-gray-700 space-y-1 w-2/4 text-left">
                        <p class="font-medium text-gray-900 break-all">
                            {videoInputController.state.selectedFile.name}
                        </p>
                        
                        {#if videoInputController.state.videoMetadata}
                            <div class="grid grid-cols-2 gap-x-6 gap-y-1 text-gray-600">
                                <p>Type: {videoInputController.state.videoMetadata.mimeType}</p>
                                <p>Size: {(videoInputController.state.videoMetadata.size / (1024 * 1024)).toFixed(2)} MB</p>
                                <p>Duration: {(videoInputController.state.videoMetadata.duration / 60).toFixed(2)} mins</p>
                                <p>Resolution: {videoInputController.state.videoMetadata.width}x{videoInputController.state.videoMetadata.height}</p>
                            </div>
                        {/if}
                    </div>

                    <!-- Actions - Upload & Cancel Buttons -->
                    <div class="flex justify-end gap-3">
                        <button
                            class="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-5 rounded-xl transition cursor-pointer"
                            onclick={() => {
                                videoInputController.cancelSelectedFile();
                            }}
                        >
                            Cancel
                        </button>

                        <button
                            class="bg-blue-600 hover:bg-blue-700 text-white py-2 px-5 rounded-xl transform shadow cursor-pointer"
                            onclick={uploader}
                        >
                            { initiatingUpload ? 'Uploading...' : 'Upload' }
                        </button>
                    </div>
                </div>
            </div>
        {/if}
    {/if}
    </div>