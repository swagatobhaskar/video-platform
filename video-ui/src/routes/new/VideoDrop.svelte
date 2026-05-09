<script lang="ts">
    
    // Video file selection handler
    let videoFileInputEl = $state<HTMLInputElement | null>(null);

    function openVideoFileDialog() {
        videoFileInputEl?.click();
    }

    import { fileInputController } from "$lib/controllers/ui/fileInputController.svelte";
    const videoInput = fileInputController({uploadFileType: "video"});
    
    let videoPreviewUrl: string | null = $state(null);
    
    $effect(() => {
        const videoFile = videoInput.state.selectedFile;
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

<!-- Calculating the height of this page: subtract 100vh from the header height -->

<div class="h-[calc(100vh-4rem)] md:h-[calc(100vh-5rem)] flex items-center justify-center">
    <!-- Video Drop -->
    <div class="w-screen md:w-3/5 h-4/5 md:h-3/5 bg-white rounded-4xl shadow-2xl relative">
        <!-- Inner border -->
        <div
            class="absolute inset-5 border-2 border-dashed border-gray-400 rounded-3xl pointer-events-auto
                flex items-center justify-center text-center p-10"
            role="button"
            tabindex="0"
            ondragenter={videoInput.handleDragEnter}
            ondragleave={videoInput.handleDragLeave}
            ondragover={videoInput.handleDragOver}
            ondrop={videoInput.handleDrop}
            class:border-blue-500={videoInput.state.isDragging}
            class:bg-blue-50={videoInput.state.isDragging}
            onclick={openVideoFileDialog}
            
            onkeydown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openVideoFileDialog();
                }
            }}
        >
            <!-- Show input options if file isn't selcted -->
            {#if !videoInput.state.selectedFile}
                <div class="flex flex-col items-center gap-3">
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
                        onchange={videoInput.handleFileSelect}
                    />
                </div>
            {:else}
                {#if videoPreviewUrl }
                    <!-- Show video preview -->
                    <div class="flex flex-col items-center gap-3">
                        <!-- Video Preview -->
                        
                        <!-- svelte-ignore a11y_media_has_caption -->
                        <video
                            src={videoPreviewUrl}
                            controls
                            class="max-h-64 rounded-lg shadow-xl pointer-events-auto"
                        ></video>
                        <!-- Video metadata -->
                        <div class="text-left text-sm text-gray-700">
                            <p class="text-gray-700">{videoInput.state.selectedFile.name}</p>
                            {#if videoInput.state.videoMetadata}
                                <p>Type: {videoInput.state.videoMetadata.mimeType}</p>
                                <p>Size: {(videoInput.state.videoMetadata.size / (1024 * 1024)).toFixed(2)} MB</p>
                                <p>Duration: {(videoInput.state.videoMetadata.duration / 60).toFixed(2)} mins</p>
                                <p>Resolution: {videoInput.state.videoMetadata.width}x{videoInput.state.videoMetadata.height}</p>
                            {/if}
                        </div>

                        <!-- Upload & Cancel Buttons -->
                        <div class="flex gap-3 pointer-events-auto">
                            <button
                                class="bg-gray-500 text-white py-2 px-4 rounded cursor-pointer"
                                onclick={() => {
                                    // if (uploader.uploading) cancelUpload();
                                    // else
                                    videoInput.cancelSelectedFile();
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                class="bg-blue-500 text-white py-2 px-4 rounded cursor-pointer"
                                // onclick={uploadVideoFile}
                            >
                                <!-- { uploader.uploading ? 'Uploading...' : 'Upload' } -->
                                Upload
                            </button>
                        </div>
                    </div>
                {/if}
            {/if}
        </div>
        {#if videoInput.state.error}
            <p class="error">{videoInput.state.error}</p>
        {/if}
    </div>
</div>
