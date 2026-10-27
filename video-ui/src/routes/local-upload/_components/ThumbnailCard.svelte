<script lang="ts">
    let { videoId }: { videoId?: string | null } = $props();

    import { fileInputController } from '$lib/controllers/fileInputController.svelte';
	import ThumbnailPreview from './ThumbnailPreview.svelte';

    const thumbnailInput = fileInputController({uploadFileType: "image"});
    
    let uploading = $state(false);
    let error = $state<string | null>(null);
    let thumbnailR2Url = $state<string | null>(null);
    let thumbnailPreviewUrl = $state<string | null>(null);
    let thumbnailFileInputEl = $state<HTMLInputElement | null>(null);

    function openThumbnailFileDialog() {
        thumbnailFileInputEl?.click();
    }

    const handleThumbnailUpload = async () => {
        const thumbnail_file = thumbnailInput.state.selectedFile;
        // const videoId = "2bdfd33c-c577-4f80-b0b7-fe3bd0772bcc";
        // console.log("Uploading thumbnail for videoId:", videoId, "file:", thumbnail_file);
        if (!videoId || !thumbnail_file) return;

        uploading = true;
        error = null;

        try {
            const formData = new FormData();
            formData.append('thumbnail_image', thumbnail_file); // must match the FastAPI param name

            const uploadRes = await fetch(`/api/thumbnail/video/${videoId}/upload`,{
                method: 'POST',
                // Don't define Content-Type header when sending FormData, the browser will set it automatically with the correct boundary.
                // headers: { 'Content-Type': 'application/json'},
                body: formData,
            })
            if (!uploadRes.ok) {
                const body = await uploadRes.json().catch(() => null);
                error = body?.detail ?? `Upload failed (${uploadRes.status})`;
                return;
            };
            const data: {thumbnail_object_key: string} = await uploadRes.json();
            thumbnailR2Url = data.thumbnail_object_key;
            thumbnailInput.cancelSelectedFile(); // clear the local selection
        } catch (err: unknown) {
            error = err instanceof Error ? err.message : 'Unknown error occurred';
            // if (err instanceof Error) {
            //     if (err.name === "AbortError") {
            //         console.log("Upload cancelled");
            //     } else {
            //         console.error("From else: ", err);
            //         error = err.message;
            //     }
            // } else {
            //     console.error(err);
            //     error = 'Unknown error occurred';
            // }
        } finally {
            uploading = false;
        }
    }

    function changeThumbnail() {
        thumbnailR2Url = null;
        thumbnailInput.cancelSelectedFile();
    }

    // Local preview URL, cleaned up when the file changes
    $effect(() => {
        const thumbnailFile = thumbnailInput.state.selectedFile;
        if (!thumbnailFile) {
            thumbnailPreviewUrl = null;
            return;
        };
        const url = URL.createObjectURL(thumbnailFile);
        thumbnailPreviewUrl = url;
        
        // clean-up when file changes
        return () => URL.revokeObjectURL(url);
    })

</script>

<div class="h-80 p-2 relative border border-gray-200"
>
    <!-- If uploaded, show thumbnail from R2 link -->
    {#if thumbnailR2Url}
        <!-- <div class="inset-5 rounded-3xl pointer-events-auto flex items-center justify-center text-center p-10"> my old code -->
        <div class="h-full flex flex-col items-center justify-center gap-3">
            <!-- <img src={thumbnailR2Url} alt="thumbnail" width="400" height="300" /> my old code -->
            <!-- Remove / change -->
            <img src={thumbnailR2Url} alt="thumbnail" class="max-h-56 object-contain" />
            <button type="button" onclick={changeThumbnail}
                class="px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 cursor-pointer">
                Change
            </button>
        </div>
    {:else if !thumbnailPreviewUrl}
        <!-- {#if !thumbnailPreviewUrl} -->
        <!-- Upload Thumbnail -- inner border -->
        <div class="absolute inset-3 border-2 border-dashed border-gray-200 rounded-2xl pointer-events-auto
            flex items-center justify-center text-center p-10"
            role="button"
            tabindex="0"
            ondragenter={thumbnailInput.handleDragEnter}
            ondragleave={thumbnailInput.handleDragLeave}
            ondragover={thumbnailInput.handleDragOver}
            ondrop={thumbnailInput.handleDrop}
            class:border-blue-500={thumbnailInput.state.isDragging}
            class:bg-blue-50={thumbnailInput.state.isDragging}
            onclick={openThumbnailFileDialog}
            
            onkeydown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openThumbnailFileDialog();
                }
            }}
        >
            <div class="flex flex-col items-center gap-3">
                <!-- Upload SVG -->
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.2" stroke="currentColor" class="size-10">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                </svg>

                <p>
                    Drop thumbnail here
                    <br />
                    or
                </p>

                <button
                    type="button"
                    // onclick={openThumbnailFileDialog}  my old code
                    onclick={(e) => { e.stopPropagation(); openThumbnailFileDialog(); }}
                    class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                >
                    Browse from device
                </button>

                <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp,image/gif"
                    class="hidden"
                    bind:this={thumbnailFileInputEl}
                    onchange={thumbnailInput.handleFileSelect}
                />
                {#if thumbnailInput.state.error}
                    <p class="text-sm text-red-600">{thumbnailInput.state.error}</p>
                {/if}
            </div>
        </div>
    {:else}
        <!-- Show thumbnail preview -->
        <ThumbnailPreview
            {thumbnailPreviewUrl}
            {thumbnailInput}
            {uploading}
            {error}
            {handleThumbnailUpload}
        />
        <!-- {/if} -->
    {/if}
</div>
