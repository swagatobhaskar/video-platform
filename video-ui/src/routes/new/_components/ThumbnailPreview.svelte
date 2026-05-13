<script lang="ts">
    let {
        thumbnailPreviewUrl,
        thumbnailInput,
        uploading,
        error,
        handleThumbnailUpload
    } = $props();
</script>

<div class="flex flex-col items-center gap-3">
    <!-- Thumbnail Preview -->
    <img
        src={thumbnailPreviewUrl}
        alt="thumbnail-preview"
        class="max-h-64 rounded-lg shadow-xl pointer-events-auto"
    />
    <!-- Thumbnail metadata -->
    <div class="text-left text-sm text-gray-700">
        <p class="text-gray-700">{thumbnailInput.state?.selectedFile?.name}</p>
        {#if thumbnailInput.state.thumbnailMetadata}
            <p>format: {thumbnailInput.state.thumbnailMetadata.format}</p>
            <p>Size: {(thumbnailInput.state.thumbnailMetadata.size / (1024 * 1024)).toFixed(2)} MB</p>
            <p>Resolution: {thumbnailInput.state.thumbnailMetadata.width}x{thumbnailInput.state.thumbnailMetadata.height}</p>
        {/if}
    </div>

    {#if error}
        <p class="text-red-500">{error}</p>
    {/if}

     <!-- Uploading state -->
     {#if uploading}
        <p class="text-blue-500">Uploading thumbnail...</p>
     {/if}

    <!-- Upload & Cancel Buttons -->
    <div class="flex gap-3 pointer-events-auto">
        <button
            class="bg-gray-500 text-white py-2 px-4 rounded cursor-pointer"
            onclick={() => {
                // if (uploader.uploading) cancelUpload();
                // else
                thumbnailInput.cancelSelectedFile();
            }}
        >
            Cancel
        </button>
        <button
            class="bg-blue-500 text-white py-2 px-4 rounded cursor-pointer"
            // onclick={uploadVideoFile}
            onclick={handleThumbnailUpload}
        >
            { uploading ? 'Uploading...' : 'Upload' }
        </button>
    </div>
</div>