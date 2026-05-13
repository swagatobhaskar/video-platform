<script lang="ts">

    let uploading: boolean = $state(false);
    let error: string | null = $state(null);
    let thumbnailR2Url: string | null= $state(null);

    let { workflow } = $props();

    import {
        fileInputController
        } from '$lib/controllers/ui/fileInputController.svelte';
        
	import ThumbnailPreview from './ThumbnailPreview.svelte';

    const thumbnailInput = fileInputController({uploadFileType: "image"});

    let thumbnailFileInputEl = $state<HTMLInputElement | null>(null);

    function openThumbnailFileDialog() {
        thumbnailFileInputEl?.click();
    }

    const handleThumbnailUpload = async () => {
        uploading = true;

        try {
            const uploadRes = await fetch(
                'http://127.0.0.1:8000/api/upload/thumbnail-upload',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json'}
                }
            )
            if (!uploadRes.ok) return;
            else {
                thumbnailR2Url = uploadRes.json();
            }
        } catch (err: unknown) {
            if (err instanceof Error) {
                if (err.name === "AbortError") {
                    console.log("Upload cancelled");
                } else {
                    console.error("From else: ", err);
                    error = err.message;
                }
            } else {
                console.error(err);
                error = 'Unknown error occurred';
            }
        } finally {
            uploading = false;
            workflow.workflowProgress.thumbnailUploaded = true;
        }
    }

    let thumbnailPreviewUrl: string | null = $state(null);

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

<div class="flex-1 shadow-gray-200 p-12 relative border border-gray-200 bg-white/90
    backdrop-blur-sm rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.06)]"
>
    <!-- If uploaded, show thumbnail from R2 link -->
    {#if thumbnailR2Url}
        <div class=" inset-5 rounded-3xl pointer-events-auto
            flex items-center justify-center text-center p-10">
            <img src={thumbnailR2Url} alt="thumbnail" width="400" height="300" />
            
            <!-- Remove / change -->
        </div>
    {:else}
        {#if !thumbnailPreviewUrl}
            <!-- Upload Thumbnail -- inner border -->
            <div class="absolute inset-5 border-2 border-dashed border-gray-300 rounded-3xl pointer-events-auto
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
                        onclick={openThumbnailFileDialog}
                        class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                    >
                        Browse from device
                    </button>

                    <input
                        type="file"
                        accept="image/*"
                        class="hidden"
                        bind:this={thumbnailFileInputEl}
                        onchange={thumbnailInput.handleFileSelect}
                    />
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
        {/if}
    {/if}
</div>
