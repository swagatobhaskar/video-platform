<script lang="ts">
    let {
        thumbnailPreviewUrl,
        thumbnailInput,
        uploading,
        error,
        handleThumbnailUpload
    } = $props();
</script>

<!-- <div class="w-full max-w-xl mx-auto"> -->
<div class="h-full flex flex-col">

    <!-- Preview Card -->
    <!-- <div class="group overflow-hidden transition-all duration-300"> -->

        <!-- Image -->
        <!-- <div class="relative p-4"> -->
        <div class="flex-1 min-h-0 p-4">
            <div class="h-full w-full overflow-hidden rounded-2xl bg-gray-100">
                <img
                    src={thumbnailPreviewUrl}
                    alt="thumbnail-preview"
                    class="w-full h-full object-cover"
                />
            </div>
        </div>

        <!-- Thumbnail info -->
        <!-- <div class="relative px-5 pb-5 space-y-4"> -->
        <div class="px-5 pb-5 space-y-4 flex-0">

            <div class="">
                <!-- File name -->
                <p class="font-semibold text-gray-800">
                    {thumbnailInput.state?.selectedFile?.name}
                </p>
                
                {#if thumbnailInput.state.thumbnailMetadata}
                    <div class="mt-2 flex flex-wrap gap-2 text-xs">
                        <span class="rounded-full bg-gray-100 px-3 py-1 text-gray-700">
                            {thumbnailInput.state.thumbnailMetadata.format}
                        </span>

                        <span class="rounded-full bg-gray-100 px-3 py-1 text-gray-700">
                            {(thumbnailInput.state.thumbnailMetadata.size / (1024 * 1024)).toFixed(2)} MB
                        </span>

                        <span class="rounded-full bg-gray-100 px-3 py-1 text-gray-700">
                            {thumbnailInput.state.thumbnailMetadata.width}x{thumbnailInput.state.thumbnailMetadata.height}
                        </span>
                    </div>
                {/if}
            </div>

            <!-- Error -->
            {#if error}
                <div class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                    {error}
                </div>
            {/if}

            <!-- Uploading -->
            {#if uploading}
                <div class="space-y-2">
                    <div class="h-2 overflow-hidden rounded-full bg-gray-200">
                        <div class="h-full w-1/2 animate-pulse rounded-full bg-blue-500"></div>
                    </div>

                    <p class="text-sm text-blue-600">
                        Uploading thumbnail...
                    </p>
                </div>
            {/if}

            <!-- Upload & Cancel Buttons -->
            <div class="flex gap-3">
                <button
                    class="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3
                        font-medium text-gray-700 transition hover:bg-gray-50 cursor-pointer"
                    onclick={() => {
                        // if (uploader.uploading) cancelUpload();
                        // else
                        thumbnailInput.cancelSelectedFile();
                    }}
                >
                    Cancel
                </button>
                <button
                    class="flex-1 rounded-xl bg-blue-600 px-4 py-3 font-medium text-white shadow-lg
                        shadow-blue-200 transition hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                    // onclick={uploadVideoFile}
                    onclick={handleThumbnailUpload}
                >
                    { uploading ? 'Uploading...' : 'Upload' }
                </button>
            </div>
        </div>
    <!-- </div> -->
</div>