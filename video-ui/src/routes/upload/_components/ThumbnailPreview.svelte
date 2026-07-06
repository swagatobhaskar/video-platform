<script lang="ts">
    let {
        thumbnailPreviewUrl,
        thumbnailInput,
        uploading,
        error,
        handleThumbnailUpload
    } = $props();
</script>

<div class="h-full flex flex-col">

    <!-- Preview Card -->

    <!-- Image -->
    <div class="h-60 p-1">
        <div class="h-full w-full overflow-hidden rounded-lg bg-gray-100">
            <img
                src={thumbnailPreviewUrl}
                alt="thumbnail-preview"
                class="w-full h-full object-cover"
            />
        </div>
    </div>

    <!-- File name -->
    <p class="font-light ml-4 text-[13px] text-gray-800">
        {thumbnailInput.state?.selectedFile?.name}
    </p>

    <!-- Shor Meta + Buttons -->
    <div class="flex flex-row gap-3 items-center">

        <!-- Thumbnail info -->
        <div class="px-2 pb-2 space-y-1 flex-1/2">                    
                
            {#if thumbnailInput.state.thumbnailMetadata}
                <div class="mt-1 flex flex-wrap gap-1 text-xs">
                    <span class="rounded-md bg-gray-100 px-2 py-1 text-gray-700">
                        {thumbnailInput.state.thumbnailMetadata.format}
                    </span>

                    <span class="rounded-md bg-gray-100 px-2 py-1 text-gray-700">
                        {(thumbnailInput.state.thumbnailMetadata.size / (1024 * 1024)).toFixed(2)} MB
                    </span>

                    <span class="rounded-md bg-gray-100 px-2 py-1 text-gray-700">
                        {thumbnailInput.state.thumbnailMetadata.width}x{thumbnailInput.state.thumbnailMetadata.height}
                    </span>
                </div>
            {/if}

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

        </div>

        <!-- Upload & Cancel Buttons -->
        <div class="flex-1/2 flex flex-row gap-4">
            <button
                class="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2
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
                class="flex-1 rounded-md bg-blue-600 px-3 py-2 font-medium text-white shadow-lg
                    shadow-blue-200 transition hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                // onclick={uploadVideoFile}
                onclick={handleThumbnailUpload}
            >
                { uploading ? 'Uploading...' : 'Upload' }
            </button>
        </div>
    </div>        
</div>